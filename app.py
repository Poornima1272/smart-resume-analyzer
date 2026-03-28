from flask import Flask, render_template, request, jsonify
import PyPDF2
from docx import Document
import re
import os
import io
import spacy

# ✅ Load spaCy model
nlp = spacy.load("en_core_web_sm")

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ================= AI FUNCTION =================
def ai_resume_analysis(text):
    doc = nlp(text)

    skills = []
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"] and len(token.text) > 2:
            skills.append(token.text.lower())

    skills = list(set(skills))[:10]

    # Role suggestion
    if "python" in text.lower():
        role = "Python Developer"
    elif "java" in text.lower():
        role = "Java Developer"
    elif "html" in text.lower() or "css" in text.lower():
        role = "Frontend Developer"
    else:
        role = "Software Developer"

    return f"""
🔹 Extracted Skills: {', '.join(skills)}

🔹 Suggested Role: {role}

🔹 Improvements:
- Add more technical keywords
- Improve resume formatting
- Add projects with description
- Include achievements
"""


# ================= ANALYZER =================
class ResumeAnalyzer:

    def extract_text(self, file_content, filename):
        if filename.endswith('.pdf'):
            pdf = PyPDF2.PdfReader(io.BytesIO(file_content))
            return " ".join([p.extract_text() or "" for p in pdf.pages])

        elif filename.endswith('.docx'):
            doc = Document(io.BytesIO(file_content))
            return " ".join([p.text for p in doc.paragraphs])

        return ""

    def extract_skills(self, text):
        skills = re.findall(r'\b(python|java|sql|html|css|aws|react)\b', text.lower())
        return list(set(skills))

    # 🔥 NEW ATS SCORE FUNCTION
    def calculate_score(self, text):
        score = 0
        text = text.lower()

        # ✅ Keywords
        keywords = ["python", "java", "sql", "html", "css", "react", "aws"]
        matches = sum(1 for k in keywords if k in text)
        score += matches * 10   # max 70

        # ✅ Length score
        word_count = len(text.split())
        if word_count > 300:
            score += 20
        elif word_count > 150:
            score += 10

        # ✅ Sections check
        sections = ["education", "project", "experience", "skills"]
        section_matches = sum(1 for s in sections if s in text)
        score += section_matches * 2   # max 8

        return min(score, 100)

    def analyze(self, file_content, filename):
        text = self.extract_text(file_content, filename)

        if not text.strip():
            return {'success': False, 'error': 'Cannot read file'}

        skills = self.extract_skills(text)
        score = self.calculate_score(text)

        ai_result = ai_resume_analysis(text)

        return {
            'success': True,
            'score': score,
            'skills': skills,
            'ai_analysis': ai_result
        }


analyzer = ResumeAnalyzer()


# ================= ROUTES =================
@app.route('/')
def index():
    return render_template('resume-ai.html')


@app.route('/analyze', methods=['POST'])
def analyze_route():
    if 'resume' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})

    file = request.files['resume']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})

    try:
        content = file.read()
        result = analyzer.analyze(content, file.filename)
        print(result)
        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ================= RUN =================
if __name__ == '__main__':
    app.run(debug=True)