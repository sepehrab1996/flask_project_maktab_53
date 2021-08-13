from flask import Blueprint, render_template, request, redirect, session, url_for
from werkzeug.utils import secure_filename
import hashlib
import base64
import uuid

from blog.db import get_db

bp = Blueprint("blog", __name__)


@bp.route('/', defaults={'page': None})
@bp.route('/<page>/')
def index(page):
    if page is None:
        return render_template('base.html')
    else:
        if page not in ('home', 'login', 'register', 'profile'):
            return "Page not Found!", 404
        content_html = f"{page}_content.html"
        if page in ('login', 'register'):
            return render_template(f'auth/{content_html}')
        else:
            return render_template(content_html)


@bp.route("/register", methods=["POST"])
def register():
    if request.method == 'POST':
        f_name = request.form.get('f_name')
        l_name = request.form.get('l_name')
        username = request.form.get('username')
        password = request.form.get('password')

        salt = base64.urlsafe_b64encode(uuid.uuid4().bytes).hex()
        hashed_password = hashlib.sha512((password + salt).encode()).hexdigest()

        email = request.form.get('email')
        phone_number = request.form.get('phone')
        f = request.files.get('image')
        if f:
            file_name = secure_filename(f.filename)
            f.save('blog/static/img/' + file_name)
            image = file_name
    else:
        image = None

    db = get_db()
    user = {'f_name': f_name, 'l_name': l_name, 'password': hashed_password, 'salt': salt, 'username': username,
            'email': email,
            'image': image, 'phone_number': phone_number}
    skip_username = 0
    skip_phone = 0
    for i in range(db.users.count()):
        if skip_username == 0 and skip_phone == 0:
            if username == db.users.find({}, {'username': 1, "_id": 0})[i]["username"]:
                skip_username = 1
            if phone_number == db.users.find({}, {'phone_number': 1, "_id": 0})[i]["phone_number"]:
                skip_phone = 1
    if skip_username == 0 and skip_phone == 0:
        db.users.insert_one(user)
        return {'f_name': f_name, 'l_name': l_name}

    else:
        if skip_username == 1:
            return "این نام کاربری قبلا ثبت شده است"
        return "شماره همراه قبلا ثبت شده است"


@bp.route("/login", methods=["POST"])
def login():
    db = get_db()
    username = request.form.get('username')
    password = request.form.get('password')
    login_user = db.users.find({"username": username}, {"_id": 0})

    if login_user.count() != 0:
        valid_password = login_user[0]["password"]
        generated_password = hashlib.sha512((password + login_user[0]["salt"]).encode()).hexdigest()
        if valid_password == generated_password:
            session["username"] = username
            return {'f_name': login_user[0]["f_name"], 'l_name': login_user[0]["l_name"],
                    "username": session["username"]}

        else:
            return "رمز عبور اشتباه است"
    else:
        return "نام کاربری پیدا نشد"


@bp.route("/logout", methods=["GET"])
def logout():
    session.pop('username', None)
    print(session)
    return ""


@bp.route("/post/<int:post_id>/")
def post(post_id):
    return f'post_id is {post_id}'


@bp.route("/category-posts/<int:category_id>/")
def category(category_id):
    return f'category_id is {category_id}'


@bp.route("/tag-posts/<int:tag_id>/")
def tag(tag_id):
    return f'tag_id is {tag_id}'
