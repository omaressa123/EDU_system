from flask import Blueprint, jsonify, request

from utils.cv_analysis_service import (
    analyze_cv_text,
    extract_text_from_upload,
    generate_section_template,
    improve_cv_text,
)


document_ai_bp = Blueprint("document_ai", __name__)


@document_ai_bp.route("/analyze", methods=["POST"])
def analyze_document():
    uploaded_file = request.files.get("file")
    university_name = (request.form.get("university_name") or "").strip()

    if not uploaded_file:
        return jsonify({"message": "File is required."}), 400

    extracted_text, extraction_warnings = extract_text_from_upload(uploaded_file)
    if not extracted_text:
        return jsonify(
            {
                "message": "Could not extract text from this file.",
                "warnings": extraction_warnings,
            }
        ), 400

    analysis = analyze_cv_text(extracted_text, university_name)
    analysis["warnings"] = extraction_warnings

    return jsonify(
        {
            "message": "Document analyzed successfully.",
            "file_name": uploaded_file.filename,
            "analysis": analysis,
            "extracted_text": extracted_text,
        }
    )


@document_ai_bp.route("/improve", methods=["POST"])
def improve_document():
    data = request.get_json() or {}
    original_text = (data.get("text") or "").strip()
    university_name = (data.get("university_name") or "").strip()

    if not original_text:
        return jsonify({"message": "Text is required for improvement."}), 400

    analysis = analyze_cv_text(original_text, university_name)
    improvement = improve_cv_text(original_text, analysis)

    return jsonify(
        {
            "message": "Improved CV generated successfully.",
            "analysis": analysis,
            "improvement": improvement,
        }
    )


@document_ai_bp.route("/template", methods=["POST"])
def generate_template():
    data = request.get_json() or {}
    missing_sections = data.get("missing_sections") or []

    if not isinstance(missing_sections, list) or not missing_sections:
        return jsonify({"message": "missing_sections must be a non-empty list."}), 400

    templates = {}
    for section in missing_sections:
        templates[section] = generate_section_template(str(section))

    return jsonify(
        {
            "message": "Templates generated successfully.",
            "templates": templates,
        }
    )
