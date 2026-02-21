from flask import Flask, render_template, request , session , redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from flask_mail import Mail
import os
from werkzeug.utils import secure_filename
import math



with open('templates/config.json', 'r') as c:
    P=json.load(c)["params"]
    
app = Flask(__name__)
app.secret_key = P['secret_key']
app.config['UPLOAD_FOLDER']=P['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME = P['gmail_user'], 
    MAIL_PASSWORD = P['gmail_password'] )
mail = Mail(app)


if P['local_server']:
    app.config['SQLALCHEMY_DATABASE_URI'] = P['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = P['prod_uri']


db = SQLAlchemy(app)

class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_num = db.Column(db.String(20), nullable=False)
    mes = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=True)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.DateTime, nullable=True)
    img_file = db.Column(db.String(12), nullable=False)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(P['no_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(P['no_of_posts']):(page-1)*int(P['no_of_posts'])+ int(P['no_of_posts'])]
    if page==1:
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)

    is_last = (page == last)
    return render_template('index.html', params=P, posts=posts, prev=prev, next=next, is_last=is_last)

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    
    if 'user' in session and session['user'] == P['admin_user']:
        posts = Posts.query.all()
        return render_template("dashboard.html",params=P,posts=posts)
    
    
    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if username == P['admin_user'] and userpass == P['admin_password']:
            session['user'] = username
            posts = Posts.query.all()
            return render_template("dashboard.html",params=P,posts=posts)

    
    else:
        return render_template("login.html",params=P)

@app.route("/about")
def about():
    return render_template("about.html",params=P)

@app.route("/post")
def post():
    return render_template("post.html",params=P)

@app.route("/post/<string:post_slug>", methods=['GET']) 
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html",params=P,post=post)

@app.route("/edit/<string:sno>", methods=['POST', 'GET']) 
def edit(sno):
    if 'user' in session and session['user'] == P['admin_user']:

        if request.method == 'POST' and sno == '0':
            box_title = request.form.get('title')
            box_tagline = request.form.get('tagline')
            box_slug = request.form.get('slug')
            box_content = request.form.get('content')
            box_img_file = request.form.get('img_file')
            date=datetime.now()
            post = Posts(title=box_title, tagline=box_tagline, slug=box_slug, content=box_content, img_file=box_img_file, date=date)
            db.session.add(post)
            db.session.commit()
            return redirect("/dashboard")
        
        
        if request.method == 'POST' and sno != '0':
            post = Posts.query.filter_by(sno=sno).first()

            
            post.title = request.form.get('title')
            post.tagline = request.form.get('tagline')
            post.slug = request.form.get('slug')
            post.content = request.form.get('content')
            post.img_file = request.form.get('img_file')
           

            db.session.commit()
            return redirect("/dashboard")


              
    posts = Posts.query.filter_by(sno=sno).first()
    return render_template("edit.html",params=P, post=posts ,sno=sno)

@app.route("/delete/<string:sno>", methods=['POST', 'GET'])
def delete(sno):
    if 'user' in session and session['user'] == P['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect("/dashboard")


@app.route("/uploader", methods=['POST', 'GET'])
def uploader():
        if 'user' in session and session['user'] == P['admin_user']:
            if request.method == 'POST':
                f = request.files['file1']
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename) ))
                return "Uploaded successfully"

@app.route("/logout", methods=['POST', 'GET'])
def logout():
    session.pop('user', None)
    return redirect("/dashboard")

@app.route("/contact", methods=['POST', 'GET'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contact(name=name, email=email, phone_num=phone, mes=message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients=[P['gmail_user']],
                          body=message + "\n" + "Phone number:" +  phone)
        
    return render_template("contact.html",params=P)

app.run(debug=True)




