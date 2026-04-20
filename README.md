# EDU System - Egyptian University Matching Platform

## Overview
EDU System is a comprehensive Flask web application for matching Egyptian students (public, American, private schools) with universities. Features admin dashboard, student profiles, chat system, application tracking, and AI-powered university search/matching.

## ✨ Features
- **Student Profiles**: Detailed academic records (national exam scores, SAT/ACT, IB/IGCSE/A-Level)
- **Admin Dashboard**: Stats, recent activity, profile management
- **University Database**: 100+ Egyptian universities with fees, requirements, faculties
- **Chat System**: Real-time student ↔ uni rep conversations
- **Application Tracking**: Status workflow (draft → accepted/rejected)
- **Search & Matching**: AI-powered university recommendations based on grades/school type
- **Document Upload**: Transcripts, certificates (mock S3 integration)
- **Responsive UI**: Modern dashboard with charts, dark theme

## 🛠 Tech Stack
- **Backend**: Flask, Flask-SQLAlchemy, Flask-Login (session auth)
- **Frontend**: HTML/CSS/JS, Chart.js, FontAwesome
- **Database**: SQLite (production-ready PostgreSQL)
- **Blueprints**: auth, admin, profile, search, chat, application
- **Docker**: Ready for containerization

## 🚀 Quick Start
```bash
cd EDU_system
pip install -r requirements.txt
python create_admin.py  # Create admin user
flask run
```
- Admin login: username `admin`, password `admin123`
- Visit `http://localhost:5000/dashboard`

## 📁 Project Structure
```
EDU_system/
├── app.py              # Main app & routes
├── models.py           # DB models (User hierarchy, University, etc)
├── blueprints/         # Modular routes
│   ├── admin/          # Dashboard, data management
│   ├── profile/        # User profile
│   ├── auth/           # Login/registration
│   ├── search/         # Uni matching
│   ├── chat/           # Messaging
│   └── application/    # App tracking
├── static/             # CSS/JS/HTML
├── utils/matching.py   # AI matching logic
└── data/egypt_universities.csv
```

## 🔌 API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | Admin/student login |
| `/api/profile/profile` | GET/POST | Profile view/update |
| `/api/profile/results` | POST | Update student grades |
| `/api/admin/stats` | GET | Dashboard stats |
| `/api/search/universities` | GET | Search unis |
| `/api/chat/start` | POST | New chat session |
| `/api/application/submit` | POST | Submit app |

## 🗄 Database Models
```mermaid
classDiagram
    class User {
        <<polymorphic>> id, name, email, role
    }
    class Student {
        school_type, national_id
    }
    class PublicSchoolStudent {
        national_exam_score, track
    }
    class University {
        name, fees, requirements
    }
    class AcademicProfile {
        grades (JSON), documents
    }
    User <|-- Student : inherits
    Student <|-- PublicSchoolStudent
    Student ||--o| AcademicProfile
```

## 🐳 Docker
```bash
docker-compose up --build
```

## 📊 Screenshots
![Dashboard](screenshots/dashboard.png)
![Profile](screenshots/profile.png)

## 🤝 Contributing
1. Fork repo
2. Create feature branch
3. PR to `main`

## 📄 License
MIT
