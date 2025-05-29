from pymongo import MongoClient
import os
from dotenv import load_dotenv
from pathlib import Path
import sys

# Load .env from the project root directory
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

MONGO_URI = os.getenv("MONGO_URI")

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

db = client["HomeBites"]
