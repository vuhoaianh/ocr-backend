from flask import Flask, render_template, redirect, request, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import os

load_dotenv()

client = MongoClient(os.getenv('DB_HOST'), int(os.getenv('DB_PORT')))
db = client[os.getenv('DB_USER')]
collection = db['db_users']


def create_account():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            re_password = request.form['re_password']

            existing_user = collection.find_one({'username': username})
            if existing_user:
                error_message = "Username already exists. Please choose a different one."
                return render_template('register_page.html', error_message=error_message)

            # Check if the password matches re-password
            if password != re_password:
                error_message = "Password and re-password do not match."
                return render_template('register_page.html', error_message=error_message)

            hash_password = generate_password_hash(password, method='pbkdf2:sha256')
            user_data = {
                'username': username,
                'password': hash_password
            }
            collection.insert_one(user_data)
            return redirect('/login')
        except Exception as e:
            return redirect('/signup')
    return render_template('register_page.html')


def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = collection.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            access_token = create_access_token(identity={'id': user['username']})
            return jsonify(message='Login successful', token=access_token), 200
        else:
            return jsonify(message='Invalid username or password'), 401

@jwt_required()
def profile():
    user_identity = get_jwt_identity()
    user_id = user_identity['id']
    return jsonify(message='This is your profile', userId=user_id), 200