from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
import random

from models import db, User, Post

app = Flask(__name__)

# DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secretkey'

# MAIL
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'farhadabdukadirov03@gmail.com'
app.config['MAIL_PASSWORD'] = 'sysuhncdvcaupmaz'

db.init_app(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
# MODEL


with app.app_context():
    db.create_all()


# HOME (СТАРТ САЙТА)
@app.route("/")
def index():
    user = None

    if "user_id" in session:
        user = User.query.get(session["user_id"])

    return render_template("index.html", user=user)


# POSTS
@app.route("/post")
def post():
    new_post = Post.query.all()
    return render_template("post.html", posts=new_post)


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":

        title = request.form["title"]
        content = request.form["content"]

        # берём пользователя из session
        user_id = session.get("user_id")

        if not user_id:
            return redirect(url_for("login"))

        post = Post(
            title=title,
            content=content,
            user_id=user_id
        )

        db.session.add(post)
        db.session.commit()

        return redirect(url_for("post"))

    return render_template("create.html")

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    post = Post.query.get(id)

    if post:
        db.session.delete(post)
        db.session.commit()

    return redirect("/post")

@app.route("/about")
def about():
    return render_template("about.html")

# AUTH
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        confirm = request.form["confirm_password"]

        if password != confirm:
            return "Пароли не совпадают"

        hashed = bcrypt.generate_password_hash(password).decode('utf-8')

        user = User(email=email, password=hashed)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):

            code = str(random.randint(100000, 999999))
            print(code)

            session["2fa_code"] = code
            session["temp_user_id"] = user.id

            send_email(user.email, code)

            return redirect(url_for("verify_2fa"))

        return "Неверный логин или пароль"

    return render_template("login.html")
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.context_processor
def inject_user():
    user = None

    if "user_id" in session:
        user = User.query.get(session["user_id"])

    return dict(user=user)

@app.route("/debug")
def debug():
    users = User.query.all()
    return "<br>".join([u.email for u in users])




import random


@app.route("/verify", methods=["GET", "POST"])
def verify_2fa():
    if request.method == "POST":
        code = request.form["code"]

        if code == session.get("2fa_code"):

            session["user_id"] = session["temp_user_id"]

            session.pop("2fa_code", None)
            session.pop("temp_user_id", None)

            return redirect(url_for("index"))

        return "Неверный код"

    return render_template("verify.html")

def send_email(to_email, code):
    msg = Message(

        "Ваш код подтверждения",
        sender=app.config['MAIL_USERNAME'],
        recipients=[to_email]
    )
    msg.body = f"Ваш код: {code}"
    mail.send(msg)

if __name__ == "__main__":
    app.run(debug=True)