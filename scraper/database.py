import os

from supabase import create_client, Client


def get_supabase_client() -> Client:
    """Create and return a Supabase client using environment variables."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        raise EnvironmentError(
            f"Unset environment variables: {'SUPABASE_URL ' if not supabase_url else ' '}{'SUPABASE_SERVICE_ROLE_KEY' if not supabase_key else ''}"
        )

    return create_client(supabase_url, supabase_key)
