from flask import jsonify, Blueprint, request
from datetime import datetime
from config.db import db
from bson import ObjectId

# Define blueprint for conversation routes
conversation_blueprint = Blueprint('conversation', __name__, url_prefix='/app')
conversations_collection = db['conversation']
users_collection = db['users']

# Route to create a new conversation for a user
@conversation_blueprint.route('/api/create_conversation/<user_id>', methods=['POST'])
def create_conversation(user_id):
    try:
        # Validate user_id
        if not ObjectId.is_valid(user_id):
            return jsonify({"status": "error", "message": "Invalid user ID"}), 400

        # Create a new conversation document
        new_conversation = {
            "user_id": ObjectId(user_id),
            "queries": [],
            "responses": [],
            "created_at": datetime.utcnow()
        }

        # Insert the new conversation document and get the inserted ID
        conversation_id = conversations_collection.insert_one(new_conversation).inserted_id

        # Update the user's document by adding the new conversation ID
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"conversations": conversation_id}}
        )

        return jsonify({"status": "success", "conversation_id": str(conversation_id)}), 201

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Route to get a specific conversation using its ID
@conversation_blueprint.route('/api/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    try:
        # Validate conversation_id
        if not ObjectId.is_valid(conversation_id):
            return jsonify({"status": "error", "message": "Invalid conversation ID"}), 400

        # Find the conversation document using the conversation ID
        conversation = conversations_collection.find_one({"_id": ObjectId(conversation_id)})

        if not conversation:
            return jsonify({"status": "error", "message": "Conversation not found"}), 404

        return jsonify({
            "status": "success",
            "conversation_id": str(conversation["_id"]),
            "user_id": str(conversation["user_id"]),
            "queries": [str(query_id) for query_id in conversation['queries']],
            "responses": [str(response_id) for response_id in conversation['responses']],
            "created_at": conversation["created_at"]
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Route to get all conversation IDs for a given user
@conversation_blueprint.route('/api/conversation_ids/<user_id>', methods=['GET'])
def get_conversation_ids(user_id):
    try:
        # Validate user_id
        if not ObjectId.is_valid(user_id):
            return jsonify({"status": "error", "message": "Invalid user ID"}), 400

        # Find the user document using the user ID
        user = users_collection.find_one({"_id": ObjectId(user_id)})

        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        # Get the list of conversation IDs associated with the user
        conversation_ids = user.get('conversations', [])
        conversation_id_str = [str(conv_id) for conv_id in conversation_ids]

        return jsonify({
            "status": "success",
            "user_id": user_id,
            "conversation_ids": conversation_id_str
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
