from pymongo import MongoClient


mongodb_client = MongoClient(
    "mongodb://root:supersecure123@localhost:27017/?authMechanism=DEFAULT"
)

mongodb = mongodb_client.get_database("college")