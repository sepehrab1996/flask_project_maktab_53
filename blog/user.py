import base64
import hashlib
import re
import uuid
from bson import ObjectId
from collections import Counter

from flask import Blueprint, render_template, request, redirect, session
from werkzeug.utils import secure_filename

from blog.db import get_db

bp = Blueprint("user", __name__)


@bp.route("/profile/")
def profile():
    db = get_db()
    login_user = db.users.find({"username": session["username"]}, {"_id": 0})
    return render_template("profile_content.html", logged_in_user=login_user[0])


@bp.route("/edit-profile/")
def edit_profile():
    db = get_db()
    login_user = db.users.find({"username": session["username"]}, {"_id": 0})
    return render_template("edit_profile_content.html", logged_in_user=login_user[0])


@bp.route("/merge_change/", methods=["POST"])
def merge_change():
    if request.method == 'POST':
        db = get_db()
        myquery = {"username": session["username"]}
        f_name = request.form.get('f_name')
        l_name = request.form.get('l_name')
        email = request.form.get('email')
        phone_number = request.form.get('phone')
        f = request.files.get('image')
        password = request.form.get('new_password')
        confirm_password = request.form.get('new_confirm_password')
        # update name and lastname
        name_lastname = {
            'f_name': f_name,
            'l_name': l_name,
        }
        for item in name_lastname:
            if name_lastname[item]:
                newvalues = {"$set": {item: name_lastname[item]}}
                db.users.update_one(myquery, newvalues)
        # update email
        regex_for_email = r"^[a-zA-Z0-9]+[\._]?[a-zA-Z0-9]+[@]\w+[.]\w{2,3}$"
        if email:
            if not re.search(regex_for_email, email):
                return "ایمیل نامعتبر است"
            newvalues = {"$set": {'email': email}}
            db.users.update_one(myquery, newvalues)
        # update phone_number
        regex_for_phone = r"^(\+98?)?{?(0?9[0-9]{9,9}}?)$"
        if phone_number:
            if not re.search(regex_for_phone, phone_number):
                return "شماره موبایل نامعتبر است"
            newvalues = {"$set": {'phone_number': phone_number}}
            db.users.update_one(myquery, newvalues)
        # update image
        if f:
            file_name = secure_filename(f.filename)
            f.save('blog/static/img/profiles/' + file_name)
            image = file_name
            newvalues = {"$set": {'image': image}}
            db.users.update_one(myquery, newvalues)
        if password:
            salt = base64.urlsafe_b64encode(uuid.uuid4().bytes).hex()
            hashed_password = hashlib.sha512((password + salt).encode()).hexdigest()
            if password != confirm_password:
                return 'رمز عبور با تکرار خود همخوانی ندارد'
            newvalues = {"$set": {'password': hashed_password, 'salt': salt}}
            db.users.update_one(myquery, newvalues)
        if confirm_password:
            if password != confirm_password:
                return 'رمز عبور با تکرار خود همخوانی ندارد'
        return "success"


@bp.route("/my_posts/")
def my_posts():
    db = get_db()
    user_posts = db.posts.find({"owner": session["username"]}, )
    sort_user_posts = user_posts.sort("pub_date", -1)

    list_of_user_posts = list()
    for item in sort_user_posts:
        item["_id"] = str(item["_id"])
        list_of_user_posts.append(item)
    return render_template("my_posts_content.html", list_of_user_posts=(list_of_user_posts, session))


@bp.route("/delete_post/", methods=["POST"])
def delete_post():
    if request.method == 'POST':
        db = get_db()
        db.posts.delete_one({"_id": ObjectId(list(request.form.keys())[0])})
    return "پست مورد نظر با موفقیت حذف گردید"


@bp.route('/change-state/', methods=["POST"])
def post_state():
    db = get_db()
    user_posts = db.posts.find({"owner": session["username"]}, )
    state = int(request.form.get('state'))
    post_id = request.form.get('post_id')[3:]
    for item in user_posts:
        if str(item['_id']) == post_id:
            new_val = {"$set": {'active_state': state}}
            db.posts.update_one(item, new_val)
    return " "


