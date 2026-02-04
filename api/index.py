import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import app

# Vercel needs the app variable
app = app
