import csv
import os
from app import create_app
from models import db, University, Faculty, Program, AdmissionRequirement, FAQEntry

app = create_app()

def seed_egyptian_universities():
    with app.app_context():
        # Clear and recreate to apply schema changes (since we added columns)
        db.drop_all()
        db.create_all()

        # 1. Manual Seed Data (for detailed info)
        manual_unis = {
            "cairo university": {
                "website": "https://cu.edu.eg/Home",
                "scholarships": "Offers merit-based scholarships for top-ranking students in Thanaweya Amma.",
                "facilities": "Main library, historical campus, sports facilities, and several research centers.",
                "contact_email": "info@cu.edu.eg",
                "contact_phone": "+20 2 35676105",
                "accreditation": "Accredited by the Supreme Council of Universities in Egypt.",
                "housing": "Provides student hostels for those coming from outside Cairo and Giza.",
                "min_fees": 0,
                "max_fees": 1000,
                "curriculums": ["public"]
            },
            "american university in cairo (auc)": {
                "website": "https://www.aucegypt.edu/",
                "scholarships": "Extensive financial aid and scholarships (merit-based and need-based), including the Public School Scholarship.",
                "facilities": "State-of-the-art library, Olympic-sized pool, several dining options, and a modern theater.",
                "contact_email": "admissions@aucegypt.edu",
                "contact_phone": "+20 2 26151000",
                "accreditation": "Accredited by the Middle States Commission on Higher Education (USA) and the Supreme Council of Universities.",
                "housing": "On-campus dormitories and off-campus housing services available.",
                "min_fees": 150000,
                "max_fees": 300000,
                "curriculums": ["public", "american", "private"]
            },
            "british university in egypt (bue)": {
                "website": "https://www.bue.edu.eg/",
                "scholarships": "Scholarships for top students, siblings discount, and sports excellence awards.",
                "facilities": "Modern campus with high-tech labs, large library, and recreational areas.",
                "contact_email": "admission@bue.edu.eg",
                "contact_phone": "+20 2 26890000",
                "accreditation": "Validated by UK partner universities and accredited by the Supreme Council of Universities.",
                "housing": "Student dorms located near the campus with shuttle services.",
                "min_fees": 120000,
                "max_fees": 200000,
                "curriculums": ["public", "american", "private"]
            },
            "alexandria university": {
                "website": "https://www.alexu.edu.eg/index.php/en/",
                "scholarships": "Awards for academic excellence and support for students with financial needs.",
                "facilities": "Research centers, central library, medical clinics, and sports clubs.",
                "contact_email": "info@alexu.edu.eg",
                "contact_phone": "+20 3 5921675",
                "accreditation": "Accredited by the Supreme Council of Universities.",
                "housing": "Hostels for male and female students across the city.",
                "min_fees": 0,
                "max_fees": 1000,
                "curriculums": ["public"]
            },
            "ain shams university": {
                "website": "https://www.asu.edu.eg/ar",
                "scholarships": "Merit scholarships for top Thanaweya Amma students and financial aid for eligible students.",
                "facilities": "Central library, university hospitals, and various research units.",
                "contact_email": "info@asu.edu.eg",
                "contact_phone": "+20 2 26831474",
                "accreditation": "Accredited by the Supreme Council of Universities.",
                "housing": "Student housing facilities available in multiple locations.",
                "min_fees": 0,
                "max_fees": 1000,
                "curriculums": ["public"]
            }
        }

        # 2. Read CSV Data
        # Using a relative path that works both locally and in Docker
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(current_dir, 'data', 'egypt_universities.csv')
        
        if not os.path.exists(csv_path):
            print(f"Error: CSV file not found at {csv_path}")
            return
            
        uni_map = {} # {uni_name: {info: {}, faculties: {fac_name: [programs]}}}

        with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                uni_name = row['University'].strip().lower()
                fac_name = row['Faculty'].strip()
                prog_name = row['Department'].strip()
                city = row['City'].strip()
                uni_type = row['Type'].strip().lower()
                founded = row['Founded_Year'].strip()
                try:
                    founded = int(float(founded))
                except:
                    founded = None

                if uni_name not in uni_map:
                    # Initialize university with basic info from CSV
                    uni_map[uni_name] = {
                        "name": row['University'].strip(),
                        "type": uni_type if uni_type in ['public', 'private'] else 'public',
                        "city": city,
                        "founded": founded,
                        "faculties": {}
                    }
                    
                    # Merge manual info if available
                    if uni_name in manual_unis:
                        uni_map[uni_name].update(manual_unis[uni_name])
                    else:
                        # Defaults for universities not in manual list
                        uni_map[uni_name].update({
                            "website": f"https://www.{uni_name.replace(' ', '')}.edu.eg",
                            "scholarships": "Contact university for scholarship information.",
                            "facilities": "Standard university facilities.",
                            "contact_email": f"info@{uni_name.replace(' ', '')}.edu.eg",
                            "contact_phone": "N/A",
                            "accreditation": "Accredited by the Supreme Council of Universities.",
                            "housing": "Contact university for housing availability.",
                            "min_fees": 0 if uni_type == 'public' else 50000,
                            "max_fees": 1000 if uni_type == 'public' else 150000,
                            "curriculums": ["public"] if uni_type == 'public' else ["public", "american", "private"]
                        })

                if fac_name not in uni_map[uni_name]["faculties"]:
                    uni_map[uni_name]["faculties"][fac_name] = []
                
                uni_map[uni_name]["faculties"][fac_name].append(prog_name)

        # 3. Save to DB
        for uni_name, u_data in uni_map.items():
            uni = University(
                name=u_data["name"],
                type=u_data["type"],
                location=u_data.get("location", u_data["city"]),
                city=u_data["city"],
                country="Egypt",
                website=u_data["website"],
                min_tuition_fees=u_data["min_fees"],
                max_tuition_fees=u_data["max_fees"],
                scholarships=u_data["scholarships"],
                facilities=u_data["facilities"],
                contact_email=u_data["contact_email"],
                contact_phone=u_data["contact_phone"],
                accreditation=u_data["accreditation"],
                housing=u_data["housing"],
                founded_year=u_data["founded"],
                accepted_curriculums=u_data["curriculums"]
            )
            db.session.add(uni)
            db.session.flush()

            for f_name, programs in u_data["faculties"].items():
                faculty = Faculty(
                    uni_id=uni.id, 
                    name=f_name, 
                    fees=u_data["min_fees"] if u_data["type"] == 'public' else (u_data["min_fees"] + u_data["max_fees"]) / 2,
                    duration="4-5 years"
                )
                db.session.add(faculty)
                db.session.flush()

                for p_name in programs:
                    prog = Program(
                        faculty_id=faculty.id,
                        name=p_name,
                        degree="BSc",
                        duration_years=4 if "Medicine" not in f_name else 6,
                        min_grade_required=85.0 if u_data["type"] == 'private' else 90.0,
                        language="English"
                    )
                    db.session.add(prog)

            # Add extra FAQs
            faqs = [
                FAQEntry(uni_id=uni.id, question="Do you have scholarships?", answer=u_data["scholarships"]),
                FAQEntry(uni_id=uni.id, question="What facilities are available?", answer=u_data["facilities"]),
                FAQEntry(uni_id=uni.id, question="How can I contact you?", answer=f"Email: {u_data['contact_email']}, Phone: {u_data['contact_phone']}"),
                FAQEntry(uni_id=uni.id, question="Is the university accredited?", answer=u_data["accreditation"]),
                FAQEntry(uni_id=uni.id, question="Do you provide housing?", answer=u_data["housing"]),
                FAQEntry(uni_id=uni.id, question="When was the university founded?", answer=f"It was founded in {u_data['founded']}." if u_data['founded'] else "Founding year not specified.")
            ]
            db.session.add_all(faqs)

        db.session.commit()
        print(f"Enriched data from CSV and manual entries seeded successfully for {len(uni_map)} universities!")

if __name__ == '__main__':
    seed_egyptian_universities()
