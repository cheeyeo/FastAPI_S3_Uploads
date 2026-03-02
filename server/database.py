from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from bson import ObjectId


DATABASE_URL = "mongodb://root:example@localhost:27017/"

client = AsyncIOMotorClient(DATABASE_URL)
database = client.uploads
uploads = database.get_collection("uploads")

nonasync_client = MongoClient(DATABASE_URL)
nonasync_uploads = nonasync_client["uploads"]


if __name__ == "__main__":
    from models import UpdateUploadSchema

    id = "69a46b78fde0950f86e6104e"

    collection_name = nonasync_uploads["uploads"]

    res = collection_name.update_one(
        {"_id": ObjectId(id)},
        {"$set": UpdateUploadSchema(current=100, percentage=100.0).model_dump()},
    )
    print(res)
