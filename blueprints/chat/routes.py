from flask import Blueprint, request, jsonify
from models import db, ChatSession, Message, Student, FAQEntry
import os
import json
import re
from urllib import request as urllib_request, error as urllib_error
from difflib import SequenceMatcher

chat_bp = Blueprint('chat', __name__)

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


INTENT_KEYWORDS = {
    'fees': {'fee', 'fees', 'cost', 'price', 'tuition'},
    'location': {'where', 'location', 'campus', 'city', 'address'},
    'programs': {'program', 'programs', 'major', 'majors', 'course', 'courses', 'faculty', 'faculties'},
    'admission': {'admission', 'requirement', 'requirements', 'score', 'grade', 'grades', 'eligible', 'eligibility'},
    'scholarships': {'scholarship', 'scholarships', 'aid', 'financial'},
    'facilities': {'facility', 'facilities', 'library', 'sports', 'lab', 'labs'},
    'contact': {'contact', 'email', 'phone', 'call'},
    'accreditation': {'accreditation', 'accredited'},
    'housing': {'housing', 'dorm', 'hostel', 'accommodation'},
    'founded': {'founded', 'established', 'history'}
}

PROMPT_LIBRARY = {
    'intro': [
        "Thank you for your question. Based on our latest verified records for {uni_name}:",
        "Great question. Here is a concise brief from the current database for {uni_name}:",
        "Here is what I can confirm from our institutional data for {uni_name}:",
        "I reviewed the current records and found the following for {uni_name}:",
        "From the latest available university profile, here is a structured answer for {uni_name}:",
        "Below is a professional summary from our database records for {uni_name}:"
    ],
    'closing': [
        "If you want, I can now tailor this into a student-specific recommendation path.",
        "I can also prepare a side-by-side comparison with other universities if that helps your decision.",
        "If useful, I can convert this into an application checklist for your next step.",
        "I can continue with a focused answer for one program, faculty, or budget range.",
        "For official confirmation, always verify from {website}; I can still guide your shortlist here.",
        "If you share your school track and target major, I can return a more personalized answer."
    ],
    'fees': [
        "Tuition range: {min_fee} to {max_fee}, depending on program and faculty.",
        "Estimated tuition in our records falls between {min_fee} and {max_fee}.",
        "Current fee bracket is {min_fee} - {max_fee}; final cost varies by specialization.",
        "Financial range available in the database: {min_fee} to {max_fee}."
    ],
    'location': [
        "Campus location: {location}, {city}, {country}.",
        "Main campus is listed at {location}, {city}, {country}.",
        "Geographic location in our records: {location}, {city}, {country}.",
        "The university is currently mapped to {location}, {city}, {country}."
    ],
    'programs': [
        "Popular programs in our records include: {programs}.",
        "Program options currently available include: {programs}.",
        "Key academic tracks listed in the database: {programs}.",
        "Representative programs from available data: {programs}."
    ],
    'admission': [
        "Admission minimums by curriculum: {requirements}.",
        "Eligibility thresholds in current records: {requirements}.",
        "Recorded minimum scores by school system: {requirements}.",
        "Admission criteria snapshot: {requirements}."
    ],
    'documents': [
        "Common required documents: {documents}.",
        "Frequently requested documents include: {documents}.",
        "The standard document package usually includes: {documents}."
    ],
    'scholarships': [
        "Scholarships and financial aid details: {value}.",
        "Funding opportunities listed in our records: {value}.",
        "Available scholarship information: {value}."
    ],
    'facilities': [
        "Facilities profile: {value}.",
        "Campus resources and facilities: {value}.",
        "Learning environment and facilities include: {value}."
    ],
    'contact': [
        "Contact channels: email {email}, phone {phone}.",
        "Official contact points in the system: {email} | {phone}.",
        "You can reach the university via {email} or {phone}."
    ],
    'accreditation': [
        "Accreditation details: {value}.",
        "Quality and accreditation note: {value}.",
        "Accreditation record in database: {value}."
    ],
    'housing': [
        "Housing and accommodation summary: {value}.",
        "Residential options listed: {value}.",
        "Student housing details currently available: {value}."
    ],
    'founded': [
        "{uni_name} was founded in {year}.",
        "Founding year on record: {year}.",
        "Institution establishment year: {year}."
    ],
    'faq': [
        "Related FAQ insight: {answer}",
        "Closest FAQ answer from the knowledge base: {answer}",
        "Matched institutional FAQ response: {answer}"
    ],
    'fallback_intent': [
        "I understand your question about {intent}. The current record is limited for this specific point in {uni_name}.",
        "Your question is valid. We have partial data for {intent} at {uni_name}, but not enough for a precise answer.",
        "At the moment, the structured database has limited coverage for {intent} in {uni_name}."
    ],
    'fallback_general': [
        "I could not find a precise database match for this request yet.",
        "I currently do not have a direct structured answer in the available records.",
        "This question does not map clearly to the current indexed fields."
    ],
    'clarify': [
        "If you rephrase by topic (fees, programs, admission, location, housing), I can answer more accurately.",
        "Try a focused question such as: tuition range, required score, available majors, or campus location.",
        "For best results, ask one specific item at a time (for example: required score for your curriculum)."
    ]
}


