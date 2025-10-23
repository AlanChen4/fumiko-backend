from supabase import Client

from scraper.schemas import Site


def get_sites(client: Client) -> list[Site]:
    """Get all enabled sites from the database."""
    response = client.table("sites").select("*").eq("is_enabled", True).execute()
    return [Site(**site) for site in response.data]
