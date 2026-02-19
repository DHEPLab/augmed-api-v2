"""
Seed script for AugMed demo deployment.

Creates synthetic clinical cases, users, and configurations so a freshly
deployed instance has data to explore immediately.

Usage:
    pipenv run python -m script.seed.seed_demo

Or triggered automatically by setting SEED_DEMO_DATA=true in the environment
(the entrypoint.sh checks this).

Idempotent: checks for existing data before inserting.

Demo credentials:
    Admin:      admin@demo.augmed.org / augmed-demo
    Researcher: researcher@demo.augmed.org / augmed-demo
"""

import uuid
from datetime import date, datetime

from src import create_app, db
from src.user.utils.pcrypt import generate_salt, pcrypt


def seed():
    app = create_app()
    with app.app_context():
        if _already_seeded():
            print("Demo data already exists, skipping seed.")
            return
        print("Seeding demo data...")
        _seed_concepts()
        _seed_persons()
        _seed_visits()
        _seed_observations()
        _seed_measurements()
        _seed_users()
        _seed_system_config()
        _seed_answer_config()
        _seed_display_configs()
        db.session.commit()
        print("Demo data seeded successfully.")


def _already_seeded():
    """Check if seed data already exists by looking for the demo admin user."""
    result = db.session.execute(
        db.text("SELECT COUNT(*) FROM \"user\" WHERE email = 'admin@demo.augmed.org'")
    )
    return result.scalar() > 0


def _seed_concepts():
    """Insert the minimal OMOP concepts the app needs to render cases."""
    concepts = [
        # Gender concepts
        (8507, "MALE", "Gender", "Gender", "Gender", "S", "M", "1970-01-01", "2099-12-31"),
        (8532, "FEMALE", "Gender", "Gender", "Gender", "S", "F", "1970-01-01", "2099-12-31"),
        # Race concepts
        (8516, "Black or African American", "Race", "Race", "Race", "S", "5", "1970-01-01", "2099-12-31"),
        (8527, "White", "Race", "Race", "Race", "S", "W", "1970-01-01", "2099-12-31"),
        (8515, "Asian", "Race", "Race", "Race", "S", "A", "1970-01-01", "2099-12-31"),
        # Observation type concepts
        (38000282, "Chief Complaint", "Type Concept", "Observation Type", "Obs Type", "S", "OMOP4822053", "1970-01-01", "2099-12-31"),
        (44814721, "Patient reported", "Type Concept", "Observation Type", "Obs Type", "S", "OMOP4822056", "1970-01-01", "2099-12-31"),
        (0, "No matching concept", "Metadata", "None", "Undefined", None, "No matching concept", "1970-01-01", "2099-12-31"),
        # Observation concepts
        (4041306, "Tobacco smoking behavior", "Observation", "SNOMED", "Clinical Finding", "S", "365981007", "1970-01-01", "2099-12-31"),
        (4238768, "Alcohol units per week", "Observation", "SNOMED", "Observable Entity", "S", "160573003", "1970-01-01", "2099-12-31"),
        (79936, "Nocturia", "Observation", "SNOMED", "Clinical Finding", "S", "139394000", "1970-01-01", "2099-12-31"),
        (4167217, "Family history of clinical finding", "Observation", "SNOMED", "Clinical Finding", "S", "416471007", "1970-01-01", "2099-12-31"),
        (4147325, "Heartburn", "Observation", "SNOMED", "Clinical Finding", "S", "16331000", "1970-01-01", "2099-12-31"),
        (40303797, "Anemia", "Observation", "SNOMED", "Clinical Finding", "S", "271737000", "1970-01-01", "2099-12-31"),
        (37311267, "Weight loss", "Observation", "SNOMED", "Clinical Finding", "S", "89362005", "1970-01-01", "2099-12-31"),
        (35826012, "Abdominal pain", "Observation", "SNOMED", "Clinical Finding", "S", "21522001", "1970-01-01", "2099-12-31"),
        (45614722, "Colorectal Cancer Score", "Observation", "SNOMED", "Clinical Finding", "S", "CRC-SCORE", "1970-01-01", "2099-12-31"),
        (1008364, "History of clinical finding in subject", "Observation", "SNOMED", "Clinical Finding", "S", "417662000", "1970-01-01", "2099-12-31"),
        # Measurement concepts
        (4181041, "Hemoglobin", "Measurement", "SNOMED", "Procedure", "S", "104142005", "1970-01-01", "2099-12-31"),
        (4301868, "Weight", "Measurement", "SNOMED", "Observable Entity", "S", "27113001", "1970-01-01", "2099-12-31"),
        (4326744, "Blood pressure", "Measurement", "SNOMED", "Observable Entity", "S", "75367002", "1970-01-01", "2099-12-31"),
        (4152368, "Abdominal", "Measurement", "SNOMED", "Spec Anatomic Site", "S", "818983003", "1970-01-01", "2099-12-31"),
        (40490382, "BMI (body mass index) centile", "Measurement", "SNOMED", "Observable Entity", "S", "896691000000102", "1970-01-01", "2099-12-31"),
        # Unit concepts
        (8541, "kilogram", "Unit", "UCUM", "Unit", "S", "kg", "1970-01-01", "2099-12-31"),
        (8876, "millimeter mercury column", "Unit", "UCUM", "Unit", "S", "mm[Hg]", "1970-01-01", "2099-12-31"),
        (9529, "kilogram", "Unit", "UCUM", "Unit", "S", "kg", "1970-01-01", "2099-12-31"),
        (9580, "minute", "Unit", "UCUM", "Unit", "S", "min", "1970-01-01", "2099-12-31"),
        # Qualifier concepts
        (710237, "units", "Unit", "UCUM", "Unit", "S", "U", "1970-01-01", "2099-12-31"),
        (42538822, "Severity", "Observation", "SNOMED", "Qualifier Value", "S", "272141005", "1970-01-01", "2099-12-31"),
        # Hemoglobin value concepts
        (35824280, "Normal", "Meas Value", "SNOMED", "Qualifier Value", "S", "17621005", "1970-01-01", "2099-12-31"),
        (8511, "mild", "Meas Value", "SNOMED", "Qualifier Value", "S", "255604002", "1970-01-01", "2099-12-31"),
        # Visit type concept
        (44818519, "Clinical Study visit", "Type Concept", "Visit Type", "Visit Type", "S", "OMOP4822465", "1970-01-01", "2099-12-31"),
    ]

    for c in concepts:
        db.session.execute(
            db.text("""
                INSERT INTO concept (concept_id, concept_name, domain_id, vocabulary_id,
                    concept_class_id, standard_concept, concept_code,
                    valid_start_date, valid_end_date)
                VALUES (:cid, :cname, :domain, :vocab, :cclass, :std, :code,
                    :vstart, :vend)
                ON CONFLICT (concept_id) DO NOTHING
            """),
            {
                "cid": c[0], "cname": c[1], "domain": c[2], "vocab": c[3],
                "cclass": c[4], "std": c[5], "code": c[6],
                "vstart": c[7], "vend": c[8],
            },
        )


