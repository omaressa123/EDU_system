from flask import Blueprint, request, jsonify
from models import db, ChatSession, Message, Student, UniversityRep, FAQEntry
from datetime import datetime

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/start', methods=['POST'])
def start_chat():
    data = request.get_json()
    student_id = data.get('student_id')
    uni_id = data.get('uni_id')

    student = Student.query.get(student_id)
    if not student:
        return jsonify({'message': 'Student not found'}), 404

    # Create a new chat session
    new_session = ChatSession(student_id=student_id, uni_id=uni_id)
    db.session.add(new_session)
    db.session.commit()

    return jsonify({'chat_id': new_session.id, 'status': new_session.status})

@chat_bp.route('/message', methods=['POST'])
def send_message():
    data = request.get_json()
    chat_id = data.get('chat_id')
    sender_id = data.get('sender_id')
    content = data.get('content', '').lower()

    session = ChatSession.query.get(chat_id)
    if not session:
        return jsonify({'message': 'Chat session not found'}), 404

    # 1. Store the student's message
    new_message = Message(session_id=chat_id, sender_id=sender_id, content=content)
    db.session.add(new_message)

    # 2. Dynamic Info Retrieval (Private/Detailed info)
    bot_response = None
    uni = session.university

    # Logic to provide "private" or detailed information based on student's question
    if 'fee' in content or 'cost' in content or 'price' in content:
        bot_response = f"For {uni.name}, the tuition fees range from {uni.min_tuition_fees} to {uni.max_tuition_fees} EGP. Specific program fees are available on our programs page."
    elif 'where' in content or 'location' in content or 'campus' in content or 'city' in content:
        bot_response = f"The campus for {uni.name} is located in {uni.location}, {uni.city}, {uni.country}. You can also visit our website: {uni.website}"
    elif 'program' in content or 'major' in content or 'course' in content:
        programs_list = []
        for faculty in uni.faculties:
            for program in faculty.programs:
                programs_list.append(program.name)
        bot_response = f"{uni.name} offers various programs including: {', '.join(programs_list[:5])}... and more!"
    elif 'admission' in content or 'requirement' in content or 'score' in content or 'grade' in content:
        reqs = []
        for req in uni.requirements:
            reqs.append(f"{req.school_type.capitalize()}: {req.min_score}%")
        bot_response = f"Admission requirements for {uni.name} are as follows: {', '.join(reqs)}. You'll also need: {', '.join(uni.requirements[0].required_docs if uni.requirements else [])}."
    elif 'scholarship' in content or 'financial aid' in content:
        bot_response = f"Regarding scholarships at {uni.name}: {uni.scholarships}"
    elif 'facility' in content or 'library' in content or 'sports' in content or 'lab' in content:
        bot_response = f"The facilities at {uni.name} include: {uni.facilities}"
    elif 'contact' in content or 'email' in content or 'phone' in content:
        bot_response = f"You can contact {uni.name} at Email: {uni.contact_email} or Phone: {uni.contact_phone}"
    elif 'accreditation' in content or 'accredited' in content:
        bot_response = f"Accreditation for {uni.name}: {uni.accreditation}"
    elif 'housing' in content or 'dorm' in content or 'hostel' in content:
        bot_response = f"About housing at {uni.name}: {uni.housing}"
    elif 'founded' in content or 'established' in content or 'when' in content:
        if uni.founded_year:
            bot_response = f"{uni.name} was founded in {uni.founded_year}."
        else:
            bot_response = f"I don't have the exact founding year for {uni.name}, but you can check their website: {uni.website}"
    
    # 3. Fallback to FAQ table if no dynamic match
    if not bot_response:
        faq_answer = FAQEntry.query.filter(
            FAQEntry.uni_id == session.uni_id,
            FAQEntry.question.ilike(f'%{content}%')
        ).first()
        if faq_answer:
            bot_response = faq_answer.answer

    # 4. If still no response, provide a default with university link
    if not bot_response:
        bot_response = f"Thank you for your question. For more detailed information that I might not have yet, please visit the official {uni.name} website: <a href='{uni.website}' target='_blank'>{uni.website}</a>. A university representative will also be with you shortly."

    # 5. Store and return bot message
    faq_response = Message(
        session_id=chat_id, 
        sender_id=None, # System/Bot
        content=bot_response,
        type='faq_bot'
    )
    db.session.add(faq_response)
    db.session.commit()

    return jsonify({
        'message': 'Message sent', 
        'bot_response': bot_response
    })

@chat_bp.route('/history/<int:chat_id>', methods=['GET'])
def get_chat_history(chat_id):
    session = ChatSession.query.get(chat_id)
    if not session:
        return jsonify({'message': 'Chat session not found'}), 404

    messages = []
    for msg in session.messages:
        messages.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'content': msg.content,
            'sent_at': msg.sent_at,
            'is_read': msg.is_read
        })

    return jsonify(messages)
