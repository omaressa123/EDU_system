from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ── User Hierarchy ────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False) # 'student', 'rep', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Polymorphism setup
    type = db.Column(db.String(50))
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': type
    }

class Student(User):
    __tablename__ = 'students'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    school_type = db.Column(db.String(20)) # 'public', 'american', 'private'
    national_id = db.Column(db.String(20), unique=True)
    birth_date = db.Column(db.Date)
    governorate = db.Column(db.String(50))
    
    # Relationships
    academic_profile = db.relationship('AcademicProfile', backref='student', uselist=False)
    applications = db.relationship('Application', backref='student')
    chat_sessions = db.relationship('ChatSession', backref='student')

    __mapper_args__ = {
        'polymorphic_identity': 'student',
    }

class PublicSchoolStudent(Student):
    __tablename__ = 'public_students'
    id = db.Column(db.Integer, db.ForeignKey('students.id'), primary_key=True)
    national_exam_score = db.Column(db.Float)
    exam_year = db.Column(db.String(4))
    track = db.Column(db.String(50)) # 'science', 'arts'
    
    __mapper_args__ = {
        'polymorphic_identity': 'public_student',
    }

class AmericanSchoolStudent(Student):
    __tablename__ = 'american_students'
    id = db.Column(db.Integer, db.ForeignKey('students.id'), primary_key=True)
    sat_score = db.Column(db.Integer)
    act_score = db.Column(db.Integer)
    gpa = db.Column(db.Float)
    toefl_score = db.Column(db.Integer)
    
    __mapper_args__ = {
        'polymorphic_identity': 'american_student',
    }

class PrivateSchoolStudent(Student):
    __tablename__ = 'private_students'
    id = db.Column(db.Integer, db.ForeignKey('students.id'), primary_key=True)
    curriculum = db.Column(db.String(50)) # 'IB', 'IGCSE', 'A-Level'
    ib_score = db.Column(db.Float)
    igcse_grades = db.Column(db.String(100))
    a_level_grades = db.Column(db.String(100))
    
    __mapper_args__ = {
        'polymorphic_identity': 'private_student',
    }

class UniversityRep(User):
    __tablename__ = 'university_reps'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    uni_id = db.Column(db.Integer, db.ForeignKey('universities.id'))
    position = db.Column(db.String(100))
    
    __mapper_args__ = {
        'polymorphic_identity': 'rep',
    }

class Admin(User):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    
    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }

# ── Academic Profile ──────────────────────────────────

class AcademicProfile(db.Model):
    __tablename__ = 'academic_profiles'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    school_type = db.Column(db.String(20))
    grades = db.Column(db.JSON) # Store subject-grade pairs
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    documents = db.relationship('Document', backref='profile')

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('academic_profiles.id'))
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=True)
    type = db.Column(db.String(50)) # 'transcript', 'id', 'certificate'
    file_path = db.Column(db.String(255))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending') # 'pending', 'verified', 'rejected'

# ── University ────────────────────────────────────────

class University(db.Model):
    __tablename__ = 'universities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50)) # 'public', 'private'
    location = db.Column(db.String(255))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    website = db.Column(db.String(255))
    min_tuition_fees = db.Column(db.Float)
    max_tuition_fees = db.Column(db.Float)
    description = db.Column(db.Text)
    accepted_curriculums = db.Column(db.JSON) # List of accepted school types
    
    # New Fields for enriched information
    scholarships = db.Column(db.Text)
    facilities = db.Column(db.Text)
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    accreditation = db.Column(db.Text)
    housing = db.Column(db.Text)
    founded_year = db.Column(db.Integer)

    faculties = db.relationship('Faculty', backref='university')
    requirements = db.relationship('AdmissionRequirement', backref='university')
    reps = db.relationship('UniversityRep', backref='university')

class Faculty(db.Model):
    __tablename__ = 'faculties'
    id = db.Column(db.Integer, primary_key=True)
    uni_id = db.Column(db.Integer, db.ForeignKey('universities.id'))
    name = db.Column(db.String(255), nullable=False)
    fees = db.Column(db.Float)
    duration = db.Column(db.String(50))
    
    programs = db.relationship('Program', backref='faculty')

class Program(db.Model):
    __tablename__ = 'programs'
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculties.id'))
    name = db.Column(db.String(255), nullable=False)
    degree = db.Column(db.String(50)) # 'BSc', 'BA', etc.
    duration_years = db.Column(db.Integer)
    min_grade_required = db.Column(db.Float)
    language = db.Column(db.String(50))

class AdmissionRequirement(db.Model):
    __tablename__ = 'admission_requirements'
    id = db.Column(db.Integer, primary_key=True)
    uni_id = db.Column(db.Integer, db.ForeignKey('universities.id'))
    school_type = db.Column(db.String(20))
    min_score = db.Column(db.Float)
    required_docs = db.Column(db.JSON) # List of required document types
    additional_criteria = db.Column(db.Text)

# ── Chat System ───────────────────────────────────────

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    uni_rep_id = db.Column(db.Integer, db.ForeignKey('university_reps.id'), nullable=True)
    uni_id = db.Column(db.Integer, db.ForeignKey('universities.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active') # 'active', 'closed'
    
    university = db.relationship('University', backref='chat_sessions')
    messages = db.relationship('Message', backref='session')

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='text') # 'text', 'file'
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class FAQEntry(db.Model):
    __tablename__ = 'faq_entries'
    id = db.Column(db.Integer, primary_key=True)
    uni_id = db.Column(db.Integer, db.ForeignKey('universities.id'))
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))

# ── Application ───────────────────────────────────────

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    uni_id = db.Column(db.Integer, db.ForeignKey('universities.id'))
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='draft') # 'draft', 'submitted', 'under_review', 'accepted', 'rejected'
    notes = db.Column(db.Text)
    
    attached_docs = db.relationship('Document', backref='application')
