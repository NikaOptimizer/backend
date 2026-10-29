from contextlib import closing
import hashlib
import io
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import uuid
from unittest.mock import patch

from django.contrib.auth.models import Group,User
from django.core.management import call_command,CommandError
from django.db import connection
from django.test import TransactionTestCase
from nika.backend.api.models import Drawing


class SQLiteImportTest(TransactionTestCase):
    def test_verified_import_preserves_rows_and_refuses_overwrite(self):
        if connection.vendor != 'postgresql':
            self.skipTest('Migration integration requires PostgreSQL.')
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'legacy.sqlite3'
            backup=Path(directory)/'backups'
            manage=Path(__file__).resolve().parents[1]/'manage.py'
            env={**os.environ,'NIKA_BACKEND_DB_ENGINE':'sqlite','NIKA_SQLITE_PATH':str(source)}
            def legacy(*args):
                subprocess.run([sys.executable,str(manage),*args],env=env,check=True,capture_output=True,text=True)
            legacy('migrate','--noinput')
            drawing_id=uuid.uuid4()
            code=f'''from nika.backend.api.models import Drawing
from django.contrib.auth.models import User,Group,Permission
user=User.objects.create(username='legacy-user',password='!')
group=Group.objects.create(name='legacy-group')
group.permissions.add(Permission.objects.get(codename='view_drawing'))
user.groups.add(group)
Drawing.objects.create(id='{drawing_id}',strategy_key='legacy',provider='databento',instrument_id='id',tool='marker',revision=7,data={{'time':1700000000,'label':'preserved','color':'#ff0000'}})
'''
            legacy('shell','-c',code)
            # The command creates a read-only legacy alias dynamically. Permit
            # only that alias for its real database operations during this test.
            def import_legacy(**options):
                with patch.object(type(self),'databases',self.databases | {'legacy_import'}):
                    call_command('import_sqlite',source=str(source),backup_dir=str(backup),stdout=io.StringIO(),**options)
            original=hashlib.sha256(source.read_bytes()).hexdigest()
            import_legacy()
            self.assertFalse(Drawing.objects.exists())
            import_legacy(apply=True)
            drawing=Drawing.objects.get(pk=drawing_id)
            self.assertEqual(drawing.revision,7)
            self.assertEqual(drawing.data['label'],'preserved')
            self.assertEqual(User.objects.get(username='legacy-user').groups.get().name,'legacy-group')
            self.assertEqual(Group.objects.get(name='legacy-group').permissions.get().codename,'view_drawing')
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original)
            with self.assertRaises(CommandError):
                import_legacy(apply=True)
            self.assertEqual(Drawing.objects.count(),1)
            self.assertTrue(list(backup.glob('*manifest.json')))
