import os
import re
from flask import Flask, request, jsonify, Blueprint
from flask_bcrypt  import Bcrypt 
from bson.errors import InvalidId
from bson.objectid import ObjectId
from datetime import datetime
from users.users_db import create_user, get_all_users, get_user_by_email_or_phone, get_user_by_id, update_user, delete_user

users_db = Blueprint('app', __name__)
bcrypt = Bcrypt()

def validate_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email)

def validate_password(password):
    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*?#      &]{8,}$'
    return bool(re.match(password_regex, password))

def validate_phone_number(phone_number):
    phone_number_pattern = r'^[0-9]{10,15}$'  # Adjust the regex based on the phone number format you want to support
    return re.match(phone_number_pattern, str(phone_number))

@users_db.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name = str(data.get('user_name'))
    email = str(data.get('email'))
    password = str(data.get('password'))
    phone_number = str(data.get('phone_number'))

    required = []
    if not name:
        required.append('Name')
    if  not email:
        required.append('Email')
    if not password:
        required.append('Password')
    if not phone_number:
        required.append('Phone number')

    if not name or not email or not password or not phone_number:
        requirement = ', '.join(required) + ' required.'
        return jsonify({'msg':requirement})
    
    if not re.match(r'^[a-zA-Z\s]+$', name):
        return jsonify({'msg': 'Invalid name format'}), 400

    if not validate_email(email):
        return jsonify({'msg': 'Invalid email format'}), 400

    if not validate_password(password):
        return jsonify({'msg': 'Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one number, and one special character'}), 400

    if not validate_phone_number(phone_number):
        return jsonify({'msg': 'Invalid phone number format'}), 400

    email_exists = get_user_by_email_or_phone(email=email)
    phone_exists = get_user_by_email_or_phone(phone_number=phone_number)

    if email_exists and phone_exists:
        return jsonify({'msg': 'User with similar email and phone number already exists'}), 409
    elif email_exists:
        return jsonify({'msg': 'Email already exists'}), 409
    elif phone_exists:
        return jsonify({'msg': 'Phone number already exists'}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user_id = create_user(name, email, hashed_password, phone_number)
    return jsonify({'user_id': user_id}), 201

@users_db.route('/api/users/<user_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_user(user_id):
    if request.method == 'GET':
        try:
            user = get_user_by_id(user_id)
            if user:
                user['name'] = user['name'].lower()
                user['_id'] = str(user['_id'])
                return jsonify(user), 200
            else:
                return jsonify({'msg': 'User not found'}), 404
        except InvalidId:
            return jsonify({'msg': 'Invalid user ID'}), 400
        except Exception as e:
            return jsonify({'msg': 'An error occurred', 'error': str(e)}), 500

    elif request.method == 'PUT':
        try:
            user = get_user_by_id(user_id)
            if user:
                data = request.get_json()
                update_message = []

                if 'email' in data:
                    if not validate_email(data['email']):
                        return jsonify({'msg': 'Invalid email format'}), 400    
                    update_message.append('Email ')

                if 'password' in data:
                    if not validate_password(data['password']):
                        return jsonify({'msg': 'Password does not meet criteria'}), 400
                    data['password'] = bcrypt.generate_password_hash(data['password']).decode('utf-8')
                    update_message.append('Password ')

                if 'phone_number' in data:
                    if not validate_phone_number(data['phone_number']):
                        return jsonify({'msg': 'Invalid phone number format'}), 400
                    #if phone number already exists on the other user.
                    existing_user = get_user_by_email_or_phone(phone_number=data['phone_number'])
                    if existing_user and str(existing_user['_id']) != user_id:
                        return jsonify({'msg':'Phone number already exists'}), 409
                    update_message.append('Phone number ')

                if 'name' in data:
                    update_message.append('Name ')

                if update_message:
                    update_user(user_id, data)
                    update_msg = ' and '.join(update_message) + ' updated successfully'
                    return jsonify({'msg': update_msg}), 200
                else:
                    return jsonify({'msg': 'No valid fields to update'}), 400
            else:
                return jsonify({'msg': 'User not found'}), 404
        except InvalidId:
            return jsonify({'msg': 'Invalid user ID'}), 400
        except Exception as e:
            return jsonify({'msg': 'An error occurred', 'error': str(e)}), 500

    elif request.method == 'DELETE':
        try:
            user = get_user_by_id(user_id)
            if user:
                delete_user(user_id)
                return jsonify({'msg': 'User deleted successfully'}), 200
            else:
                return jsonify({'msg': 'User not found'}), 404
        except InvalidId:
            return jsonify({'msg': 'Invalid user ID'}), 400
        except Exception as e:
            return jsonify({'msg': 'An error occurred', 'error': str(e)}), 500
    
@users_db.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    #common varibale can be either email or password.
    identifier = data.get('identifier')  
    password = data.get('password')

    if not identifier or not password:
        return jsonify({'msg': 'Identifier and password are required'}), 400
    
    email = None
    phone_number = None

    if '@' in identifier:
        email = identifier
    else:
        phone_number = identifier     

    user = get_user_by_email_or_phone(email=email, phone_number=phone_number)
    if not user :
        return jsonify({'msg': 'Invalid Identifier'}), 401
    if  not bcrypt.check_password_hash(user['password'], password):
        return jsonify({'msg': 'Invalid password'}), 401

    user_id = str(user['_id'])
    login_time = datetime.utcnow()

    update_user_login_time(user_id, login_time)
    
    return jsonify({
        'user_id': user_id,
        'login_time': login_time
    }), 200

def update_user_login_time(user_id, login_time):
    update_data = {'last_login': login_time}
    update_user(user_id, update_data)

@users_db.route('/api/users', methods=['GET'])
def list_users():
    try:
        users = get_all_users()
        print("lsit_users:",users)
        return jsonify({'users': users}), 200
    except Exception as e:
        return jsonify({'msg': 'An error occurred', 'error': str(e)}), 500
    
