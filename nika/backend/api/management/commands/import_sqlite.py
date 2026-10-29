"""Back up and import legacy Django SQLite rows into an empty PostgreSQL schema."""
from contextlib import closing
import hashlib
import io
import json
from pathlib import Path
import sqlite3
from datetime import datetime,timezone
import os

from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand, CommandError, call_command
from django.db import connections, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.utils import ConnectionHandler


EXCLUDED = {'contenttypes.contenttype', 'auth.permission'}


def digest(payload):
    rows=json.loads(payload)
    rows.sort(key=lambda row:(row['model'],str(row['pk'])))
    return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('--source',required=True)
        parser.add_argument('--backup-dir',required=True)
        parser.add_argument('--apply',action='store_true',help='Import after the backup and validation; default is export-only.')

    def handle(self,*args,**options):
        if connections['default'].vendor != 'postgresql':
            raise CommandError('The target must be PostgreSQL.')
        source=Path(options['source']).resolve()
        if not source.is_file():
            raise CommandError('SQLite source does not exist; nothing was created or imported.')
        directory=Path(options['backup_dir']).resolve()
        directory.mkdir(parents=True,exist_ok=True,mode=0o700)
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        backup=directory/f'legacy-{stamp}.sqlite3'
        fixture=directory/f'legacy-{stamp}.json'
        # Create private backup files before any content is written.
        fd=os.open(backup,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as src, closing(sqlite3.connect(backup)) as dst:
            src.backup(dst)
        alias='legacy_import'
        config=ConnectionHandler({'default':{'ENGINE':'django.db.backends.sqlite3','NAME':backup.as_uri()+'?mode=ro','OPTIONS':{'uri':True}}}).databases['default']
        connections.databases[alias]=config
        try:
            legacy=connections[alias]
            tables=set(legacy.introspection.table_names())
            models=sorted((model for model in apps.get_models() if model._meta.managed and not model._meta.proxy
                           and model._meta.db_table in tables and model._meta.label_lower not in EXCLUDED), key=lambda model:model._meta.label_lower)
            labels=[model._meta.label_lower for model in models]
            source_counts={model._meta.label_lower:model._base_manager.using(alias).count() for model in models}
            stream=io.StringIO()
            if labels:
                call_command('dumpdata',*labels,database=alias,use_natural_foreign_keys=True,stdout=stream,verbosity=0)
                payload=stream.getvalue()
            else:
                payload='[]'
            fd=os.open(fixture,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(fd,'w') as handle:
                handle.write(payload)
            manifest={'counts':source_counts,'rows':sum(source_counts.values()),'sha256':digest(payload),'applied':False}
            if options['apply']:
                executor=MigrationExecutor(connections['default'])
                if executor.migration_plan(executor.loader.graph.leaf_nodes()):
                    raise CommandError('Apply PostgreSQL migrations before importing. The SQLite backup was retained.')
                if any(model._base_manager.using('default').exists() for model in models):
                    raise CommandError('Target tables must be empty; import aborted without overwriting data. Backups retained.')
                with transaction.atomic():
                    if labels:
                        call_command('loaddata',str(fixture),database='default',verbosity=0)
                        target=io.StringIO()
                        call_command('dumpdata',*labels,database='default',use_natural_foreign_keys=True,stdout=target,verbosity=0)
                        if digest(target.getvalue()) != manifest['sha256']:
                            raise CommandError('Verification mismatch; the PostgreSQL import was rolled back.')
                    manifest['applied']=True
            result=directory/f'legacy-{stamp}-manifest.json'
            result.write_text(json.dumps(manifest,indent=2)+'\n');result.chmod(0o600)
            self.stdout.write(f"Backed up {manifest['rows']} rows. {'Imported and verified.' if manifest['applied'] else 'Export only; use --apply to import.'}")
            self.stdout.write(f'Backup directory: {directory}')
        finally:
            if alias in connections:
                connections[alias].close()
                del connections[alias]
            connections.databases.pop(alias,None)
