from flask import Blueprint, request, jsonify, g
from functools import wraps
import jwt
from models import db, University, Faculty, Program, User
from config import Config
from sqlalchemy import or_

admin_bp = Blueprint('admin', __name__)

DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 10
MAX_PER_PAGE = 100

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
        except Exception:
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


def _to_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _pagination_params():
    page = _to_int(request.args.get('page'), DEFAULT_PAGE)
    per_page = _to_int(request.args.get('per_page'), DEFAULT_PER_PAGE)
    page = page if page and page > 0 else DEFAULT_PAGE
    per_page = per_page if per_page and per_page > 0 else DEFAULT_PER_PAGE
    per_page = min(per_page, MAX_PER_PAGE)
    return page, per_page


def _paging_payload(items, page_obj):
    return {
        'items': items,
        'meta': {
            'page': page_obj.page,
            'per_page': page_obj.per_page,
            'total': page_obj.total,
            'pages': page_obj.pages,
            'has_next': page_obj.has_next,
            'has_prev': page_obj.has_prev
        }
    }


def _list_response(query, serializer):
    page, per_page = _pagination_params()
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(_paging_payload([serializer(item) for item in paginated.items], paginated))


def _validate_payload(required_fields):
    payload = request.get_json(silent=True) or {}
    missing = [field for field in required_fields if payload.get(field) in (None, "")]
    if missing:
        return None, (jsonify({'message': f"Missing required fields: {', '.join(missing)}"}), 400)
    return payload, None

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
        data, error = _validate_payload(['name', 'location', 'type'])
        if error:
            return error
        uni = University(
            name=data['name'],
            location=data['location'],
            type=data['type'],
            min_tuition_fees=_to_float(data.get('min_tuition_fees')),
            max_tuition_fees=_to_float(data.get('max_tuition_fees')),
            description=data.get('description'),
            city=data.get('city', data['location']),
            country='Egypt'
        )
        db.session.add(uni)
        db.session.commit()
        return jsonify({'message': 'University added', 'id': uni.id}), 201

    query = University.query
    search = (request.args.get('search') or '').strip()
    uni_type = (request.args.get('type') or '').strip()
    sort_by = request.args.get('sort_by', 'name')
    sort_dir = request.args.get('sort_dir', 'asc').lower()

    if search:
        wildcard = f"%{search}%"
        query = query.filter(or_(University.name.ilike(wildcard), University.location.ilike(wildcard)))

    if uni_type:
        query = query.filter(University.type == uni_type)

    sort_map = {
        'name': University.name,
        'location': University.location,
        'type': University.type,
        'id': University.id
    }
    sort_col = sort_map.get(sort_by, University.name)
    query = query.order_by(sort_col.desc() if sort_dir == 'desc' else sort_col.asc())

    return _list_response(query, lambda u: {
        'id': u.id,
        'name': u.name,
        'location': u.location,
        'type': u.type,
        'min_tuition_fees': u.min_tuition_fees,
        'max_tuition_fees': u.max_tuition_fees,
        'description': u.description
    })

@admin_bp.route('/faculties', methods=['GET', 'POST'])
@token_required
@admin_required
def faculties():
    if request.method == 'POST':
        data, error = _validate_payload(['uni_id', 'name'])
        if error:
            return error
        fac = Faculty(
            uni_id=_to_int(data['uni_id']),
            name=data['name'],
            fees=_to_float(data.get('fees')),
            duration=data.get('duration')
        )
        if not fac.uni_id:
            return jsonify({'message': 'Invalid university id'}), 400
        db.session.add(fac)
        db.session.commit()
        return jsonify({'message': 'Faculty added', 'id': fac.id}), 201

    unis_id = _to_int(request.args.get('uni_id'))
    search = (request.args.get('search') or '').strip()
    sort_by = request.args.get('sort_by', 'name')
    sort_dir = request.args.get('sort_dir', 'asc').lower()
    query = Faculty.query
    if unis_id:
        query = query.filter_by(uni_id=unis_id)
    if search:
        wildcard = f"%{search}%"
        query = query.filter(Faculty.name.ilike(wildcard))
    sort_map = {'id': Faculty.id, 'name': Faculty.name, 'fees': Faculty.fees, 'uni_id': Faculty.uni_id}
    sort_col = sort_map.get(sort_by, Faculty.name)
    query = query.order_by(sort_col.desc() if sort_dir == 'desc' else sort_col.asc())

    return _list_response(query, lambda f: {
        'id': f.id,
        'uni_id': f.uni_id,
        'name': f.name,
        'fees': f.fees,
        'duration': f.duration
    })

