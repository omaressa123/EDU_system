def match_universities(student, universities):
    """
    Auto-match logic based on student grades and university requirements.
    This is a simplified version of the algorithm.
    """
    matched = []
    
    # Ensure we have the full student profile including subclass attributes
    # In case student was fetched as a generic Student object
    from models import PublicSchoolStudent, AmericanSchoolStudent, PrivateSchoolStudent
    
    if student.school_type == 'public':
        student = PublicSchoolStudent.query.get(student.id)
    elif student.school_type == 'american':
        student = AmericanSchoolStudent.query.get(student.id)
    elif student.school_type == 'private':
        student = PrivateSchoolStudent.query.get(student.id)

    student_profile = student.academic_profile if student else None
    if not student_profile:
        return []

    for uni in universities:
        # Check if the university accepts the student's curriculum
        accepted = uni.accepted_curriculums or []
        if student.school_type not in accepted:
            continue

        # Check eligibility for each program
        eligible_programs = []
        for faculty in uni.faculties:
            for program in faculty.programs:
                # Get the student's relevant score based on school type
                score = 0
                if student.school_type == 'public':
                    score = getattr(student, 'national_exam_score', 0) or 0
                elif student.school_type == 'american':
                    gpa = getattr(student, 'gpa', 0) or 0
                    score = gpa * 25 # Convert GPA to 0-100 scale for comparison
                elif student.school_type == 'private':
                    ib = getattr(student, 'ib_score', 0) or 0
                    score = ib * 2.5 # Convert IB to 0-100 scale

                min_grade = program.min_grade_required or 0
                if score >= min_grade:
                    eligible_programs.append({
                        'program_id': program.id,
                        'name': program.name,
                        'faculty': faculty.name,
                        'fees': faculty.fees,
                        'duration': program.duration_years
                    })

        if eligible_programs:
            matched.append({
                'uni_id': uni.id,
                'name': uni.name,
                'location': uni.location,
                'type': uni.type,
                'programs': eligible_programs
            })

    return matched
