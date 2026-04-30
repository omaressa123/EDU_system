from flask import Flask, session, request, redirect, url_for, jsonify, send_from_directory
from models import db
from config import Config
from blueprints.auth import auth_bp
from blueprints.profile import profile_bp
from blueprints.search import search_bp
from blueprints.chat import chat_bp
from blueprints.application import application_bp
from blueprints.admin import admin_bp
from models import User
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import jwt

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
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    @app.route('/')
    def home():
        return send_from_directory('static', 'index.html')

    @app.route('/admin')
    def admin_page():
        return send_from_directory('static', 'admin.html')

    @app.route('/admin-login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            username = (request.form.get('username') or '').strip()
            password = request.form.get('password')

            user = User.query.filter((User.email == username) | (User.name == username)).first()
            if not user or user.role != 'admin' or not check_password_hash(user.password_hash, password):
                return jsonify({'success': False, 'message': 'Invalid admin credentials'}), 401

            session['admin_logged_in'] = True
            session['admin_user_id'] = user.id
            token = jwt.encode({
                'user_id': user.id,
                'role': user.role,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, Config.SECRET_KEY, algorithm='HS256')
            return jsonify({'success': True, 'token': token, 'user_id': user.id, 'role': user.role})
        
        return send_from_directory('static', 'admin_login.html')

    @app.route('/dashboard')
    def dashboard():
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return send_from_directory('static', 'dashboard.html')

    @app.route('/admin-token')
    def admin_token():
        if not session.get('admin_logged_in') or not session.get('admin_user_id'):
            return jsonify({'message': 'Not authenticated'}), 401
        user = User.query.get(session.get('admin_user_id'))
        if not user or user.role != 'admin':
            session.clear()
            return jsonify({'message': 'Invalid admin session'}), 401
        token = jwt.encode({
            'user_id': user.id,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, Config.SECRET_KEY, algorithm='HS256')
        return jsonify({'token': token, 'user_id': user.id, 'role': user.role})

    @app.route('/admin-logout')
    def admin_logout():
        session.clear()
        return redirect(url_for('home'))

    @app.route('/static/<path:path>')
    def send_static(path):
        return send_from_directory('static', path)

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
