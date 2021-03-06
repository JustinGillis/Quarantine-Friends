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


upvote_table = db.Table('upvotes', 
              db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='cascade'), primary_key=True), 
              db.Column('item_id', db.Integer, db.ForeignKey('item.id', ondelete='cascade'), primary_key=True))

downvote_table = db.Table('downvotes', 
              db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='cascade'), primary_key=True), 
              db.Column('item_id', db.Integer, db.ForeignKey('item.id', ondelete='cascade'), primary_key=True))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    password = db.Column(db.String(255))
    items_this_user_upvoted = db.relationship('Item', secondary=upvote_table)
    items_this_user_downvoted = db.relationship('Item', secondary=downvote_table)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(255))
    lat = db.Column(db.String(255))
    lng = db.Column(db.String(255))
    votes = db.Column(db.Integer, default=0)
    users_who_upvoted_this_item = db.relationship('User', secondary=upvote_table)
    users_who_downvoted_this_item = db.relationship('User', secondary=downvote_table)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255))
    author_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="cascade"), nullable=False)
    author = db.relationship('User', foreign_keys=[author_id], backref="user_comments")
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255))
    authors_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="cascade"), nullable=False)
    authors = db.relationship('User', foreign_keys=[authors_id], backref="user_feedback")
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/on_signup', methods=['POST'])
def on_register():
    is_valid = True

    # validations
    # add check for existing user
    # if len(request.form['first_name']) < 3:
    #     is_valid = False
    #     flash('First name is too short', 'signup')
    # if len(request.form['last_name']) < 3:
    #     is_valid = False
    #     flash('Last name is too short', 'signup')
    # if not EMAIL_REGEX.match(request.form['email']):
    #     is_valid = False
    #     flash("Invalid email address", 'signup')
    # if len(request.form['password']) < 6:
    #     is_valid = False
    #     flash('Password must be at least 6 characters', 'signup')
    # if request.form['password'] != request.form['confirm_password']:
    #     is_valid = False
    #     flash('Passwords do not match', 'signup')

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
        flash('Could not log in')
        return redirect('/')
    elif bcrypt.check_password_hash(user.password, request.form['password']):
        session['userid'] = user.id
        return redirect('/dashboard')

@app.route('/dashboard') #had to add a 'dashboard route' after login/signup because there was no way to come back to main page after you left main page after login.- Brian
def dashboard(): 
    results = User.query.filter_by(id=session['userid']).all()
    return render_template('home.html', user=results[0])



@app.route('/edit')
def edit():
    results = User.query.get(session['userid'])
    return render_template('edit.html', user = results)

@app.route('/on_edit', methods=['post'])
def on_edit():
    user_update = User.query.get(session['userid'])
    if user_update:
        user_update.first_name = request.form['first_name']
        user_update.last_name = request.form['last_name']
        user_update.email = request.form['email']
        user_update.password = bcrypt.generate_password_hash(request.form['password'])
        db.session.commit()
        return redirect('/dashboard')
    else:
        return redirect('/edit')





# start of routes under construction
@app.route('/on_upvote/<id>')
def on_upvote(id):
    item = Item.query.get(id)
    user = User.query.get(session['userid'])

    if item in user.items_this_user_downvoted:
        user.items_this_user_downvoted.remove(item)
        db.session.commit()
        print('user removed from downvote list')

    user.items_this_user_upvoted.append(item)
    db.session.commit()
    print('user added to upvote list')

    item.votes +=1
    db.session.commit()
    print('votes increased by 1')

    print('upvote process complete')
    return redirect('/test')

@app.route('/on_downvote/<id>')
def on_unlike(id):
    item = Item.query.get(id)
    user = User.query.get(session['userid'])

    if item in user.items_this_user_upvoted:
        user.items_this_user_upvoted.remove(item)
        db.session.commit()
        print('user removed from upvote list')

    user.items_this_user_downvoted.append(item)
    db.session.commit()
    print('user added to downvote list')

    item.votes -=1
    db.session.commit()
    print('votes reduced by 1')

    print('downvote process complete')
    return redirect('/test')

@app.route('/on_comment', methods=['POST'])
def on_comment():
    comment = Comment(content=request.form['comment'], author_id=session['userid'])
    db.session.add(comment)
    db.session.commit()
    return redirect('/test')

# end of routes under construction





@app.route('/on_logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/test')
def test():
    # checks if user is logged in
    if 'userid' not in session:
        return redirect('/')

    user = User.query.get(session['userid'])
    items = Item.query.all()

    markers = []
    
    if items:

        # get logged in user info
        for item in items:

            # doesn't add item if less than 0 votes
            if item.votes >= 0:
                temp = {}

                # set coords of item
                coords = {
                    'lat' : float(item.lat),
                    'lng' : float(item.lng)
                }

                # checks category and sets correct iconImage
                if item.category == 'toiletPaper':
                    iconImage = 'https://i.ibb.co/Zx24VKX/toilet-Paper.png'

                # sets correct voting links
                if user in item.users_who_upvoted_this_item:
                    content = '<p class="text-danger" >Votes: %s</p> <a href="on_downvote/%s"><i class="far fa-thumbs-down"></i></a>' % (item.votes, item.id)
                elif user in item.users_who_downvoted_this_item:
                    content = '<p class="text-danger" >Votes: %s</p> <a href="on_upvote/%s"><i class="far fa-thumbs-up"></i></a> ' % (item.votes, item.id)
                else:
                    content = '<p class="text-danger" >Votes: %s</p> <a href="on_upvote/%s"><i class="far fa-thumbs-up"></i></a> <a href="on_downvote/%s"><i class="far fa-thumbs-down"></i></a>' % (item.votes, item.id, item.id)
                
                # updates object to marker list
                temp.update({
                    'coords' : coords,
                    'iconImage' : iconImage,
                    'content' : content
                })
                markers.append(temp)
    
    comments = Comment.query.all()

    return render_template('test.html', markers=markers, comments=comments)

@app.route('/on_test', methods=['POST'])
def ontest():
    print(request.form)
    new_item = Item(category=request.form['category'], lat=request.form['lat'], lng=request.form['lng'])
    db.session.add(new_item)
    db.session.commit()
    return redirect('/test')

#feedback routes
@app.route('/feedback')
def feedback_page():
    reviews = Feedback.query.all()
    return render_template('feedback.html', reviews=reviews)

@app.route('/on_feedback', methods=['post'])
def on_feedback():
    new_feedback = Feedback(content=request.form['reviews'], authors_id=session['userid'])
    if new_feedback:
        db.session.add(new_feedback)
        db.session.commit()
        return redirect('/feedback')
    else:
        return redirect('/feedback')
#end feedback routes

if __name__ == '__main__':
    app.run(debug=True)