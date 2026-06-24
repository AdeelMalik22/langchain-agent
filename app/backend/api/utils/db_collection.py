from motor.motor_asyncio import AsyncIOMotorClient

mongodb_client = AsyncIOMotorClient(
        "mongodb://root:supersecure123@localhost:27017/?authMechanism=DEFAULT")
mongodb = mongodb_client.get_database("college")


