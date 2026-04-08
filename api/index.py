import sys
import os

# Ensure Vercel can resolve the 'app' module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
