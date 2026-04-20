from flask import Blueprint, request, jsonify
from models import db, Application, Student, University, Program, Document
from datetime import datetime

application_bp = Blueprint('application', __name__)

@application_bp.route('/submit', methods=['POST'])
def submit_application():
    data = request.get_json()
    student_id = data.get('student_id')
    uni_id = data.get('uni_id')
    program_id = data.get('program_id')
    notes = data.get('notes')

    student = Student.query.get(student_id)
    if not student:
        return jsonify({'message': 'Student not found'}), 404

    # Create new application
    new_app = Application(
        student_id=student_id, 
        uni_id=uni_id, 
        program_id=program_id, 
        status='submitted',
        notes=notes
    )
    db.session.add(new_app)
    
    # Associate documents from academic profile to this application
    if student.academic_profile:
        for doc in student.academic_profile.documents:
            doc.application_id = new_app.id
    
    db.session.commit()

    return jsonify({'app_id': new_app.id, 'status': new_app.status, 'message': 'Application submitted successfully'})

@application_bp.route('/status/<int:student_id>', methods=['GET'])
def check_status(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'message': 'Student not found'}), 404

    apps_data = []
    for app in student.applications:
        apps_data.append({
            'id': app.id,
            'uni_name': University.query.get(app.uni_id).name,
            'program_name': Program.query.get(app.program_id).name,
            'submitted_at': app.submitted_at,
            'status': app.status
        })

    return jsonify(apps_data)

@application_bp.route('/update-status', methods=['POST'])
def update_status():
    data = request.get_json()
    app_id = data.get('app_id')
    new_status = data.get('status') # 'under_review', 'accepted', 'rejected'
    notes = data.get('notes')

    application = Application.query.get(app_id)
    if not application:
        return jsonify({'message': 'Application not found'}), 404

    application.status = new_status
    if notes:
        application.notes = notes
    
    db.session.commit()

    return jsonify({'message': 'Application status updated successfully'})
