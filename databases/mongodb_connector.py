import os
from pymongo import MongoClient
from bson.objectid import ObjectId


USER = os.environ.get("MONGO_DB_USER")
PASSWORD = os.environ.get("MONGO_DB_PASSWORD")
DATABASE = os.environ.get("MONGO_DB_DATABASE")

def get_database():
    db_url = f"mongodb+srv://{USER}:{PASSWORD}@{DATABASE}.rd5qm6z.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(db_url)
    return client[DATABASE]


def create_object_id(_id):
    return ObjectId(_id)


if __name__ == "__main__":
    database = get_database()
    print("Connection Successful")
