from flask import Blueprint, request, jsonify
from models import db, User, Student, PublicSchoolStudent, AmericanSchoolStudent, PrivateSchoolStudent
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'student')
    school_type = data.get('school_type')

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'User already exists'}), 400

    password_hash = generate_password_hash(password)
    
    if role == 'student':
        if school_type == 'public':
            new_user = PublicSchoolStudent(name=name, email=email, password_hash=password_hash, role=role, school_type=school_type)
        elif school_type == 'american':
            new_user = AmericanSchoolStudent(name=name, email=email, password_hash=password_hash, role=role, school_type=school_type)
        elif school_type == 'private':
            new_user = PrivateSchoolStudent(name=name, email=email, password_hash=password_hash, role=role, school_type=school_type)
        else:
            new_user = Student(name=name, email=email, password_hash=password_hash, role=role, school_type=school_type)
    else:
        new_user = User(name=name, email=email, password_hash=password_hash, role=role)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'message': 'Invalid credentials'}), 401

    token = jwt.encode({
        'user_id': user.id,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, Config.SECRET_KEY, algorithm='HS256')

    response_data = {
        'token': token,
        'user_id': user.id,
        'role': user.role
    }

    if user.role == 'student' and hasattr(user, 'school_type'):
        response_data['school_type'] = user.school_type

    return jsonify(response_data)
