from flask import Flask, send_from_directory
import os
import logging
from flask_restful import Api
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from accounts.account import create_account, login, profile
from home.home import home
from resources.routes import initialize_routes
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('SECRET_KEY')

app.add_url_rule("/signup", view_func=create_account, methods=['GET', 'POST'])
app.add_url_rule("/login", view_func=login, methods=['GET', 'POST'])
app.add_url_rule("/home", view_func=home, methods=['GET', 'POST'])
app.add_url_rule("/profile", view_func=profile, methods=['GET'])

    
@app.route("/static/<path:name>", methods=['GET'])
def download_file(name):
    return send_from_directory(
       "/static", name, as_attachment=True
    )


jwt = JWTManager(app)
LOGGING_CONFIG = {
    'level': logging.ERROR,
    'filename': 'app.log',
    'filemode': 'w',
    'format': '%(name)s - %(levelname)s - %(message)s'
}

CORS(app)
api = Api(app)
initialize_routes(api)
