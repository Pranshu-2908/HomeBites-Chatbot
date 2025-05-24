from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGO_URI)
print(client.list_database_names())
db = client["HomeBites"] 
print(db.list_collection_names())
