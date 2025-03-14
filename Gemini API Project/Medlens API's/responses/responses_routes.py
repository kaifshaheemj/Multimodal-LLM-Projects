from flask import jsonify, Blueprint, request
from datetime import datetime
from config.db import db
from bson import ObjectId

# Define the blueprint for response routes
responses = Blueprint('responses', __name__, url_prefix='/app')
responses_collection = db['responses']
queries_collection = db['queries']
conversations_collection = db['conversation']

# Route to add a response to a query within a conversation
@responses.route('/conversations/<conversation_id>/add_response', methods=['POST'])
def add_response(conversation_id):
    try:
        conversation_id = ObjectId(conversation_id)
        conversation = conversations_collection.find_one({"_id": conversation_id})

        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404

        # Retrieve response data from request
        data = request.get_json()
        response_text = data.get('response')
        query_id = data.get('query_id')

        if not response_text or not query_id:
            return jsonify({"error": "Both response text and query ID are required"}), 400

        # Ensure query_id is a valid ObjectId
        try:
            query_id = ObjectId(query_id)
        except Exception:
            return jsonify({"error": "Invalid query ID"}), 400

        # Check if the query exists
        query = queries_collection.find_one({"_id": query_id, "conversation_id": conversation_id})
        if not query:
            return jsonify({"error": "Query not found"}), 404

        # Create a new response document
        response = {
            "conversation_id": conversation_id,
            "query_id": query_id,
            "response_text": response_text,
            "created_at": datetime.utcnow()
        }

        # Insert the response document and get its ID
        response_id = responses_collection.insert_one(response).inserted_id

        # Update the query document by setting the new response ID
        queries_collection.update_one(
            {"_id": query_id},
            {"$set": {"response_id": response_id}}
        )

        # Update the conversation document by pushing the new response ID
        conversations_collection.update_one(
            {"_id": conversation_id},
            {"$push": {"responses": response_id}}
        )

        return jsonify({"response_id": str(response_id), "message": "Response added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to get all responses for a specific conversation
@responses.route('/conversations/<conversation_id>/responses', methods=['GET'])
def get_responses(conversation_id):
    try:
        conversation_id = ObjectId(conversation_id)
        conversation = conversations_collection.find_one({"_id": conversation_id})

        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404

        response_ids = conversation.get('responses', [])

        # Retrieve all response documents associated with the conversation
        responses_cursor = responses_collection.find({"_id": {"$in": response_ids}})

        response_list = []
        for response in responses_cursor:
            response_list.append({
                "response_id": str(response['_id']),
                "query_id": str(response['query_id']),
                "response_text": response['response_text'],
                "created_at": response['created_at']
            })

        return jsonify({
            "conversation_id": str(conversation_id),
            "responses": response_list
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to get a specific response using its ID
@responses.route('/responses/<response_id>', methods=['GET'])
def get_response(response_id):
    try:
        response = responses_collection.find_one({"_id": ObjectId(response_id)})

        if not response:
            return jsonify({"error": "Response not found"}), 404

        return jsonify({
            "response_id": str(response["_id"]),
            "query_id": str(response["query_id"]),
            "response_text": response["response_text"],
            "created_at": response["created_at"]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
