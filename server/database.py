from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo import AsyncMongoClient


# DATABASE_URL = "mongodb://root:example@localhost:27017/"
DATABASE_URL = "mongodb://sa:Password123@localhost:27017,localhost:27018,localhost:27019/fastapiuploads?authSource=admin"

client = AsyncIOMotorClient(DATABASE_URL)
database = client.uploads
uploads = database.get_collection("uploads")

nonasync_client = MongoClient(DATABASE_URL)
database = nonasync_client.get_database("fastapiuploads")
nonasync_uploads = database.get_collection("uploads")

async_client = AsyncMongoClient(DATABASE_URL)
async_database = async_client.get_database("fastapiuploads")
async_uploads = async_database.get_collection("uploads")


if __name__ == "__main__":
    from models import UploadSchema
    from typing import TypedDict

    class Restaurant(TypedDict):
        name: str

    print(f"DATABASE: {database}")

    # nonasync_uploads.insert_one(Restaurant(name="Mongo's Burgers 222"))

    nonasync_uploads.insert_one(
        UploadSchema(filename="testfile", size=100.0).model_dump()
    )
