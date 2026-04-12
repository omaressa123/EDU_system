from flask import Flask
from EDU_system.models import db
from EDU_system.config import Config
from EDU_system.blueprints.auth import auth_bp
from EDU_system.blueprints.profile import profile_bp
from EDU_system.blueprints.search import search_bp
from EDU_system.blueprints.chat import chat_bp
from EDU_system.blueprints.application import application_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize DB
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')
    app.register_blueprint(search_bp, url_prefix='/api/search')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(application_bp, url_prefix='/api/application')

    @app.route('/')
    def home():
        return app.send_static_file('index.html')

    @app.route('/static/<path:path>')
    def send_static(path):
        return app.send_static_file(path)

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
