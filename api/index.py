import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from main import app  # Vercel serves the ASGI `app`
