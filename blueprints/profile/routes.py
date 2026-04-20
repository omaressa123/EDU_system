from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for, session
from models import db, Student, PublicSchoolStudent, AmericanSchoolStudent, PrivateSchoolStudent, AcademicProfile, Document, Admin, University, User
from datetime import datetime

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get('admin_logged_in'):
        return redirect('/admin-login')
    
    from models import User, University
    admin_user = User.query.filter_by(role='admin').first()  # Simple admin lookup
    
    if request.method == 'POST':
        admin_user.name = request.form['name']
        admin_user.email = request.form['email']
        admin_user.phone = request.form.get('phone', '')
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect('/api/profile/profile')
    
    total_users = User.query.count()
    total_unis = University.query.count()
    
    return render_template('profile.html', current_user=admin_user, total_users=total_users, total_unis=total_unis)


@profile_bp.route('/results', methods=['POST'])
def enter_results():
    data = request.get_json()
    student_id = data.get('student_id')
    school_type = data.get('school_type')
    grades = data.get('grades')

    student = Student.query.get(student_id)
    if not student:
        return jsonify({'message': 'Student not found'}), 404

    profile = student.academic_profile
    if not profile:
        profile = AcademicProfile(student_id=student_id, school_type=school_type, grades=grades)
        db.session.add(profile)
    else:
        profile.grades = grades
        profile.school_type = school_type
        profile.last_updated = datetime.utcnow()

    # Update specific student type data
    if school_type == 'public':
        public_student = PublicSchoolStudent.query.get(student_id)
        public_student.national_exam_score = data.get('national_exam_score')
        public_student.exam_year = data.get('exam_year')
        public_student.track = data.get('track')
    elif school_type == 'american':
        american_student = AmericanSchoolStudent.query.get(student_id)
        american_student.sat_score = data.get('sat_score')
        american_student.act_score = data.get('act_score')
        american_student.gpa = data.get('gpa')
        american_student.toefl_score = data.get('toefl_score')
    elif school_type == 'private':
        private_student = PrivateSchoolStudent.query.get(student_id)
        private_student.curriculum = data.get('curriculum')
        private_student.ib_score = data.get('ib_score')
        private_student.igcse_grades = data.get('igcse_grades')
        private_student.a_level_grades = data.get('a_level_grades')

    db.session.commit()
    return jsonify({'message': 'Academic results updated successfully'})

@profile_bp.route('/upload-document', methods=['POST'])
def upload_document():
    # In a real app, you would handle file uploads and save to S3 or a local folder.
    # Here we'll just mock it.
    data = request.get_json()
    student_id = data.get('student_id')
    doc_type = data.get('type')
    file_path = data.get('file_path')

    student = Student.query.get(student_id)
    if not student or not student.academic_profile:
        return jsonify({'message': 'Academic profile not found'}), 404

    new_doc = Document(profile_id=student.academic_profile.id, type=doc_type, file_path=file_path)
    db.session.add(new_doc)
    db.session.commit()

    return jsonify({'message': 'Document uploaded successfully', 'doc_id': new_doc.id})
