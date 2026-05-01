import io
import re
from typing import Dict, List, Tuple

import PyPDF2
import pytesseract
from PIL import Image
from docx import Document as DocxDocument


EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
NAME_REGEX = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b")


def extract_text_from_upload(file_storage) -> Tuple[str, List[str]]:
    filename = (file_storage.filename or "").lower()
    warnings: List[str] = []

    if filename.endswith(".pdf"):
        return _extract_pdf_text(file_storage), warnings

    if filename.endswith(".docx"):
        return _extract_docx_text(file_storage), warnings

    if filename.endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
        warnings.append("OCR extraction may contain recognition errors.")
        return _extract_image_text(file_storage), warnings

    if filename.endswith(".doc"):
        warnings.append("Legacy .doc files are not fully supported. Please upload .docx for better accuracy.")
        return "", warnings

    warnings.append("Unsupported file type. Use PDF, DOCX, or image files.")
    return "", warnings


def analyze_cv_text(text: str, university_name: str = "") -> Dict:
    cleaned = _normalize(text)
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    words = cleaned.split()

    found = _detected_core_fields(cleaned)
    missing = _missing_sections(cleaned)
    weaknesses = _weaknesses(cleaned, lines, words)
    issues = _issues(cleaned, lines)
    suggestions = _build_actionable_suggestions(missing, weaknesses, issues)

    score = _score(found, missing, weaknesses, issues)
    specialization = _specialization_feedback(cleaned, university_name)

    return {
        "score": score,
        "found": found,
        "missing": missing,
        "weakness": weaknesses,
        "issues": issues,
        "suggestions": suggestions,
        "specialization_feedback": specialization,
    }


def improve_cv_text(original_text: str, analysis: Dict) -> Dict:
    improved = original_text.strip()
    applied_fixes: List[Dict] = []
    templates: Dict[str, str] = {}

    for section in analysis.get("missing", []):
        template = generate_section_template(section)
        templates[section] = template
        improved += f"\n\n{template}"
        applied_fixes.append({
            "problem": f"Missing section: {section}",
            "fix_applied": True,
            "how": f"Inserted a ready-to-fill {section} template.",
        })

    if "Weak formatting (very long lines or unstructured bullets)." in analysis.get("issues", []):
        improved = _format_for_readability(improved)
        applied_fixes.append({
            "problem": "Weak formatting",
            "fix_applied": True,
            "how": "Reformatted text with clearer section spacing and bullet points.",
        })

    if "Potential grammar/style issues (very long sentences)." in analysis.get("issues", []):
        improved = _split_long_sentences(improved)
        applied_fixes.append({
            "problem": "Potential grammar/style issues",
            "fix_applied": True,
            "how": "Split very long sentences into shorter, clearer statements.",
        })

    for weakness in analysis.get("weakness", []):
        applied_fixes.append({
            "problem": weakness,
            "fix_applied": True,
            "how": "Added specific suggestion and placeholders to strengthen this section.",
        })

    return {
        "improved_text": improved.strip(),
        "templates_added": templates,
        "validation": applied_fixes,
    }


def generate_section_template(section_name: str) -> str:
    key = section_name.strip().lower()

    if key == "projects":
        return (
            "Projects\n"
            "- Project Name: [Title]\n"
            "  - Goal: [What problem you solved]\n"
            "  - Tools: [Python, Flask, SQL, ...]\n"
            "  - Result: [Measurable impact]"
        )
    if key == "achievements":
        return (
            "Achievements\n"
            "- [Award or milestone], [Year]\n"
            "- [Competition/certification], [Rank or score]"
        )
    if key == "motivation paragraph":
        return (
            "Motivation Paragraph\n"
            "I am applying because [specific reason]. My academic preparation in [field] and "
            "practical work in [project/experience] align with the program's focus on [focus area]. "
            "I am motivated to contribute through [clear contribution]."
        )
    if key == "experience":
        return (
            "Experience\n"
            "- Role, Company, Duration\n"
            "  - Responsibility: [What you handled]\n"
            "  - Impact: [Outcome with numbers if possible]"
        )
    return (
        f"{section_name.title()}\n"
        "- Add 2 to 4 concise bullet points focused on actions and measurable outcomes."
    )


