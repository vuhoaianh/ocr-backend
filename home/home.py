from flask import render_template, session, redirect, url_for


def home():
    # if 'logged_in' not in session or not session['logged_in']:
    #     return redirect(url_for('login'))
    username = session.get("username")
    return username
    # return render_template("welcome.html")