def _seed_persons():
    """Create 3 synthetic patient records."""
    persons = [
        (1001, 8532, 1983, 12, 31, 8516, 0, "DEMO-001"),
        (1002, 8507, 1975, 5, 15, 8527, 0, "DEMO-002"),
        (1003, 8532, 1990, 8, 22, 8515, 0, "DEMO-003"),
    ]
    for p in persons:
        db.session.execute(
            db.text("""
                INSERT INTO person (person_id, gender_concept_id, year_of_birth,
                    month_of_birth, day_of_birth, race_concept_id,
                    ethnicity_concept_id, person_source_value)
                VALUES (:pid, :gender, :yob, :mob, :dob, :race, :eth, :src)
                ON CONFLICT (person_id) DO NOTHING
            """),
            {
                "pid": p[0], "gender": p[1], "yob": p[2], "mob": p[3],
                "dob": p[4], "race": p[5], "eth": p[6], "src": p[7],
            },
        )


def _seed_visits():
    """Create 3 visit occurrences (one per person = one case each)."""
    visits = [
        (1001, 1001, 0, "2024-06-01", "2024-07-01", 44818519),
        (1002, 1002, 0, "2024-06-15", "2024-07-15", 44818519),
        (1003, 1003, 0, "2024-07-01", "2024-08-01", 44818519),
    ]
    for v in visits:
        db.session.execute(
            db.text("""
                INSERT INTO visit_occurrence (visit_occurrence_id, person_id,
                    visit_concept_id, visit_start_date, visit_end_date,
                    visit_type_concept_id)
                VALUES (:vid, :pid, :vcid, :vstart, :vend, :vtcid)
                ON CONFLICT (visit_occurrence_id) DO NOTHING
            """),
            {
                "vid": v[0], "pid": v[1], "vcid": v[2],
                "vstart": v[3], "vend": v[4], "vtcid": v[5],
            },
        )


