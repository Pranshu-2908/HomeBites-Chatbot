from pymongo import MongoClient
import os
from dotenv import load_dotenv
from pathlib import Path
import sys

# Load .env from the project root directory
env_path = Path(__file__).resolve().parent.parent / ".env"
print(f"Loading environment variables from: {env_path}")  # Debug print
load_dotenv(dotenv_path=env_path)

MONGO_URI = os.getenv("MONGO_URI")

print(f"Loaded MONGO_URI: {MONGO_URI!r}")  # Debug print

if not MONGO_URI:
    print("MONGO_URI not found in environment variables.")
    sys.exit(1)

try:
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')
    print("MongoDB connection successful.")
except Exception as e:
    print("MongoDB connection error:", e)
    sys.exit(1)

db = client["HomeBite"]
