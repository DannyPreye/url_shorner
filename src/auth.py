from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash,generate_password_hash
from src.constants.http_status_codes import HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT, HTTP_201_CREATED, HTTP_200_OK
import validators
from src.database import User, db
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity
from flasgger import  swag_from

auth=Blueprint("auth",__name__,url_prefix="/api/v1/auth")

@auth.post("/register")
@swag_from("./docs/auth/register.yaml")
def register():
    username=request.json["username"]
    email=request.json["email"]
    password=request.json["password"]
    print(f"{username}")
    if len(password) < 6:
        return jsonify({"error":"password is too short"}), HTTP_400_BAD_REQUEST
    if len(username) < 3:
        return jsonify({"error":"username is too short"}), HTTP_400_BAD_REQUEST
    if  not username.isalnum() or " " in username:
        return jsonify({"error":"username should be alphanumeric, also no spaces"}), HTTP_400_BAD_REQUEST
    if not validators.email(email):
        return jsonify({"error":"your email is not valid"}), HTTP_400_BAD_REQUEST

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({"error":"email is already taken"}), HTTP_409_CONFLICT
    if User.query.filter_by(username=username).first() is not None:
        return jsonify({"error":"username is already taken"}), HTTP_409_CONFLICT

    pwd_hash=generate_password_hash(password)

    user=User(username=username, password=pwd_hash, email=email)

    db.session.add(user)
    db.session.commit()

    return jsonify({"message":"User has been created", "user":{"username":user.username,"email":user.email}}),HTTP_201_CREATED


@auth.post("/login")
@swag_from("./docs/auth/login.yaml")
def login():
    email=request.json.get("email","")
    password=request.json.get("password","")
    user= User.query.filter_by(email=email).first()

    if user:
        is_pass_correct=check_password_hash(user.password, password)
        if  is_pass_correct:
            refresh=create_refresh_token(identity=user.id)
            access=create_access_token(identity=user.id)
            return jsonify({
                   "refresh_token": refresh,
                   "access_token":access,
                "user":{
                    "username":user.username,
                    "email":user.email
                }
            }),HTTP_200_OK
    return jsonify({"message":"incorrect email or password"}), HTTP_400_BAD_REQUEST

@auth.get("/me")
@jwt_required()
def me():
    user_id=get_jwt_identity()

    user = User.query.filter_by(id=user_id).first()

    return jsonify({
      "user":{
            "username":user.username,
             "email":user.email
      }
    }),HTTP_200_OK

@auth.get("/token/refresh")
@jwt_required(refresh=True)
def refresh_token():
    identity=get_jwt_identity()
    access=create_access_token(identity=identity)

    return jsonify({
        "access_token":access
    }),HTTP_200_OK
