import os
import urllib.parse


def _fix_db_url(url):
    """Normalise a database URL for SQLAlchemy and cloud-provider quirks.

    Transformations applied (in order):
    1. Replaces the legacy ``postgres://`` scheme with ``postgresql://`` —
       required by SQLAlchemy 1.4+.
    2. **Supabase Session / Transaction Mode pooler** (``*.pooler.supabase.com``):
       the PostgreSQL username *must* be ``postgres.<PROJECT_REF>`` (e.g.
       ``postgres.abcdefghijkl``).  Using the bare ``postgres`` username causes
       a misleading ``FATAL: password authentication failed for user "postgres"``
       error.  A ``ValueError`` is raised early with an actionable message so
       the misconfiguration is obvious in the deploy logs.
    3. Appends ``sslmode=require`` for all Supabase connections if the query
       string does not already specify ``sslmode``.  Supabase requires SSL for
       both pooler and direct connections.
    """
    if not url:
        return url

    # 1. Legacy scheme fix.
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)

    # 2 & 3. Supabase-specific fixes.
    if 'supabase' in url:
        parsed = urllib.parse.urlparse(url)

        hostname = parsed.hostname or ''

        # Supabase pooler URLs require 'postgres.PROJECT_REF' as the username.
        # A plain 'postgres' username is rejected by the pooler with a
        # confusing "password authentication failed" error.
        if hostname == 'pooler.supabase.com' or hostname.endswith('.pooler.supabase.com'):
            username = parsed.username or ''
            if username and not username.startswith('postgres.'):
                raise ValueError(
                    "Supabase pooler DATABASE_URL is misconfigured: the username "
                    f"'{username}' is missing the project reference.\n"
                    "For Session / Transaction Mode pooler connections the username "
                    "must be 'postgres.<PROJECT_REF>' "
                    "(e.g. 'postgres.abcdefghijkl').\n"
                    "Recommended fix: use the Supabase **direct** connection URL "
                    "instead (Project Settings → Database → Connection string → "
                    "URI):\n"
                    "  postgresql://postgres:<PASSWORD>@db.<PROJECT_REF>"
                    ".supabase.co:5432/postgres\n"
                    "If you intentionally use the pooler, change the username in "
                    "DATABASE_URL to 'postgres.<PROJECT_REF>'."
                )

        # Ensure SSL for all Supabase connections.
        qs = dict(urllib.parse.parse_qsl(parsed.query))
        if 'sslmode' not in qs:
            qs['sslmode'] = 'require'
            url = urllib.parse.urlunparse(
                parsed._replace(query=urllib.parse.urlencode(qs))
            )

    return url


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = _fix_db_url(
        os.environ.get('DATABASE_URL', 'sqlite:////tmp/aura.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': ProductionConfig,
}
