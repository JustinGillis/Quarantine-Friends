from flask import Flask, render_template, redirect, request, session, url_for, flash
import re
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask import json

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
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(255))
    lat = db.Column(db.String(255))
    lng = db.Column(db.String(255))
    votes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255))
    author_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="cascade"), nullable=False)
    author = db.relationship('User', foreign_keys=[author_id], backref="user_comments")
    item_id = db.Column(db.Integer, db.ForeignKey("item.id", ondelete="cascade"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/on_signup', methods=['POST'])
def on_register():
    is_valid = True

    # validations
    if len(request.form['first_name']) < 3:
        is_valid = False
        flash('First name is too short', 'signup')
    if len(request.form['last_name']) < 3:
        is_valid = False
        flash('Last name is too short', 'signup')
    if not EMAIL_REGEX.match(request.form['email']):
        is_valid = False
        flash("Invalid email address", 'signup')
    if len(request.form['password']) < 6:
        is_valid = False
        flash('Password must be at least 6 characters', 'signup')
    if request.form['password'] != request.form['confirm_password']:
        is_valid = False
        flash('Passwords do not match', 'signup')

    if is_valid:
        pw_hash = bcrypt.generate_password_hash(request.form['password'])
        new_user = User(first_name=request.form['first_name'], last_name=request.form['last_name'], email=request.form['email'], password=pw_hash)
        db.session.add(new_user)
        db.session.commit()
        user = User.query.filter_by(email=request.form['email']).first()
        session['userid'] = user.id
        return render_template('home.html', user = user)
    else:
        return redirect('/')

@app.route('/on_login', methods=['post'])
def on_login():
    user = User.query.filter_by(email=request.form['email']).first()
    if user == None:
        flash('Could not log in', 'login')
        return redirect('/')
    elif bcrypt.check_password_hash(user.password, request.form['password']):
        session['userid'] = user.id
        return redirect('/dashboard')

@app.route('/dashboard') #had to add a 'dashboard route' after login/signup because there was no way to come back to main page after you left main page after login.- Brian
def dashboard(): 
    results = User.query.all()
    return render_template('home.html', user=results[0])

@app.route('/map')
def map():
    return render_template('map.html')

@app.route('/edit') #added 'Edit' path, but needs '<user_id>' not sure how to add that with sqlite - Brian
def edit():
    return render_template('edit.html')

#@app.route('on_edit', methods=['post']) - Brian
# def on_edit():
# needs sqlite for 'INSERT INTO'
#     return redirect("/dashboard")




# start of routes under construction

@app.route('/on_upvote/<id>')
def on_upvote(id):
    item = Item.query.filter_by(id=id).first()
    item.votes +=1
    db.session.commit()
    print('upvote complete')
    return redirect('/test')

@app.route('/on_downvote/<id>')
def on_unlike(id):
    item = Item.query.filter_by(id=id).first()
    item.votes -=1
    db.session.commit()
    print('downvote complete')
    return redirect('/test')

@app.route('/on_comment/<id>', methods=['POST'])
def on_comment(id):
    comment = Comment(content=request.form['content'], author_id=session['userid'], project_id=id)
    db.session.add(comment)
    db.session.commit()
    return redirect('/view_project/' + id)

@app.route('/on_delete_comment/<project>/<id>')
def on_delete_comment(project, id):
    existing_user = User.query.get(session['userid'])
    comment = Comment.query.get(id)
    existing_user.user_comments.remove(comment)
    db.session.commit()
    return redirect('/view_project/' + project)

# end of routes under construction





@app.route('/on_logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/test')
def test():
    items = Item.query.all()
    markers = []
    if items:
        markers = []
        for item in items:
            if item.votes >= 0:
                temp = {}
                coords = {
                    'lat' : float(item.lat),
                    'lng' : float(item.lng)
                }
                temp.update({
                    'coords' : coords,
                    'iconImage' : 'https://i.ibb.co/Zx24VKX/toilet-Paper.png',
                    'content' : '<p>Votes: %s</p><a href="on_upvote/%s">Upvote</a> <a href="on_downvote/%s">Downvote</a>' % (item.votes, item.id, item.id)
                })
                markers.append(temp)
    print('markers:', markers)
    return render_template('test.html', markers=markers)

@app.route('/on_test', methods=['POST'])
def ontest():
    print(request.form)
    new_item = Item(category=request.form['category'], lat=request.form['lat'], lng=request.form['lng'])
    db.session.add(new_item)
    db.session.commit()
    return redirect('/test')

if __name__ == '__main__':
    app.run(debug=True)