def _extract_pdf_text(file_storage) -> str:
    content = file_storage.read()
    file_storage.seek(0)
    reader = PyPDF2.PdfReader(io.BytesIO(content))
    text_parts: List[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text_parts.append(page_text)
    return "\n".join(text_parts).strip()


def _extract_docx_text(file_storage) -> str:
    content = file_storage.read()
    file_storage.seek(0)
    document = DocxDocument(io.BytesIO(content))
    paragraphs = [p.text for p in document.paragraphs if p.text and p.text.strip()]
    return "\n".join(paragraphs).strip()


def _extract_image_text(file_storage) -> str:
    content = file_storage.read()
    file_storage.seek(0)
    image = Image.open(io.BytesIO(content))
    return pytesseract.image_to_string(image).strip()


def _normalize(text: str) -> str:
    return re.sub(r"\r\n?", "\n", text or "").strip()


def _detected_core_fields(text: str) -> List[str]:
    found: List[str] = []
    if EMAIL_REGEX.search(text):
        found.append("Email")
    if _detect_name(text):
        found.append("Name")
    return found


def _detect_name(text: str) -> str:
    match = NAME_REGEX.search(text[:500])
    return match.group(1) if match else ""


def _missing_sections(text: str) -> List[str]:
    lowered = text.lower()
    required_markers = {
        "Projects": ["project"],
        "Achievements": ["achievement", "award", "honor"],
        "Motivation paragraph": ["motivation", "objective", "personal statement"],
        "Experience": ["experience", "internship", "employment"],
    }
    missing = []
    for section, markers in required_markers.items():
        if not any(marker in lowered for marker in markers):
            missing.append(section)
    return missing


def _weaknesses(text: str, lines: List[str], words: List[str]) -> List[str]:
    weaknesses: List[str] = []
    if len(words) < 180:
        weaknesses.append("CV is too short for strong evaluation.")
    if not any(len(line.split()) > 3 and line.lstrip().startswith(("-", "*", "•")) for line in lines):
        weaknesses.append("Short or missing bullet-driven experience section.")
    if "skills" in text.lower() and text.lower().count("skill") < 2:
        weaknesses.append("Skills section appears brief.")
    return weaknesses


def _issues(text: str, lines: List[str]) -> List[str]:
    issues: List[str] = []
    if any(len(line) > 140 for line in lines):
        issues.append("Weak formatting (very long lines or unstructured bullets).")
    if re.search(r"([^.?!]{180,}[.?!])", text):
        issues.append("Potential grammar/style issues (very long sentences).")
    return issues


def _build_actionable_suggestions(missing: List[str], weaknesses: List[str], issues: List[str]) -> List[str]:
    suggestions: List[str] = []
    for section in missing:
        suggestions.append(f"Add a dedicated {section} section with at least 2 concrete bullet points.")
    for weakness in weaknesses:
        if "too short" in weakness.lower():
            suggestions.append("Expand the CV to 350-600 words by adding outcomes and measurable impact.")
        elif "bullet-driven" in weakness.lower():
            suggestions.append("Rewrite experience using action verbs and 2-4 quantified bullet points.")
        elif "skills section" in weakness.lower():
            suggestions.append("List 6-10 skills grouped by technical, language, and soft skills.")
    for issue in issues:
        if "formatting" in issue.lower():
            suggestions.append("Use short lines, clear section headers, and consistent bullet indentation.")
        elif "grammar" in issue.lower():
            suggestions.append("Split long sentences; keep each bullet under 25 words and proofread tense consistency.")
    return suggestions[:10]


def _score(found: List[str], missing: List[str], weaknesses: List[str], issues: List[str]) -> int:
    score = 100
    score -= max(0, (2 - len(found)) * 12)
    score -= len(missing) * 10
    score -= len(weaknesses) * 8
    score -= len(issues) * 6
    return max(0, min(100, score))


def _specialization_feedback(text: str, university_name: str) -> str:
    university = (university_name or "").strip()
    if not university:
        return "No university selected. Provide a university name for specialized CV alignment feedback."

    lowered = text.lower()
    technical_markers = ["python", "programming", "engineering", "data", "math", "algorithm"]
    writing_markers = ["research", "essay", "analysis", "presentation", "communication"]

    technical_hits = sum(1 for marker in technical_markers if marker in lowered)
    writing_hits = sum(1 for marker in writing_markers if marker in lowered)

    if technical_hits < 2 and any(name in university.lower() for name in ["guc", "cairo", "ain shams"]):
        return f"This CV is currently weak for {university}: add technical projects, quantifiable outcomes, and core skills."

    if writing_hits < 1:
        return f"For {university}, strengthen motivation and communication-oriented achievements."

    return f"This CV has a reasonable baseline for {university}; focus next on stronger project evidence and formatting polish."


def _format_for_readability(text: str) -> str:
    blocks = [block.strip() for block in text.split("\n\n") if block.strip()]
    normalized_blocks = []
    for block in blocks:
        if len(block.split()) > 35 and "\n-" not in block and "\n•" not in block:
            sentences = re.split(r"(?<=[.?!])\s+", block)
            bullet_block = "\n".join(f"- {sentence.strip()}" for sentence in sentences if sentence.strip())
            normalized_blocks.append(bullet_block)
        else:
            normalized_blocks.append(block)
    return "\n\n".join(normalized_blocks)


def _split_long_sentences(text: str) -> str:
    def _sentence_splitter(match: re.Match) -> str:
        sentence = match.group(0)
        return sentence.replace(", ", ". ", 1)

    return re.sub(r"[^.?!]{200,}[.?!]", _sentence_splitter, text)
