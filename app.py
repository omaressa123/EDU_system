from flask import Flask, session, request, redirect, url_for, jsonify, send_from_directory
from models import db
from config import Config
from blueprints.auth import auth_bp
from blueprints.profile import profile_bp
from blueprints.search import search_bp
from blueprints.chat import chat_bp
from blueprints.application import application_bp
from blueprints.admin import admin_bp

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
            username = request.form.get('username')
            password = request.form.get('password')
            
            if username == 'admin' and password == 'admin123':
                session['admin_logged_in'] = True
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'message': 'Invalid username or password'})
        
        return send_from_directory('static', 'admin_login.html')

    @app.route('/dashboard')
    def dashboard():
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return send_from_directory('static', 'dashboard.html')

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
