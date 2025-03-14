from flask import Flask
from users.user_routes import users_db
from conversation.conversation_routes import conversation_blueprint
from responses.responses_routes import responses
from queries.queries_routes import queries  # Importing queries routes
from gemini_api import gemini_blueprint

app = Flask(__name__)
app.register_blueprint(users_db, url_prefix="/app")
app.register_blueprint(conversation_blueprint, url_prefix="/app")
app.register_blueprint(responses, url_prefix="/app")
app.register_blueprint(queries, url_prefix="/app")  # Register queries blueprint
app.register_blueprint(gemini_blueprint, url_prefix="/app")

if __name__ == '__main__':
    app.run(debug=True)
