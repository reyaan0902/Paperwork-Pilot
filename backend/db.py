import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    # Fallback to your project URL if not in .env
    supabase_url = "https://klnmfwnpmgzwnlfipwyl.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtsbm1md25wbWd6d25sZmlwd3lsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTExMDk2NzYsImV4cCI6MjEwNjY4NTY3Nn0.FJzQv7v4uVyZpXuhVs_W9auKyrqAN3zlV8BeuiHnjXc"

supabase: Client = create_client(supabase_url, supabase_key)