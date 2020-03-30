from flask import Flask, render_template, redirect, request, session, url_for
import re
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt 

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quarantine_friends.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.secret_key = 'secret key'
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    password = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/on_signup', methods=['POST'])
def on_register():
    is_valid = True

    # add validations

    if is_valid:
        pw_hash = bcrypt.generate_password_hash(request.form['password'])
        new_user = User(first_name=request.form['first_name'], last_name=request.form['last_name'], email=request.form['email'], password=pw_hash)
        db.session.add(new_user)
        db.session.commit()
        user = User.query.filter_by(email=request.form['email']).first()
        session['userid'] = user.id
        return redirect('/') # change to correct page
    else:
        return redirect('/') # change to correct page

@app.route('/on_login', methods=['post'])
def on_login():
    user = User.query.filter_by(email=request.form['email']).first()
    if user == None:
        return redirect('/') # change to correct page
    elif bcrypt.check_password_hash(user.password, request.form['password']):
        session['userid'] = user.id
        return redirect('/') # change to correct page

@app.route('/on_logout')
def logout():
    session.clear()
    return redirect('/') # change to correct page

if __name__ == '__main__':
    app.run(debug=True)