def _seed_observations():
    """Insert synthetic observations for each case."""
    obs_id = 10001
    observations = []
    for visit_id, person_id in [(1001, 1001), (1002, 1002), (1003, 1003)]:
        # Smoking status
        observations.append(
            (obs_id, person_id, 4041306, "2024-06-01", 0, None, "non-smoker", None, None, None, visit_id)
        )
        obs_id += 1
        # Alcohol intake
        observations.append(
            (obs_id, person_id, 4238768, "2024-06-01", 0, None, None, None, None, 710237, visit_id)
        )
        obs_id += 1
        # Family history
        observations.append(
            (obs_id, person_id, 4167217, "2024-06-01", 0, None, "Cancer: No", None, None, None, visit_id)
        )
        obs_id += 1
        # Medical history
        observations.append(
            (obs_id, person_id, 1008364, "2024-06-01", 0, None, "Hypertension: Yes", None, None, None, visit_id)
        )
        obs_id += 1
        # Chief complaint — nocturia
        observations.append(
            (obs_id, person_id, 79936, "2024-06-01", 38000282, None, "3x per night", None, 0, None, visit_id)
        )
        obs_id += 1
        # Patient-reported abdominal pain
        observations.append(
            (obs_id, person_id, 35826012, "2024-06-01", 44814721, None, "Duration: 2 months", 0, None, None, visit_id)
        )
        obs_id += 1
        # CRC score (for AI arm)
        observations.append(
            (obs_id, person_id, 45614722, "2024-06-01", 0, None,
             f"Colorectal Cancer Score: {7 + person_id - 1001}", None, None, None, visit_id)
        )
        obs_id += 1

    for o in observations:
        db.session.execute(
            db.text("""
                INSERT INTO observation (observation_id, person_id,
                    observation_concept_id, observation_date,
                    observation_type_concept_id, value_as_number,
                    value_as_string, value_as_concept_id,
                    qualifier_concept_id, unit_concept_id,
                    visit_occurrence_id)
                VALUES (:oid, :pid, :ocid, :odate, :otcid, :vnum,
                    :vstr, :vcid, :qcid, :ucid, :vid)
                ON CONFLICT (observation_id) DO NOTHING
            """),
            {
                "oid": o[0], "pid": o[1], "ocid": o[2], "odate": o[3],
                "otcid": o[4], "vnum": o[5], "vstr": o[6], "vcid": o[7],
                "qcid": o[8], "ucid": o[9], "vid": o[10],
            },
        )


def _seed_measurements():
    """Insert synthetic measurements (vitals) for each case."""
    meas_id = 10001
    measurements = []
    for visit_id, person_id in [(1001, 1001), (1002, 1002), (1003, 1003)]:
        # Hemoglobin — Normal
        measurements.append(
            (meas_id, person_id, 4181041, "2024-06-01", 0, None, None, 35824280, None, visit_id)
        )
        meas_id += 1
        # Weight
        measurements.append(
            (meas_id, person_id, 4301868, "2024-06-01", 0, None, 0, None, 8541, visit_id)
        )
        meas_id += 1
        # Blood pressure
        measurements.append(
            (meas_id, person_id, 4326744, "2024-06-01", 0, None, 0, None, 8876, visit_id)
        )
        meas_id += 1

    for m in measurements:
        db.session.execute(
            db.text("""
                INSERT INTO measurement (measurement_id, person_id,
                    measurement_concept_id, measurement_date,
                    measurement_type_concept_id, operator_concept_id,
                    value_as_number, value_as_concept_id,
                    unit_concept_id, visit_occurrence_id)
                VALUES (:mid, :pid, :mcid, :mdate, :mtcid, :ocid,
                    :vnum, :vcid, :ucid, :vid)
                ON CONFLICT (measurement_id) DO NOTHING
            """),
            {
                "mid": m[0], "pid": m[1], "mcid": m[2], "mdate": m[3],
                "mtcid": m[4], "ocid": m[5], "vnum": m[6], "vcid": m[7],
                "ucid": m[8], "vid": m[9],
            },
        )


