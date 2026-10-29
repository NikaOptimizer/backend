from pathlib import Path
import tempfile
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from nika.backend.database import database_config


class DatabaseConfigTest(SimpleTestCase):
    def test_postgresql_is_default_and_distinct_from_questdb(self):
        config=database_config('/unused',{'NIKA_POSTGRES_PASSWORD':'secret','NIKA_QUESTDB_PG_PORT':'8812'})
        self.assertEqual(config['ENGINE'],'django.db.backends.postgresql')
        self.assertEqual(config['PORT'],'13070')
        self.assertEqual(config['NAME'],'nika')
        self.assertEqual(config['TEST']['NAME'],'test_nika')

    def test_no_silent_sqlite_fallback(self):
        with self.assertRaises(ImproperlyConfigured):database_config('/unused',{})
        config=database_config('/unused',{'NIKA_BACKEND_DB_ENGINE':'sqlite','NIKA_SQLITE_PATH':'/tmp/legacy.sqlite'})
        self.assertEqual(config['ENGINE'],'django.db.backends.sqlite3')
        self.assertEqual(config['NAME'],'/tmp/legacy.sqlite')

    def test_password_file_and_configuration_errors_do_not_leak_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'password';path.write_text('file-secret\n')
            config=database_config(directory,{'NIKA_POSTGRES_PASSWORD_FILE':str(path),'NIKA_POSTGRES_PASSWORD':'ignored'})
            self.assertEqual(config['PASSWORD'],'file-secret')
        with self.assertRaises(ImproperlyConfigured) as error:
            database_config('/unused',{'NIKA_POSTGRES_PASSWORD_FILE':'/private/secret'})
        self.assertNotIn('/private',str(error.exception))
        for values in [{'NIKA_POSTGRES_PORT':'bad'},{'NIKA_POSTGRES_PORT':'0'},{'NIKA_POSTGRES_HOST':'example.org'}]:
            with self.assertRaises(ImproperlyConfigured):database_config('/unused',{'NIKA_POSTGRES_PASSWORD':'secret',**values})
        config=database_config('/unused',{'NIKA_POSTGRES_PASSWORD':'secret','NIKA_POSTGRES_HOST':'example.org','NIKA_POSTGRES_SSLMODE':'verify-full'})
        self.assertEqual(config['OPTIONS']['sslmode'],'verify-full')
