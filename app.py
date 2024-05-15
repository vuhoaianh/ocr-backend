from flask import Flask
import os
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

jwt = JWTManager(app)

CORS(app)
api = Api(app)
initialize_routes(api)
