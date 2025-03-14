import os
import json
import PIL.Image
from bson import ObjectId
from flask import Flask, request, jsonify, Blueprint
import google.generativeai as genai
from dotenv import load_dotenv
from pymongo import MongoClient

# Load the environment variables from .env file
load_dotenv()

app = Flask(__name__)
os.makedirs("./temp", exist_ok=True)  

# MongoDB setup
client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=50000)
db = client["MedGlance_APIs"]  # Use your actual database name here

# Define MongoDB collections
users_collection = db['users']
conversations_collection = db['conversation']
queries_collection = db['queries']
responses_collection = db['responses']

# Gemini API class for handling AI interactions
class Gemini:
    def __init__(self) -> None:
        # Configure the API key for Google Generative AI
        self.api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=self.api_key)
        if not self.api_key:
            raise ValueError("API_KEY is not set. Please set it in the .env file")
    
        self.model = genai.GenerativeModel('gemini-1.5-pro', generation_config={"response_mime_type": "application/json"})

    def app_prompt(self, user_input: str = None) -> str:
        base_prompt = """
        Your name is MedLens, an AI assistant specializing in analyzing medicines and providing detailed information about their usage, ingredients, side effects, and other relevant details based on provided images or text. Your goal is to act as a knowledgeable medical expert and accurately interpret the contents of an image or a user query.

        If an image is provided:
        - First, identify the type of medicine (tablet, capsule, syrup, etc.) and any visible imprints.
        - Determine the active ingredients, dosage, and brand name.
        - Provide a list of uses, common side effects, and safety information (e.g., who should or shouldn't use this medicine).
        - Mention alternative medicines if applicable.

        If text is provided:
        - Address the user’s query based on the context and provide a comprehensive explanation.
        - Cross-reference with common drug databases to ensure the accuracy of your response.

        For every response:
        - Structure your output clearly with labeled sections (e.g., "Description", "Usage", "Side Effects").
        - If there is ambiguity or insufficient information, ask follow-up questions to the user for clarity.

        Always keep your responses informative, concise, and user-friendly.
        """
        if user_input:
            return f"{base_prompt}\n\nUser input: {user_input}"
        else:
            return base_prompt


    def respond(self, image_path: str = None, user_text: str = None) -> dict:
        prompt = self.app_prompt(user_text)
        print("Prompt:", prompt)

        if image_path and user_text:
            img = PIL.Image.open(image_path)
            response = self.model.generate_content([prompt, img])
        elif image_path:
            img = PIL.Image.open(image_path)
            response = self.model.generate_content([prompt, img])
        elif user_text:
            response = self.model.generate_content([prompt])
        else:
            raise ValueError("No image or text provided for generating a response.")

        print("Response:", response.text)
        return json.loads(response.text)

# Blueprint for Gemini API interactions
gemini_blueprint = Blueprint('gemini', __name__, url_prefix='/app')

@gemini_blueprint.route('/analyze', methods=['POST'])
def analyze():
    gemini = Gemini()

    # Check for required parameters in the request
    user_id = request.form.get('user_id')
    conversation_id = request.form.get('conversation_id')
    if not user_id or not conversation_id:
        return jsonify({'error': 'user_id and conversation_id are required parameters.'}), 400

    # Check for image in the request
    img_file = request.files.get('image')
    img_path = None
    if img_file:
        img_path = f"./temp/{img_file.filename}"
        img_file.save(img_path)

    # Check for text in the request
    user_text = request.form.get('message')

    if not img_path and not user_text:
        return jsonify({'error': 'No image or text provided for analysis.'}), 400

    try:
        # Analyze the image/text using Gemini API
        response = gemini.respond(image_path=img_path, user_text=user_text)

        # Save the query to the database
        query_id = queries_collection.insert_one({
            "user_id": user_id,
            "conversation_id": conversation_id,
            "query_text": user_text,
            "image_path": img_path
        }).inserted_id

        # Save the response to the database
        response_id = responses_collection.insert_one({
            "query_id": query_id,
            "response_text": response
        }).inserted_id

        # Update the conversation with the new query and response IDs
        conversations_collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$push": {"queries": query_id, "responses": response_id}}
        )

        return jsonify({
            'status': 'success',
            'query_id': str(query_id),
            'response_id': str(response_id),
            'response': response
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Register the blueprint with the main Flask app
# app.register_blueprint(gemini_blueprint)

# if __name__ == '__main__':
#     app.run(debug=True)