def _normalize(text):
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', (text or '').lower())
    return re.sub(r'\s+', ' ', cleaned).strip()


def _tokens(text):
    return set(_normalize(text).split())


def _pick_template(group, content_seed, **kwargs):
    options = PROMPT_LIBRARY.get(group, [])
    if not options:
        return ""
    idx = sum(ord(c) for c in (content_seed or group)) % len(options)
    return options[idx].format(**kwargs)


def _best_faq_answer(uni_id, question):
    faqs = FAQEntry.query.filter(FAQEntry.uni_id == uni_id).all()
    if not faqs:
        return None

    q_norm = _normalize(question)
    q_tokens = _tokens(question)
    best_score = 0.0
    best_answer = None

    for faq in faqs:
        faq_q = faq.question or ''
        ratio = SequenceMatcher(None, q_norm, _normalize(faq_q)).ratio()
        overlap = 0.0
        faq_tokens = _tokens(faq_q)
        if q_tokens and faq_tokens:
            overlap = len(q_tokens & faq_tokens) / len(q_tokens)
        score = (0.65 * ratio) + (0.35 * overlap)
        if score > best_score:
            best_score = score
            best_answer = faq.answer

    return (best_answer, best_score) if best_score >= 0.42 else (None, 0.0)


def _detect_intents(content):
    tokens = _tokens(content)
    detected = set()
    for intent, keywords in INTENT_KEYWORDS.items():
        if tokens & keywords:
            detected.add(intent)
    return detected


def _format_currency(value):
    if value is None:
        return "N/A"
    return f"{value:,.0f} EGP"


def _format_intro(uni_name):
    return _pick_template('intro', uni_name, uni_name=uni_name)


def _format_closing(uni, content_seed):
    return _pick_template('closing', content_seed, website=(uni.website or "the official university website"))


def _format_bullets(lines):
    if not lines:
        return ""
    return "\n".join([f"- {line}" for line in lines])


def _get_gemini_api_key():
    # Support both GEMINI_API_KEY and GOOGLE_API_KEY and strip accidental quotes.
    raw_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not raw_key:
        return None
    return raw_key.strip().strip('"').strip("'")


