import os
from app import create_app
from models import db, Admin, User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Check if admin exists
    existing = User.query.filter_by(email='admin@gmail.com').first()
    if existing:
        print("Admin already exists.")
    else:
        admin = Admin(
            name='admin1',
            email='admin1@gmail.com',
            password_hash=generate_password_hash('admin1234'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin created successfully! Email: admin1@gmail.com, Password: admin1234")

print("Done.")
