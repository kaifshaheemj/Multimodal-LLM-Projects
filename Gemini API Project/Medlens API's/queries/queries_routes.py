from config.db import db
from datetime import datetime
from bson import ObjectId
from flask import request, jsonify, Blueprint
import base64

# Blueprint definition for queries
queries = Blueprint('queries', __name__, url_prefix="/api")
queries_collection = db['queries']
conversations_collection = db['conversation']
responses_collection = db['responses']

# Route to add a new query (text and/or image) to a conversation
@queries.route('/conversations/<conversation_id>/add_query', methods=["POST"])
def add_query(conversation_id):
    try:
        conversation_id = ObjectId(conversation_id)
        conversation = conversations_collection.find_one({"_id": conversation_id})

        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404

        # Check if the request contains both query text and an image
        data = request.form if request.form else request.get_json()  # Handles form-data or JSON
        query_text = data.get('query') if data else None

        # Check if an image is provided
        image = request.files.get('image')  # Image should be uploaded as a form-data file

        # Create the query object
        query = {
            "conversation_id": conversation_id,
            "created_at": datetime.utcnow()
        }

        # Add text if provided
        if query_text:
            query["query_text"] = query_text

        # If an image is provided, store it as a base64 encoded string (for demonstration purposes)
        if image:
            image_data = base64.b64encode(image.read()).decode('utf-8')  # Store as base64 string
            query["query_image"] = image_data  # Alternatively, save the file and use the path

        # If neither query_text nor image is provided, return an error
        if not query_text and not image:
            return jsonify({"error": "Either query text or image is required"}), 400

        # Insert the new query into the collection
        query_id = queries_collection.insert_one(query).inserted_id

        # Update the conversation with the new query ID
        conversations_collection.update_one(
            {"_id": conversation_id},
            {"$push": {"queries": query_id}}
        )

        return jsonify({"query_id": str(query_id), "message": "Query added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to get all query IDs for a conversation
@queries.route('/conversations/get_query_ids/<conversation_id>', methods=['GET'])
def get_query_ids(conversation_id):
    try:
        conversation_id = ObjectId(conversation_id)
        conversation = conversations_collection.find_one({"_id": conversation_id})

        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404

        query_ids = conversation.get('queries', [])
        query_ids_list = [str(query_id) for query_id in query_ids]

        return jsonify({
            "conversation_id": str(conversation_id),
            "query_ids": query_ids_list
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to add a response to a specific query
@queries.route('/conversations/<conversation_id>/queries/<query_id>/add_response', methods=["POST"])
def add_response(conversation_id, query_id):
    try:
        conversation_id = ObjectId(conversation_id)
        query_id = ObjectId(query_id)

        # Check if the conversation and query exist
        conversation = conversations_collection.find_one({"_id": conversation_id})
        query = queries_collection.find_one({"_id": query_id, "conversation_id": conversation_id})

        if not conversation or not query:
            return jsonify({"error": "Conversation or Query not found"}), 404

        # Retrieve the response text from the request
        data = request.get_json()
        response_text = data.get('response')
        if not response_text:
            return jsonify({"error": "Response text is required"}), 400

        # Create the new response object
        response = {
            "conversation_id": conversation_id,
            "query_id": query_id,
            "response_text": response_text,
            "created_at": datetime.utcnow()
        }

        # Insert the new response into the collection
        response_id = responses_collection.insert_one(response).inserted_id

        # Update the query with the new response ID
        queries_collection.update_one(
            {"_id": query_id},
            {"$set": {"response_id": response_id}}
        )

        return jsonify({"response_id": str(response_id)}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to retrieve all queries and responses for a conversation
@queries.route('/conversations/retrieve/<conversation_id>', methods=["GET"])
def retrieve(conversation_id):
    try:
        conversation_id = ObjectId(conversation_id)
        conversation = conversations_collection.find_one({"_id": conversation_id})

        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404

        # Retrieve the list of query IDs
        query_ids = conversation.get('queries', [])

        # Fetch all queries and their associated responses from the collections
        queries = list(queries_collection.find({'_id': {'$in': query_ids}}))

        queries_list = []
        for query in queries:
            response = responses_collection.find_one({"_id": query.get("response_id")})
            query_data = {
                "query_id": str(query['_id']),
                "query_text": query.get('query_text'),
                "query_image": query.get('query_image'),
                "created_at": query['created_at'],
                "response": {
                    "response_id": str(response['_id']) if response else None,
                    "response_text": response['response_text'] if response else None,
                    "created_at": response['created_at'] if response else None
                } if response else None
            }
            queries_list.append(query_data)

        return jsonify({
            "conversation_id": str(conversation["_id"]),
            "queries": queries_list
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
