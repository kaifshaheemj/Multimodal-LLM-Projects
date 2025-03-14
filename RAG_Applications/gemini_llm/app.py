from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from docs_preprocessing import check_document_type, text_chunking
from openai_clip import embedding_the_chunks, tokenizer, model
from qdrant import retrieve_from_qdrant, store_chunk_embedding_in_db, create_user_collection
from gemini_llm import LLM
import torch

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"  # Directory to save uploaded files
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/mria/upload", methods=["POST"])
def upload_document():
    try:
        # Check if the request contains a file
        if "file" not in request.files:
            return jsonify({"error": "File not included in the request"}), 400

        # Check for user_id and user_collection
        user_id = request.get_json("user_id")
        user_collection = request.get_json("user_collection")
        if not user_id or not user_collection:
            return jsonify({"error": "user_id and user_collection are required"}), 400

        # Retrieve the file
        file = request.files["file"]

        # Save the file securely
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        return jsonify({
            "message": "File uploaded and processed successfully",
            "file_path": file_path,
            "user_id": user_id,
            "user_collection": user_collection
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/mria/query", methods=["POST"])
def query_model():
    """API for querying the model with similarity search."""
    try:
        # Get the query and user details
        user_query = request.json("user_query")
        collection_name = request.json("user_collection")
        
        if not user_query or not collection_name:
            return jsonify({"error": "Missing required parameters (user_query, user_collection)."}), 400

        # Generate query embedding
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        inputs = tokenizer(user_query, return_tensors="pt", padding=True, truncation=True).to(device)
        with torch.no_grad():
            text_outputs = model(**inputs)
            sentence_embeddings = text_outputs[0][:, 0]

        query_embedding = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1).squeeze(0).cpu().tolist()

        # Perform similarity search
        retrieved_chunks = retrieve_from_qdrant(collection_name, query_embedding, top_k=5)

        # Pass retrieved chunks and query to Gemini LLM
        response = LLM(retrieved_chunks, user_query)

        return jsonify({"user_query": user_query, "response": response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
