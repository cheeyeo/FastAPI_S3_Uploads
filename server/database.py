from server.config import get_settings
from pymongo import MongoClient
from pymongo import AsyncMongoClient


# Cannot contain IPs but only hostname so need to check /etc/hosts for mapping of mongodb container IP to hostname else it will fail name resolution
# Connect to Root:
# mongodb://sa:Password123@mongo1:27017,mongo2:27017,mongo3:27017/?authSource=admin
DATABASE_URL = f"mongodb://{get_settings().mongo_db_user}:{get_settings().mongo_db_password}@mongo1:27017,mongo2:27017,mongo3:27017/fastapiuploads"

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

    nonasync_uploads.insert_one(Restaurant(name="Mongo's Burgers 222"))

    nonasync_uploads.insert_one(
        UploadSchema(filename="testfile", size=100.0).model_dump()
    )
