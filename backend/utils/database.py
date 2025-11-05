from pymongo import MongoClient
from dotenv import load_dotenv
from backend.utils.security import hash_password
from bson import ObjectId
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI","mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client['qna']
users_collection = db['users']

def add_user_to_db(first_name, last_name, email, password):
    result = users_collection.insert_one({
        "first_name": first_name, 
        "last_name": last_name, 
        "email": email, 
        "password": hash_password(password)
    })
    return users_collection.find_one({'_id':result.inserted_id})

def get_user_by_email(email, password):
    """Retrieves user doc by email and password"""
    
    user = users_collection.find_one(
        {"email":email, "password":hash_password(password)}
    )
    return user