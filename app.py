import os
import uuid
from flask import (
    Flask, flash, render_template, 
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)

@app.route("/")
@app.route("/get_devs")
def get_devs():
    developers = list(mongo.db.developers.find())
    return render_template("developers.html", developers=developers)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    developers = list(mongo.db.developers.find({"$text": {"$search": query}}))
    return render_template("developers.html", developers=developers)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "email": request.form.get("email").lower(),
            "password": generate_password_hash(request.form.get("password")),
        }

        mongo.db.users.insert_one(register)

        session["user"] = request.form.get("username").lower()
        flash("Registration successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(request.form.get("username")))
                    return redirect(url_for(
                        "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    userdevs = list(mongo.db.developers.find({"created_by": username}))

    if session["user"]:
        return render_template(
            "profile.html", username=username, userdevs=userdevs)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_dev", methods=["GET", "POST"])
def add_dev():
    if request.method == "POST":
        
        looking_for_work = "on" if request.form.get("looking_for_work") else "off"

        if "dev_image" in request.files:
            dev_image = request.files['dev_image']
            if dev_image.filename != '':
                dev_image.filename = str(uuid.uuid4())
            mongo.save_file(dev_image.filename, dev_image)

        dev = {
            "first_name": request.form.get("first_name"),
            "last_name": request.form.get("last_name"),
            "dev_image": dev_image.filename,
            "looking_for_work": looking_for_work,
            "skills": request.form.getlist("skills"),
            "created_by": session["user"],
            "img_id": result
        }

        mongo.db.developers.insert_one(dev)
        flash("Developer successfully added!")
        return redirect(url_for("get_devs"))

    skills = mongo.db.skills.find().sort("skill_name", 1)
    return render_template("add_dev.html", skills=skills)


@app.route('/img_uploads/<filename>')
def img_uploads(filename):
    return mongo.send_file(filename)


@app.route("/edit_dev/<dev_id>", methods=["GET", "POST"])
def edit_dev(dev_id):
    
    if request.method == "POST":
        looking_for_work = "on" if request.form.get("looking_for_work") else "off"
        devsubmit = {
            "first_name": request.form.get("first_name"),
            "last_name": request.form.get("last_name"),
            "looking_for_work": looking_for_work,
            "skills": request.form.getlist("skills"),
            "created_by": session["user"]
        }
        mongo.db.developers.update({"_id": ObjectId(dev_id)}, devsubmit)
        flash("Developer successfully updated!")

    dev = mongo.db.developers.find_one({"_id": ObjectId(dev_id)})
    skills = mongo.db.skills.find().sort("skill_name", 1)
    return render_template("edit_dev.html", dev=dev, skills=skills)

@app.route("/delete_dev/<dev_id>")
def delete_dev(dev_id):
    mongo.db.developers.remove({"_id": ObjectId(dev_id)})
    flash("Developer successfully deleted!")
    return redirect(url_for("get_devs"))


@app.route("/get_skills")
def get_skills():
    skills = list(mongo.db.skills.find().sort("skill_name", 1))
    return render_template("skills.html", skills = skills)


@app.route("/add_skill", methods=["GET", "POST"])
def add_skill():
    if request.method == "POST":
        skill = {
            "skill_name": request.form.get("skill_name")
        }
        mongo.db.skills.insert_one(skill)
        flash("New skill added!")
        return redirect(url_for("get_skills"))
    return render_template("add_skill.html")


@app.route("/edit_skill/<skill_id>", methods=["GET", "POST"])
def edit_skill(skill_id):
    if request.method == "POST":
        submit = {
            "skill_name": request.form.get("skill_name")
        }
        mongo.db.skills.update({"_id": ObjectId(skill_id)}, submit)
        flash("Skill updated successfully")
        return redirect(url_for("get_skills"))
    skill = mongo.db.skills.find_one({"_id": ObjectId(skill_id)})
    return render_template("edit_skill.html", skill=skill)


@app.route("/delete_skill/<skill_id>")
def delete_skill(skill_id):
    mongo.db.skills.remove({"_id": ObjectId(skill_id)})
    flash("Skill successfully deleted!")
    return redirect(url_for("get_skills"))


@app.route("/admin")
def admin():
    skills = list(mongo.db.skills.find().sort("skill_name", 1))
    users = list(mongo.db.users.find())
    developers = list(mongo.db.developers.find())
    return render_template(
        "admin.html", skills = skills, developers = developers, users = users
        )


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
