from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from pymongo import MongoClient
import os

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
mongo_client = None
mongo_db = None

def init_mongo(app):
    global mongo_client, mongo_db
    mongo_uri = app.config.get("MONGO_URI")
    if mongo_uri:
        try:
            mongo_client = MongoClient(mongo_uri)
            # Default database name, can be parsed from URI or set explicitly
            mongo_db = mongo_client.get_database("wanderer_chat")
            print("MongoDB connected successfully.")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
    else:
        print("Warning: MONGO_URI not found in config.")
