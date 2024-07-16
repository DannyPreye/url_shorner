from flask import Blueprint, request, jsonify
from src.database import db, Bookmark
from src.constants.http_status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT, HTTP_404_NOT_FOUND
import validators

from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import  swag_from

bookmarks=Blueprint("bookmarks",__name__,url_prefix="/api/v1/bookmarks")



@bookmarks.route("/", methods=["POST","GET"])
@jwt_required()
def handle_bookmark():
    current_user=get_jwt_identity()
    if request.method == "POST":
        body=request.get_json().get("body","")
        url=request.get_json().get("url","")
        if not url:
            return jsonify({"error": "url is required"}), HTTP_400_BAD_REQUEST
        if not validators.url(url):
            return jsonify({
                "error":"invalid url"
            }),HTTP_400_BAD_REQUEST

        if Bookmark.query.filter_by(url=url).first():
             return jsonify({
                "error":"url already exists"
            }),HTTP_409_CONFLICT

        print(f"Body: {body}, URL: {url}")
        bookmark = Bookmark(url=url, body=body, user_id=current_user)
        db.session.add(bookmark)
        db.session.commit()
        return jsonify({
            "message":"Bookmark created successfully",
            "bookmark":{
                "id":bookmark.id,
                "url":bookmark.url,
                "short_url":bookmark.short_url,
                "visits": bookmark.visits,
                "body":bookmark.body,
                "created_at":bookmark.created_at,
                "updated_at":bookmark.updated_at

            }
        }), HTTP_201_CREATED
    else:
        page=request.args.get("page",1, type=int)
        per_page= request.args.get("per_page", 10, type=int)
        bookmarks= Bookmark.query.filter_by(user_id=current_user).paginate(page=page, per_page=per_page)
        data =[]
        for item in bookmarks:
            data.append({
                  "id":item.id,
                "url":item.url,
                "short_url":item.short_url,
                "visits": item.visits,
                "body":item.body,
                "created_at":item.created_at,
                "updated_at":item.updated_at
            })
        meta={
            "page":bookmarks.page,
            "pages":bookmarks.pages,
            "total_count": bookmarks.total,
            "prev_page": bookmarks.prev_num,
            "next_page": bookmarks.next_num,
            "has_next": bookmarks.has_next,
            "has_prev": bookmarks.has_prev

        }
        return jsonify({"data":data, "meta":meta}), HTTP_200_OK


@bookmarks.get("/<int:id>")
@jwt_required()
def get_single_bookmark(id):
    current_user=get_jwt_identity()

    bookmark=Bookmark.query.filter_by(id=id, user_id=current_user).first()

    if not bookmark:
        return jsonify({"message":"item not found"}),HTTP_404_NOT_FOUND

    return jsonify({
        "bookmark":{
               "id":bookmark.id,
                "url":bookmark.url,
                "short_url":bookmark.short_url,
                "visits": bookmark.visits,
                "body":bookmark.body,
                "created_at":bookmark.created_at,
                "updated_at":bookmark.updated_at
        }
    }),HTTP_200_OK

@bookmarks.delete("/<int:id>")
@jwt_required()
def delete_bookmark(id):
    current_user=get_jwt_identity()

    bookmark=Bookmark.query.filter_by(id=id, user_id=current_user).first()

    if not bookmark:
        return jsonify({"message":"item not found"}),HTTP_404_NOT_FOUND

    db.session.delete(bookmark)
    db.session.commit()

    return jsonify({"message":"item deleted"}),HTTP_200_OK


@bookmarks.patch("/<int:id>")
@bookmarks.put("/<int:id>")
@jwt_required()
def update_bookmark(id):
    current_user=get_jwt_identity()

    bookmark=Bookmark.query.filter_by(id=id, user_id=current_user).first()

    if not bookmark:
        return jsonify({"message":"item not found"}),HTTP_404_NOT_FOUND

    body=request.get_json().get("body","")
    url=request.get_json().get("url","")
    if not validators.url(url):
        return jsonify({
                "error":"invalid url"
            }),HTTP_400_BAD_REQUEST

    bookmark.url=url
    bookmark.body=body

    db.session.commit()

    return jsonify({
        "message":"item updated",
        })

@bookmarks.get("/stats")
@jwt_required()
@swag_from("./docs/bookmarks/stats.yaml")
def get_stats():
    data=[]
    current_user=get_jwt_identity()
    bookmark=Bookmark.query.filter_by(user_id=current_user).all()

    for item in bookmark:
        new_link={
            "visits": item.visits,
            "url":item.url,
            "id":item.id,
            "short_url": item.short_url
        }
        data.append(new_link)

    return jsonify({"data":data}),HTTP_200_OK


