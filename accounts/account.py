from flask import Flask, render_template, redirect, request, make_response, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
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
        try:
            username = request.form['username']
            password = request.form['password']

            user = collection.find_one({'username': username})
            if user and check_password_hash(user['password'], password):
                session['logged_in'] = True
                session['username'] = username
                return redirect('/home')
            else:
                error_message = "Invalid username or password. Please try again."
                return render_template("login_page.html", error_message=error_message)
        except Exception as e:
            print(e)
            return redirect('/login')
    return render_template('login_page.html')