@admin_bp.route('/programs', methods=['GET', 'POST'])
@token_required
@admin_required
def programs():
    if request.method == 'POST':
        data, error = _validate_payload(['faculty_id', 'name', 'min_grade_required'])
        if error:
            return error
        prog = Program(
            faculty_id=_to_int(data['faculty_id']),
            name=data['name'],
            degree=data.get('degree'),
            duration_years=_to_int(data.get('duration_years')),
            min_grade_required=_to_float(data['min_grade_required']),
            language=data.get('language')
        )
        if not prog.faculty_id:
            return jsonify({'message': 'Invalid faculty id'}), 400
        db.session.add(prog)
        db.session.commit()
        return jsonify({'message': 'Program added', 'id': prog.id}), 201

    fac_id = _to_int(request.args.get('faculty_id'))
    search = (request.args.get('search') or '').strip()
    sort_by = request.args.get('sort_by', 'name')
    sort_dir = request.args.get('sort_dir', 'asc').lower()
    query = Program.query
    if fac_id:
        query = query.filter_by(faculty_id=fac_id)
    if search:
        wildcard = f"%{search}%"
        query = query.filter(or_(Program.name.ilike(wildcard), Program.degree.ilike(wildcard)))
    sort_map = {
        'id': Program.id,
        'name': Program.name,
        'degree': Program.degree,
        'min_grade_required': Program.min_grade_required,
        'faculty_id': Program.faculty_id
    }
    sort_col = sort_map.get(sort_by, Program.name)
    query = query.order_by(sort_col.desc() if sort_dir == 'desc' else sort_col.asc())

    return _list_response(query, lambda p: {
        'id': p.id,
        'faculty_id': p.faculty_id,
        'name': p.name,
        'degree': p.degree,
        'duration_years': p.duration_years,
        'min_grade_required': p.min_grade_required,
        'language': p.language
    })

# Full CRUD for Universities
@admin_bp.route('/universities/<int:id>', methods=['PUT', 'DELETE'])
@token_required
@admin_required
def university_crud(id):
    if request.method == 'PUT':
        uni = University.query.get_or_404(id)
        data = request.get_json(silent=True) or {}
        uni.name = data.get('name', uni.name)
        uni.location = data.get('location', uni.location)
        uni.type = data.get('type', uni.type)
        uni.min_tuition_fees = _to_float(data.get('min_tuition_fees'), uni.min_tuition_fees)
        uni.max_tuition_fees = _to_float(data.get('max_tuition_fees'), uni.max_tuition_fees)
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
        data = request.get_json(silent=True) or {}
        uni_id = _to_int(data.get('uni_id'))
        if uni_id:
            fac.uni_id = uni_id
        fac.name = data.get('name', fac.name)
        fac.fees = _to_float(data.get('fees'), fac.fees)
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
        data = request.get_json(silent=True) or {}
        faculty_id = _to_int(data.get('faculty_id'))
        if faculty_id:
            prog.faculty_id = faculty_id
        prog.name = data.get('name', prog.name)
        prog.degree = data.get('degree', prog.degree)
        prog.duration_years = _to_int(data.get('duration_years'), prog.duration_years)
        prog.min_grade_required = _to_float(data.get('min_grade_required'), prog.min_grade_required)
        prog.language = data.get('language', prog.language)
        db.session.commit()
        return jsonify({'message': 'Program updated successfully', 'program': {'id': prog.id, 'name': prog.name}})
    else:
        prog = Program.query.get_or_404(id)
        db.session.delete(prog)
        db.session.commit()
    return jsonify({'message': 'Program deleted successfully'})


@admin_bp.route('/universities/bulk-delete', methods=['POST'])
@token_required
@admin_required
def universities_bulk_delete():
    data = request.get_json(silent=True) or {}
    ids = data.get('ids', [])
    if not isinstance(ids, list) or not ids:
        return jsonify({'message': 'Provide a non-empty ids list'}), 400
    deleted = University.query.filter(University.id.in_(ids)).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({'message': f'{deleted} universities deleted', 'deleted': deleted})


@admin_bp.route('/faculties/bulk-delete', methods=['POST'])
@token_required
@admin_required
def faculties_bulk_delete():
    data = request.get_json(silent=True) or {}
    ids = data.get('ids', [])
    if not isinstance(ids, list) or not ids:
        return jsonify({'message': 'Provide a non-empty ids list'}), 400
    deleted = Faculty.query.filter(Faculty.id.in_(ids)).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({'message': f'{deleted} faculties deleted', 'deleted': deleted})


@admin_bp.route('/programs/bulk-delete', methods=['POST'])
@token_required
@admin_required
def programs_bulk_delete():
    data = request.get_json(silent=True) or {}
    ids = data.get('ids', [])
    if not isinstance(ids, list) or not ids:
        return jsonify({'message': 'Provide a non-empty ids list'}), 400
    deleted = Program.query.filter(Program.id.in_(ids)).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({'message': f'{deleted} programs deleted', 'deleted': deleted})

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

