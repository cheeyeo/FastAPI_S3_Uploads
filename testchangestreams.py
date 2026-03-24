# from server.database import nonasync_client, async_client
from server.config import get_settings
from pymongo import MongoClient


DATABASE_URL = f"mongodb://{get_settings().mongo_db_root_username}:{get_settings().mongo_db_root_password}@mongo1:27017,mongo2:27017,mongo3:27017/"

client = MongoClient(DATABASE_URL)
db = client.get_database("teststreams")
users = db.create_collection("users", changeStreamPreAndPostImages={"enabled": True})

pipeline = [
    {"$match": {"operationType": {"$in": ["insert", "update", "replace", "delete"]}}}
]

with users.watch(
    pipeline, full_document="updateLookup", full_document_before_change="required"
) as stream:
    for change in stream:
        print(change)
