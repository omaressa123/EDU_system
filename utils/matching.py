def match_universities(student, universities):
    """
    Auto-match logic based on student grades and university requirements.
    This is a simplified version of the algorithm.
    """
    matched = []
    student_profile = student.academic_profile
    if not student_profile:
        return []

    for uni in universities:
        # Check if the university accepts the student's curriculum
        if student.school_type not in uni.accepted_curriculums:
            continue

        # Check eligibility for each program
        eligible_programs = []
        for faculty in uni.faculties:
            for program in faculty.programs:
                # Get the student's relevant score based on school type
                score = 0
                if student.school_type == 'public':
                    score = student.national_exam_score
                elif student.school_type == 'american':
                    score = student.gpa * 25 # Convert GPA to 0-100 scale for comparison
                elif student.school_type == 'private':
                    score = student.ib_score * 2.5 # Convert IB to 0-100 scale

                if score >= program.min_grade_required:
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
