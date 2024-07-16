from flask import Flask,redirect,jsonify
from flask_migrate import Migrate
import os
from src.auth import auth
from src.bookmark import bookmarks
from src.database import db, Bookmark
from flask_jwt_extended import JWTManager
from src.constants.http_status_codes import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from flasgger import Swagger, swag_from
from src.config.swagger import template, swagger_config



def create_app(test_config=None, ):

    app=Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get("SECRET_KEY"),
            SQLALCHEMY_DATABASE_URI=os.environ.get("SQLALCHEMY_DB_URI"),
            JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY"),
            SWAGGER={
                "title":"Bookmarks API",
                "uiversion":3
            }
            )


    else:
        app.config.from_mapping(test_config)
    db.app=app
    db.init_app(app)

    JWTManager(app)

    migrate=Migrate(app,db)

    app.register_blueprint(auth)
    app.register_blueprint(bookmarks)

    Swagger(app,config=swagger_config,template=template)

    @app.get("/<short_url>")
    @swag_from("./docs/short_url.yaml")
    def redirect_to_url(short_url):
        bookmark = Bookmark.query.filter_by(short_url=short_url).first_or_404()
        if bookmark:
            bookmark.visits += 1
            db.session.commit()
            return redirect(bookmark.url)
    @app.errorhandler(404)
    def page_not_found(e):
        return jsonify({
            "error":"page not found"
        }),HTTP_404_NOT_FOUND

    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({
            "error":"internal server error"
        }),HTTP_500_INTERNAL_SERVER_ERROR


    return app