@bp.route('/like_post/', methods=["POST"])
def like_post():
    db = get_db()
    all_posts = db.posts.find()
    like_state = int(request.form.get('like_state'))
    post_id = request.form.get('post_id')[3:]
    for item in all_posts:
        if str(item['_id']) == post_id and like_state == 0:
            new_val = {"$push": {'liked_by': session["username"]}}
            db.posts.update_one(item, new_val)
            like_state = 1
        elif str(item['_id']) == post_id and like_state == 1:
            new_val = {"$pull": {'liked_by': session["username"]}}
            db.posts.update_one(item, new_val)
            like_state = 0
    my_dict = {"like_state": like_state}
    return my_dict


@bp.route('/edit_post/', methods=["POST", "GET"])
def edit_post():
    if request.method == 'POST':
        db = get_db()
        post_id = request.form.get('post_id')[3:]
        post_id = ObjectId(post_id)
        selected_post = db.posts.find_one({"_id": post_id})
        selected_post["_id"] = str(selected_post["_id"])
        db = get_db()
        # post_id = request.form.get('post_id')[3:]
        # post_id = ObjectId(post_id)
        list_of_dict = db.posts.find({}, {"tags": 1, "_id": 0})
        list_of_list = [item["tags"] for item in list_of_dict]
        list_of_list_within_none = [item for item in list_of_list if item is not None]
        all_tags = [item for sublist in list_of_list_within_none for item in sublist]
        counter = Counter(all_tags).most_common()
        list_of_all_tags = [item[0] for item in counter]
        if len(counter) >= 5:
            list_of_all_tags = list_of_all_tags[0:5]
        print(list_of_all_tags)
        return render_template("edit_post_content.html", selected_post=selected_post, recommendation_tags_for_edit=list_of_all_tags)



@bp.route("/post-edit-in-database/", methods=["POST"])
def edit_post_in_database():
    db = get_db()
    if request.method == 'POST':
        title = request.form.get('title')
        main_text = request.form.get('main_text')
        tags = request.form.get('edit_tags')
        new_list_of_tags = str(tags).replace("['", "").replace("']", "").split(",")
        if new_list_of_tags[0] == "":
            new_list_of_tags = None
        id_of_post = request.form.get("_id")
        myquery = {"_id": ObjectId(id_of_post)}
        fields = {
            'title': title,
            'main_text': main_text,
            'tags': new_list_of_tags,
        }
        for item in fields:
            if item != "tags":
                if fields[item]:
                    newvalues = {"$set": {item: fields[item]}}
                    db.posts.update_one(myquery, newvalues)
            else:
                if fields[item]:
                    tags = fields[item]
                    for tag in tags:
                        tag_in_database = db.tag_db.find({"tag_name": tag}, {"_id": 0})
                        if tag_in_database.count() == 0:
                            db.tag_db.insert_one({"tag_name": tag})
                newvalues = {"$set": {item: fields[item]}}
                db.posts.update_one(myquery, newvalues)
        return "OK"


@bp.route("/posts-list-by-tag/", methods=["POST"])
def search_by_tag():
    if request.method == 'POST':
        db = get_db()
        posts_by_tag = db.posts.find({"tags": request.form.get("tag"), "active_state": 1})
        list_posts_by_tag = list()
        for item in posts_by_tag:
            item["_id"] = str(item["_id"])
            list_posts_by_tag.append(item)
        return render_template("posts_by_tag_content.html", posts_by_tag=(list_posts_by_tag, session))


@bp.route('/show_tag_recommendation/', methods=["GET"])
def show_tag_recommendation():
    db = get_db()
    # post_id = request.form.get('post_id')[3:]
    # post_id = ObjectId(post_id)
    list_of_dict = db.posts.find({}, {"tags": 1, "_id": 0})
    list_of_list = [item["tags"] for item in list_of_dict]
    list_of_list_within_none = [item for item in list_of_list if item is not None]
    all_tags = [item for sublist in list_of_list_within_none for item in sublist]
    counter = Counter(all_tags).most_common()
    list_of_all_tags = [item[0] for item in counter]
    if len(counter) >= 5:
        list_of_all_tags = list_of_all_tags[0:5]
    dict_tags = {"list_of_all_tags":list_of_all_tags}
    return dict_tags
