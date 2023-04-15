from flask import Flask, request, render_template, session
from flask import redirect, make_response, jsonify
from functools import wraps
import os

from flask_restful import Resource, Api
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required, verify_jwt_in_request
from flask_jwt_extended import JWTManager, get_jwt_identity, get_jwt
from flask_jwt_extended import set_access_cookies, unset_access_cookies


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "secretkey"
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = False
jwt = JWTManager(app)
jwt.init_app(app)
app = Flask(__name__)
app.secret_key = "secretkey"
app.config["UPLOADED_PHOTOS_DEST"] = "static"
app.config["JWT_SECRET_KEY"] = "secretkey"
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = False
app.config["JWT_COOKIE_CSRF_PROTECT"] = False

jwt = JWTManager(app)
jwt.init_app(app)

books = [
    {
        "id": 1,
        "author": "Eric Reis",
        "country": "USA",
        "language": "English",
        "title": "Lean Startup",
        "year": 2011,
        "pages": 200,
        "img_uploaded": True
    },
    {
        "id": 2,
        "author": "Mark Schwartz",
        "country": "USA",
        "language": "English",
        "title": "A Seat at the Table",
        "year": 2017,
        "pages": 200,
        "img_uploaded": True
    },
    {
        "id": 3,
        "author": "James Womak",
        "country": "USA",
        "language": "English",
        "title": "Lean Thinking",
        "year": 1996,
        "pages": 200,
        "img_uploaded": True
    },
    {
        "id": 4,
        "author": "Neal Stephenson",
        "country": "USA",
        "language": "English",
        "title": "Snow Crash",
        "year": 1992,
        "pages": 200,
        "img_uploaded": True
    },
    {
        "id": 5,
        "author": "Douglas Adams",
        "country": "UK",
        "language": "English",
        "title": "The Hitchhiker's Guide to the Galaxy",
        "year": 1979,
        "pages": 200,
        "img_uploaded": True
    },
]

users = [
    {"username": "testuser", "password": "testuser", "role": "admin"},
    {"username": "John", "password": "John", "role": "reader"},
    {"username": "Anne", "password": "Anne", "role": "admin"},
    {"username": "Neal", "password": "secret123", "role": "admin"},
    {"username": "Douglas", "password": "123secret", "role": "reader"}
]

def get_next_id():
    return sorted([b['id'] for b in books])[-1] + 1

def admin_required(fn):
   @wraps(fn)
   def wrapper(*args, **kwargs):
        # https://flask-jwt-extended.readthedocs.io/en/stable/add_custom_data_claims/?highlight=get_jwt#storing-additional-data-in-jwts
        claims = get_jwt()
        if claims['role'] != 'admin':
            return jsonify(msg= 'Admins only!'), 403
        return fn(*args, **kwargs)
   return wrapper


def checkUser(username, password):
    for user in users:
        if username in user["username"] and password in user["password"]:
            return {"username": user["username"], "role": user["role"]}
    return None


@app.route("/", methods=["GET"])
def firstRoute():
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        validUser = checkUser(username, password)
        if validUser != None:
            # set JWT token

            user_claims = {"role": validUser["role"]}
            access_token = create_access_token(
                username, additional_claims=user_claims)

            response = make_response(
                render_template(
                    "index.html", title="books", username=username, books=books
                )
            )
            response.status_code = 200
            # add jwt-token to response headers
            response.headers.extend({"jwt-token": access_token})
            set_access_cookies(response, access_token)
            return response

    return render_template("register.html")


@app.route("/logout")
def logout():
    response = make_response(
        render_template("register.html")
    )
    # invalidate the JWT token
    response.status_code = 200
    unset_access_cookies(response)

    return response


@app.route("/books", methods=["GET"])
@jwt_required()
def getBooks():
    try:
        username = get_jwt_identity()
        return render_template('books.html', username=username, books=books)
    except:
        return render_template("register.html")


@app.route("/addbook", methods=["GET", "POST"])
@jwt_required()
@admin_required
def addBook():
    username = get_jwt_identity()
    if request.method == "GET":
        return render_template("addbook.html", username=username)
    if request.method == "POST":
        # expects pure json with quotes everywheree
        author = request.form.get("author")
        title = request.form.get("title")
        country = request.form.get("country")
        language = request.form.get("language")
        year = request.form.get("year")
        newbook = {
            "id": get_next_id(),
            "author": author, 
            "title": title,
            "country": country,
            "language": language,
            "year": year,
            "img_uploaded": False
        }
        books.append(newbook)
        return render_template(
            "books.html", books=books, username=username, title="books"
        )
    else:
        return 400


@app.route("/addimage", methods=["GET", "POST"])
@jwt_required()
@admin_required
def addimage():
    username = get_jwt_identity()
    if request.method == "GET":
        return render_template("addimage.html")
    elif request.method == "POST":
        image = request.files["image"]
        id = request.form.get("number")  # use id to number the image
        imagename = "image" + id + ".png"
        image.save(os.path.join(app.config["UPLOADED_PHOTOS_DEST"], imagename))
        print(image.filename)

        for i,b in enumerate(books):
            if int(b['id']) == int(id):
                books[i]['img_uploaded'] = True

        return render_template(
            "books.html", books=books, username=username, title="books"
        )

    return "all done"


@app.route("/delbook", methods=["GET", "POST"])
@jwt_required()
@admin_required
def delBook():
    username = get_jwt_identity()
    if request.method == "GET":
        return render_template("delbook.html", username=username)
    if request.method == "POST":
        # expects pure json with quotes everywheree
        
        id = request.form.get("id")

        book_index = 0
        for i, b in enumerate(books):
            if int(b['id']) == int(id):
                book_index = i
        
        del books[book_index]

        return render_template(
            "books.html", books=books, username=username, title="books"
        )
    else:
        return 400

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
