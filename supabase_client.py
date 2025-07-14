from supabase import create_client, Client
import dontleak as dl

SUPABASE_URL = dl.SUPABASE_URL
SUPABASE_KEY = dl.SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_balance(username: str) -> int:
    result = supabase.table('users').select('*').eq('twitch', username).execute()
    if result.data:
        return result.data[0]['points']
    else:
        supabase.table('users').insert({'twitch': username, 'points': 0}).execute()
        return 0

def add_points(username: str, amount: int):
    current = get_balance(username)
    new_total = current + amount
    supabase.table('users').update({'points': new_total}).eq('twitch', username).execute()

def deduct_points(username: str, amount: int) -> bool:
    current = get_balance(username)
    if current < amount:
        return False
    new_total = current - amount
    supabase.table('users').update({'points': new_total}).eq('twitch', username).execute()
    return True