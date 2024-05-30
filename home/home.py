from flask import render_template, session, redirect, url_for, make_response


def home():
    return render_template("welcome.html")