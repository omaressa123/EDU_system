from flask import Blueprint, request, jsonify
from models import University, Student, Program, Faculty, AdmissionRequirement
from utils.matching import match_universities

search_bp = Blueprint('search', __name__)

@search_bp.route('/universities', methods=['GET'])
def list_universities():
    location = request.args.get('location')
    uni_type = request.args.get('type') # 'public', 'private'
    fees_max = request.args.get('fees_max', type=float)
    program_name = request.args.get('program')

    query = University.query
    if location:
        query = query.filter(University.location.ilike(f'%{location}%'))
    if uni_type:
        query = query.filter(University.type == uni_type)
    if fees_max:
        query = query.filter(University.min_tuition_fees <= fees_max)
    if program_name:
        query = query.join(Faculty).join(Program).filter(Program.name.ilike(f'%{program_name}%'))

    universities = query.all()
    results = []
    for uni in universities:
        results.append({
            'id': uni.id,
            'name': uni.name,
            'location': uni.location,
            'city': uni.city,
            'fees': f'{uni.min_tuition_fees} - {uni.max_tuition_fees}',
            'website': uni.website
        })

    return jsonify(results)

@search_bp.route('/match', methods=['POST'])
def auto_match():
    data = request.get_json()
    student_id = data.get('student_id')
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'message': 'Student not found'}), 404

    universities = University.query.all()
    matched = match_universities(student, universities)
    return jsonify(matched)

@search_bp.route('/university/<int:uni_id>', methods=['GET'])
def university_details(uni_id):
    uni = University.query.get(uni_id)
    if not uni:
        return jsonify({'message': 'University not found'}), 404

    faculties_data = []
    for faculty in uni.faculties:
        programs_data = []
        for program in faculty.programs:
            programs_data.append({
                'id': program.id,
                'name': program.name,
                'degree': program.degree,
                'duration': program.duration_years,
                'min_grade': program.min_grade_required,
                'language': program.language
            })
        faculties_data.append({
            'id': faculty.id,
            'name': faculty.name,
            'fees': faculty.fees,
            'duration': faculty.duration,
            'programs': programs_data
        })

    return jsonify({
        'id': uni.id,
        'name': uni.name,
        'location': uni.location,
        'description': uni.description,
        'faculties': faculties_data
    })