def _call_gemini(user_question):
    api_key = _get_gemini_api_key()
    if not api_key:
        return None

    model_name = os.getenv("GEMINI_MODEL", GEMINI_MODEL).strip().strip('"').strip("'")
    gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

    prompt = (
        "You are EDU System's AI admissions assistant.\n"
        "Answer the student directly in a professional, clear, and helpful tone.\n"
        "Use concise structure, practical guidance, and actionable next steps.\n"
        "If the question is broad, ask one focused follow-up question.\n"
        "Do not mention internal system details.\n\n"
        f"Student question: {user_question}\n\n"
        "Return only the final response text."
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.35,
            "topP": 0.9,
            "maxOutputTokens": 320
        }
    }

    req = urllib_request.Request(
        f"{gemini_api_url}?key={api_key}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    # Retry transient failures once to reduce "service unavailable" responses.
    for _ in range(2):
        try:
            with urllib_request.urlopen(req, timeout=15) as response:
                raw = response.read().decode("utf-8")
                result = json.loads(raw)
                candidates = result.get("candidates", [])
                if not candidates:
                    return None
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    return None
                text = (parts[0].get("text") or "").strip()
                return text or None
        except urllib_error.HTTPError as e:
            # Retry only transient/provider-side failures.
            if e.code in (429, 500, 502, 503, 504):
                continue
            return None
        except (urllib_error.URLError, json.JSONDecodeError, TimeoutError):
            continue
    return None


def _generate_smart_response(user_question):
    return _call_gemini(user_question)


def _build_db_response(session, content):
    uni = session.university
    intents = _detect_intents(content)
    responses = []
    fallback_priority = []

    if 'fees' in intents:
        responses.append(_pick_template(
            'fees',
            content,
            min_fee=_format_currency(uni.min_tuition_fees),
            max_fee=_format_currency(uni.max_tuition_fees)
        ))
        fallback_priority.append('fees')

    if 'location' in intents:
        responses.append(_pick_template(
            'location',
            content,
            location=uni.location or 'N/A',
            city=uni.city or 'N/A',
            country=uni.country or 'N/A'
        ))
        fallback_priority.append('location')

    if 'programs' in intents:
        programs_list = []
        for faculty in uni.faculties:
            for program in faculty.programs:
                programs_list.append(program.name)
        if programs_list:
            preview = ', '.join(programs_list[:7])
            responses.append(_pick_template('programs', content, programs=preview))
        else:
            responses.append("Program-level records are currently limited for this university.")
        fallback_priority.append('programs')

    if 'admission' in intents:
        reqs = [f"{req.school_type}: {req.min_score}%" for req in uni.requirements]
        docs = uni.requirements[0].required_docs if uni.requirements and uni.requirements[0].required_docs else []
        if reqs:
            resp = _pick_template('admission', content, requirements=', '.join(reqs))
            if docs:
                resp += " " + _pick_template('documents', content, documents=', '.join(docs))
            responses.append(resp)
        else:
            responses.append("Admission requirement records are not fully populated yet for this university.")
        fallback_priority.append('admission')

    if 'scholarships' in intents and uni.scholarships:
        responses.append(_pick_template('scholarships', content, value=uni.scholarships))
        fallback_priority.append('scholarships')

    if 'facilities' in intents and uni.facilities:
        responses.append(_pick_template('facilities', content, value=uni.facilities))
        fallback_priority.append('facilities')

    if 'contact' in intents:
        responses.append(_pick_template(
            'contact',
            content,
            email=uni.contact_email or 'N/A',
            phone=uni.contact_phone or 'N/A'
        ))
        fallback_priority.append('contact')

    if 'accreditation' in intents and uni.accreditation:
        responses.append(_pick_template('accreditation', content, value=uni.accreditation))
        fallback_priority.append('accreditation')

    if 'housing' in intents and uni.housing:
        responses.append(_pick_template('housing', content, value=uni.housing))
        fallback_priority.append('housing')

    if 'founded' in intents:
        if uni.founded_year:
            responses.append(_pick_template('founded', content, uni_name=uni.name, year=uni.founded_year))
        else:
            responses.append("Founding year is not available in the current database records.")
        fallback_priority.append('founded')

    faq_answer, faq_score = _best_faq_answer(session.uni_id, content)
    if faq_answer:
        responses.append(_pick_template('faq', content + str(faq_score), answer=faq_answer))

    if responses:
        intro = _format_intro(uni.name)
        body = _format_bullets(responses)
        closing = _format_closing(uni, content)
        return f"{intro}\n{body}\n\n{closing}"

    # Intent fallback: if detected but no rich data available
    if fallback_priority:
        primary = fallback_priority[0].replace('_', ' ')
        return (
            f"{_pick_template('fallback_intent', content, intent=primary, uni_name=uni.name)} "
            f"For official information, please review {uni.website}. "
            f"{_pick_template('clarify', content)}"
        )

    return (
        f"{_pick_template('fallback_general', content)} "
        f"For complete and official details, please review {uni.website}. "
        f"{_pick_template('clarify', content)}"
    )

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
    raw_content = (data.get('content') or '').strip()
    content = raw_content.lower()

    session = ChatSession.query.get(chat_id)
    if not session:
        return jsonify({'message': 'Chat session not found'}), 404

    # 1. Store the student's message
    new_message = Message(session_id=chat_id, sender_id=sender_id, content=raw_content)
    db.session.add(new_message)
    bot_response = _generate_smart_response(raw_content)
    if not bot_response:
        # Always keep the chat responsive even if external AI provider is down.
        bot_response = _build_db_response(session, raw_content)

    # 2. Store and return bot message
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