def _seed_users():
    """Create demo admin and researcher users with known passwords."""
    demo_password = "augmed-demo"

    users = [
        {
            "name": "Demo Admin",
            "email": "admin@demo.augmed.org",
            "admin_flag": True,
            "position": "Administrator",
            "employer": "Demo Institution",
            "area_of_clinical_ex": "Administration",
        },
        {
            "name": "Demo Researcher",
            "email": "researcher@demo.augmed.org",
            "admin_flag": False,
            "position": "Physician",
            "employer": "Demo Hospital",
            "area_of_clinical_ex": "Internal Medicine",
        },
    ]

    for user in users:
        salt = generate_salt()
        hashed = pcrypt(demo_password, salt)
        db.session.execute(
            db.text("""
                INSERT INTO "user" (name, email, password, salt, admin_flag,
                    position, employer, area_of_clinical_ex, active)
                VALUES (:name, :email, :password, :salt, :admin_flag,
                    :position, :employer, :area, true)
                ON CONFLICT (email) DO NOTHING
            """),
            {
                "name": user["name"],
                "email": user["email"],
                "password": hashed,
                "salt": salt,
                "admin_flag": user["admin_flag"],
                "position": user["position"],
                "employer": user["employer"],
                "area": user["area_of_clinical_ex"],
            },
        )


def _seed_system_config():
    """Insert the page_config that drives the case display tree."""
    page_config = {
        "BACKGROUND": {
            "Family History": [4167217],
            "Social History": {
                "Smoke": [4041306],
                "Drink": [4238768],
            },
            "Medical History": [1008364],
            "CRC risk assessments": [45614722],
        },
        "PATIENT COMPLAINT": {
            "Chief Complaint": [38000282],
            "Patient Reported": [44814721],
        },
        "PHYSICAL EXAMINATION": {
            "Hemoglobin": [4181041],
            "Body measure": [4301868, 4326744, 4152368],
        },
    }

    import json

    db.session.execute(
        db.text("""
            INSERT INTO system_config (id, json_config)
            VALUES ('page_config', :config)
            ON CONFLICT (id) DO NOTHING
        """),
        {"config": json.dumps(page_config)},
    )


def _seed_answer_config():
    """Insert a demo questionnaire config."""
    config_id = str(uuid.uuid4())
    questionnaire = [
        {
            "type": "single_choice",
            "title": "Based on the information provided, what is your assessment of colorectal cancer risk for this patient?",
            "required": True,
            "options": ["Low risk", "Medium risk", "High risk", "Insufficient information"],
        },
        {
            "type": "single_choice",
            "title": "Would you recommend this patient for colorectal cancer screening?",
            "required": True,
            "options": ["Yes, immediately", "Yes, within routine schedule", "No", "Need more information"],
        },
        {
            "type": "free_text",
            "title": "Please provide any additional comments or reasoning for your assessment.",
            "required": False,
        },
    ]

    import json

    db.session.execute(
        db.text("""
            INSERT INTO answer_config (id, config, created_timestamp)
            VALUES (:id, :config, :ts)
        """),
        {"id": config_id, "config": json.dumps(questionnaire), "ts": datetime.utcnow()},
    )


def _seed_display_configs():
    """Assign all 3 cases to the demo researcher with full feature visibility."""
    researcher_email = "researcher@demo.augmed.org"

    for case_id in [1001, 1002, 1003]:
        config_id = f"{researcher_email}-{case_id}"
        path_config = [
            {"path": "BACKGROUND.Family History.Cancer: No", "style": {"highlight": True}},
            {"path": "BACKGROUND.Medical History.Hypertension: Yes", "style": {"highlight": True}},
            {"path": "BACKGROUND.Social History.Smoke.non-smoker", "style": {}},
            {"path": "BACKGROUND.Social History.Drink", "style": {}},
            {"path": "RISK ASSESSMENT.CRC risk assessments", "style": {}},
        ]

        import json

        db.session.execute(
            db.text("""
                INSERT INTO display_config (id, user_email, case_id, path_config)
                VALUES (:id, :email, :cid, :config)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": config_id,
                "email": researcher_email,
                "cid": case_id,
                "config": json.dumps(path_config),
            },
        )


if __name__ == "__main__":
    seed()
