from supabase import create_client, Client
from src.config import SUPABASE_URL, SUPABASE_KEY

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError(
                "Supabase credentials not configured. "
                "Set SUPABASE_URL and SUPABASE_KEY in .env file."
            )
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client
