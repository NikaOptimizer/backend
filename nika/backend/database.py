"""Explicit relational database configuration, separate from QuestDB settings."""
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured


def database_config(base_dir, env=None):
    env = os.environ if env is None else env
    engine = env.get('NIKA_BACKEND_DB_ENGINE', 'postgresql')
    if engine == 'sqlite':
        return {'ENGINE': 'django.db.backends.sqlite3', 'NAME': env.get('NIKA_SQLITE_PATH', str(Path(base_dir)/'db.sqlite3'))}
    if engine != 'postgresql':
        raise ImproperlyConfigured('NIKA_BACKEND_DB_ENGINE must be postgresql or explicitly sqlite for legacy export.')
    try:
        port = int(env.get('NIKA_POSTGRES_PORT', '13070'))
        if not 1 <= port <= 65535:
            raise ValueError()
    except ValueError:
        raise ImproperlyConfigured('NIKA_POSTGRES_PORT must be a valid TCP port.') from None
    host = env.get('NIKA_POSTGRES_HOST', '127.0.0.1')
    sslmode = env.get('NIKA_POSTGRES_SSLMODE', 'disable')
    if sslmode not in ('disable', 'verify-full') or host not in ('127.0.0.1', '::1', 'localhost') and sslmode != 'verify-full':
        raise ImproperlyConfigured('Use verify-full TLS for non-loopback PostgreSQL hosts.')
    password = env.get('NIKA_POSTGRES_PASSWORD', '')
    if password_file := env.get('NIKA_POSTGRES_PASSWORD_FILE'):
        try:
            password = Path(password_file).read_text().rstrip('\r\n')
        except OSError:
            raise ImproperlyConfigured('PostgreSQL password file cannot be read.') from None
    if not password:
        raise ImproperlyConfigured('Configure NIKA_POSTGRES_PASSWORD_FILE or NIKA_POSTGRES_PASSWORD; PostgreSQL has no SQLite fallback.')
    options = {'connect_timeout': 5, 'sslmode': sslmode}
    if certificate := env.get('NIKA_POSTGRES_SSLROOTCERT'):
        options['sslrootcert'] = certificate
    return {'ENGINE': 'django.db.backends.postgresql',
            'NAME': env.get('NIKA_POSTGRES_DB', 'nika'),
            'USER': env.get('NIKA_POSTGRES_USER', 'nika'),
            'PASSWORD': password, 'HOST': host, 'PORT': str(port),
            'CONN_MAX_AGE': 0, 'OPTIONS': options,
            'TEST': {'NAME': env.get('NIKA_POSTGRES_TEST_DB', 'test_nika')}}
