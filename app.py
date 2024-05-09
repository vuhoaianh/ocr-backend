from flask import Flask
import os
from flask_restful import Api
from flask_cors import CORS
from flask_pymongo import PyMongo
# from flask_session import Session
from accounts.account import create_account, login
from home.home import home
from resources.routes import initialize_routes

secret_key = os.urandom(24)

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key


app.add_url_rule("/signup", view_func=create_account, methods=['GET', 'POST'])
app.add_url_rule("/login", view_func=login, methods=['GET', 'POST'])
app.add_url_rule("/home", view_func=home, methods=['GET', 'POST'])

CORS(app)
api = Api(app)
initialize_routes(api)
