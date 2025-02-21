import os
from flask import Flask
from flasgger import Swagger
from models import db
from flask_migrate import Migrate

def init_extensions(app):
    # Inicializa o SQLAlchemy
    db.init_app(app)
    Migrate(app, db)
    
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/apispec_1.json",
                "rule_filter": lambda rule: True,  # inclui todas as rotas
                "model_filter": lambda tag: True,  # inclui todos os modelos
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/"
    }
    Swagger(app, config=swagger_config)

def register_blueprints(app):
    from controllers.auth import auth_bp
    from controllers.user import user_bp
    from controllers.post import post_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(post_bp)

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///socialmedia.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.getenv('SECRET_KEY', 'SUA_CHAVE_SECRETA')

    init_extensions(app)
    register_blueprints(app)
    
    return app

if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(host="0.0.0.0", debug=True)
