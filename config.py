import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SEERR_URL = os.getenv("SEERR_URL")
SEERR_API_KEY = os.getenv("SEERR_API_KEY")
SEERR_EMAIL = os.getenv("SEERR_EMAIL")
SEERR_PASSWORD = os.getenv("SEERR_PASSWORD")

if not SEERR_URL:
    raise ValueError("SEERR_URL must be set in the .env file")

if not SEERR_API_KEY:
    raise ValueError("SEERR_API_KEY must be set in the .env file")

if not SEERR_EMAIL:
    raise ValueError("SEERR_EMAIL must be set in the .env file")
    
if not SEERR_PASSWORD:
    raise ValueError("SEERR_PASSWORD must be set in the .env file")
