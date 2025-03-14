from config.db import db
from datetime import datetime
from bson.errors import InvalidId
from bson.objectid import ObjectId

users_collection = db['users']

def create_user(name, email, hashed_password, phone_number):
    user = {
        'name': name.lower(),
        'email': email,
        'password': hashed_password,
        'phone_number': phone_number,
        'created_at': datetime.utcnow()
    }
    result = users_collection.insert_one(user)
    return str(result.inserted_id)  

def get_all_users():
    users = []
    for user in users_collection.find({}):
        user['name'] = user['name'].lower()  # Optional: Convert name to lowercase
        user['_id'] = str(user['_id'])  # Convert ObjectId to string
        users.append(user)
    print(users)
    return users

def get_user_by_id(user_id):
    if not ObjectId.is_valid(user_id):
        raise InvalidId("Invalid User_id")
    return users_collection.find_one({'_id': ObjectId(user_id)})

def update_user(user_id, update_data):
    if not ObjectId.is_valid(user_id):
        raise InvalidId("Invalid User_id")
    users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': update_data})
    
def get_user_by_email_or_phone(email=None, phone_number=None):
    if email and phone_number:
        return users_collection.find_one({'$or': [{'email': email}, {'phone_number': phone_number}]})
    elif email:
        return users_collection.find_one({'email': email})
    elif phone_number:
        return users_collection.find_one({'phone_number': phone_number})
    return None

def delete_user(user_id):
    if not ObjectId.is_valid(user_id):
        raise InvalidId("Invalid User_id")
    users_collection.delete_one({'_id': ObjectId(user_id)})
