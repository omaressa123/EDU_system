from flask import Blueprint, request, jsonify, g
from functools import wraps
import jwt
from datetime import datetime
from models import db, University, Faculty, Program, User
from config import Config

admin_bp = Blueprint('admin', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token missing'}), 401
        try:
            token = token.split(' ')[1]  # Bearer token
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            g.current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.current_user or g.current_user.role != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    return jsonify({
        'id': g.current_user.id,
        'name': g.current_user.name,
        'role': g.current_user.role
    })

@admin_bp.route('/universities', methods=['GET', 'POST'])
@token_required
@admin_required
def universities():
    if request.method == 'POST':
        data = request.json
        uni = University(
            name=data['name'],
            location=data['location'],
            type=data['type'],
            min_tuition_fees=data.get('min_tuition_fees'),
            max_tuition_fees=data.get('max_tuition_fees'),
            description=data.get('description'),
            city=data.get('city', data['location']),  # Use provided city or location
            country='Egypt'  # Default
        )
        db.session.add(uni)
        db.session.commit()
        return jsonify({'message': 'University added', 'id': uni.id}), 201

    unis = University.query.all()
    return jsonify([{
        'id': u.id,
        'name': u.name,
        'location': u.location,
        'type': u.type,
        'min_tuition_fees': u.min_tuition_fees,
        'max_tuition_fees': u.max_tuition_fees
    } for u in unis])

@admin_bp.route('/faculties', methods=['GET', 'POST'])
@token_required
@admin_required
def faculties():
    if request.method == 'POST':
        data = request.json
        fac = Faculty(
            uni_id=data['uni_id'],
            name=data['name'],
            fees=data.get('fees'),
            duration=data.get('duration')
        )
        db.session.add(fac)
        db.session.commit()
        return jsonify({'message': 'Faculty added', 'id': fac.id}), 201

    unis_id = request.args.get('uni_id')
    query = Faculty.query
    if unis_id:
        query = query.filter_by(uni_id=unis_id)
    facs = query.all()
    return jsonify([{
        'id': f.id,
        'uni_id': f.uni_id,
        'name': f.name,
        'fees': f.fees,
        'duration': f.duration
    } for f in facs])

@admin_bp.route('/programs', methods=['GET', 'POST'])
@token_required
@admin_required
def programs():
    if request.method == 'POST':
        data = request.json
        prog = Program(
            faculty_id=data['faculty_id'],
            name=data['name'],
            degree=data.get('degree'),
            duration_years=data.get('duration_years'),
            min_grade_required=data['min_grade_required'],
            language=data.get('language')
        )
        db.session.add(prog)
        db.session.commit()
        return jsonify({'message': 'Program added', 'id': prog.id}), 201

    fac_id = request.args.get('faculty_id')
    query = Program.query
    if fac_id:
        query = query.filter_by(faculty_id=fac_id)
    progs = query.all()
    return jsonify([{
        'id': p.id,
        'faculty_id': p.faculty_id,
        'name': p.name,
        'degree': p.degree,
        'min_grade_required': p.min_grade_required,
        'language': p.language
    } for p in progs])

# Full CRUD for Universities
@admin_bp.route('/universities/<int:id>', methods=['PUT', 'DELETE'])
@token_required
@admin_required
def university_crud(id):
    if request.method == 'PUT':
        uni = University.query.get_or_404(id)
        data = request.json
        uni.name = data.get('name', uni.name)
        uni.location = data.get('location', uni.location)
        uni.type = data.get('type', uni.type)
        uni.min_tuition_fees = data.get('min_tuition_fees', uni.min_tuition_fees)
        uni.max_tuition_fees = data.get('max_tuition_fees', uni.max_tuition_fees)
        uni.description = data.get('description', uni.description)
        uni.city = data.get('city', uni.city or data.get('location'))
        db.session.commit()
        return jsonify({'message': 'University updated successfully', 'university': {'id': uni.id, 'name': uni.name}})
    else:  # DELETE
        uni = University.query.get_or_404(id)
        db.session.delete(uni)
        db.session.commit()
        return jsonify({'message': 'University deleted successfully'})

# Full CRUD for Faculties
@admin_bp.route('/faculties/<int:id>', methods=['PUT', 'DELETE'])
@token_required
@admin_required
def faculty_crud(id):
    if request.method == 'PUT':
        fac = Faculty.query.get_or_404(id)
        data = request.json
        fac.name = data.get('name', fac.name)
        fac.fees = data.get('fees', fac.fees)
        fac.duration = data.get('duration', fac.duration)
        db.session.commit()
        return jsonify({'message': 'Faculty updated successfully', 'faculty': {'id': fac.id, 'name': fac.name}})
    else:
        fac = Faculty.query.get_or_404(id)
        db.session.delete(fac)
        db.session.commit()
        return jsonify({'message': 'Faculty deleted successfully'})

# Full CRUD for Programs
@admin_bp.route('/programs/<int:id>', methods=['PUT', 'DELETE'])
@token_required
@admin_required
def program_crud(id):
    if request.method == 'PUT':
        prog = Program.query.get_or_404(id)
        data = request.json
        prog.name = data.get('name', prog.name)
        prog.degree = data.get('degree', prog.degree)
        prog.duration_years = data.get('duration_years', prog.duration_years)
        prog.min_grade_required = data.get('min_grade_required', prog.min_grade_required)
        prog.language = data.get('language', prog.language)
        db.session.commit()
        return jsonify({'message': 'Program updated successfully', 'program': {'id': prog.id, 'name': prog.name}})
    else:
        prog = Program.query.get_or_404(id)
        db.session.delete(prog)
        db.session.commit()
    return jsonify({'message': 'Program deleted successfully'})

@admin_bp.route('/stats', methods=['GET'])
@token_required
@admin_required
def get_stats():
    from models import University, Faculty, Program, User, Application, ChatSession
    return jsonify({
        'total_users': User.query.count(),
        'total_universities': University.query.count(),
        'total_faculties': Faculty.query.count(),
        'total_programs': Program.query.count(),
        'total_applications': Application.query.count(),
        'total_chats': ChatSession.query.count(),
        'recent_activity': []  # Add later
    })

