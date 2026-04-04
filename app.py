import re
import json
import sqlite3
import hashlib
from datetime import datetime

import streamlit as st
import pandas as pd
from openai import OpenAI

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.ensemble import VotingClassifier

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="NUC Accreditation Prediction System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM STYLING
# =========================================================
st.markdown("""
<style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1.5rem;
    }

    .hero-card {
        padding: 1.2rem 1.4rem;
        border-radius: 18px;
        border: 1px solid rgba(120,120,120,0.15);
        background: linear-gradient(135deg, rgba(59,130,246,0.10), rgba(99,102,241,0.08));
        margin-bottom: 1rem;
    }

    .score-card {
        padding: 1rem;
        border-radius: 16px;
        border: 1px solid rgba(120,120,120,0.12);
        background: rgba(34,197,94,0.06);
        text-align: center;
        min-height: 120px;
    }

    .report-box {
        padding: 1.2rem;
        border-radius: 16px;
        border: 1px solid rgba(120,120,120,0.15);
        background: rgba(99,102,241,0.05);
        line-height: 1.7;
    }

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(120,120,120,0.10);
        padding: 0.8rem;
        border-radius: 14px;
    }

    .stButton > button {
        border-radius: 12px;
        padding: 0.65rem 1rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-card">
    <h1 style="margin-bottom:0;">🎓 NUC Accreditation Prediction System</h1>
</div>
""", unsafe_allow_html=True)

# =========================================================
# DATABASE
# =========================================================
DB_PATH = "nuc_app.db"


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            institution_name TEXT NOT NULL,
            discipline TEXT NOT NULL,
            programme_name TEXT NOT NULL,
            self_study_score REAL NOT NULL,
            predicted_status TEXT NOT NULL,
            actual_ratio REAL,
            core_pct REAL,
            phd_pct REAL,
            created_at TEXT NOT NULL,
            assessment_payload TEXT NOT NULL,
            report_text TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_user(full_name: str, email: str, password: str):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO users (full_name, email, password_hash, role, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                full_name,
                email.strip().lower(),
                hash_password(password),
                "user",
                datetime.utcnow().isoformat()
            )
        )
        conn.commit()
        return True, "Account creation is successful."
    except sqlite3.IntegrityError:
        return False, "An account with that email already exists."
    finally:
        conn.close()


def authenticate_user(email: str, password: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, full_name, email, role
        FROM users
        WHERE email = ? AND password_hash = ?
        """,
        (email.strip().lower(), hash_password(password))
    )
    row = cur.fetchone()
    conn.close()
    return row


def save_assessment(user_id: int, institution: str, discipline: str, programme: str,
                    self_study_score: float, predicted_status: str, actual_ratio: float,
                    core_pct: float, phd_pct: float, assessment_payload: str, report_text: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO assessments (
            user_id, institution_name, discipline, programme_name,
            self_study_score, predicted_status, actual_ratio, core_pct, phd_pct,
            created_at, assessment_payload, report_text
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id, institution, discipline, programme,
            self_study_score, predicted_status, actual_ratio, core_pct, phd_pct,
            datetime.utcnow().isoformat(), assessment_payload, report_text
        )
    )
    conn.commit()
    conn.close()


def get_user_assessments(user_id: int):
    conn = get_conn()
    df = pd.read_sql_query(
        """
        SELECT id, institution_name, discipline, programme_name,
               self_study_score, predicted_status, actual_ratio,
               core_pct, phd_pct, created_at
        FROM assessments
        WHERE user_id = ?
        ORDER BY datetime(created_at) DESC
        """,
        conn,
        params=(user_id,)
    )
    conn.close()
    return df


def get_user_report_history(user_id: int):
    conn = get_conn()
    df = pd.read_sql_query(
        """
        SELECT id, institution_name, discipline, programme_name,
               predicted_status, self_study_score, created_at, report_text
        FROM assessments
        WHERE user_id = ?
        ORDER BY datetime(created_at) DESC
        """,
        conn,
        params=(user_id,)
    )
    conn.close()
    return df


def get_all_users():
    conn = get_conn()
    df = pd.read_sql_query(
        """
        SELECT id, full_name, email, role, created_at
        FROM users
        ORDER BY datetime(created_at) DESC
        """,
        conn
    )
    conn.close()
    return df


def get_all_assessments():
    conn = get_conn()
    df = pd.read_sql_query(
        """
        SELECT id, user_id, institution_name, discipline, programme_name,
               self_study_score, predicted_status, created_at
        FROM assessments
        ORDER BY datetime(created_at) DESC
        """,
        conn
    )
    conn.close()
    return df

# =========================================================
# MODEL TRAINING
# =========================================================
@st.cache_resource
def train_model():
    df = pd.read_csv("nuc_dataset_22150_questionnaire_full.csv")

    target = "actual_accreditation_status"
    drop_cols = [
        "programme_id",
        "institution_name",
        "programme_name",
        "self_study_score",
        "academic_score",
        "staffing_score",
        "physical_facilities_score",
        "library_score",
        "funding_score",
        "research_score",
        target,
    ]

    X = df.drop(columns=drop_cols)
    y = df[target]

    le = LabelEncoder()
    y = le.fit_transform(y)

    X = pd.get_dummies(X, drop_first=True)
    training_columns = X.columns

    X_train, _, y_train, _ = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    lr = LogisticRegression(max_iter=1000)
    dt = DecisionTreeClassifier(random_state=42)
    rf = RandomForestClassifier(n_estimators=150, random_state=42)
    gb = GradientBoostingClassifier(random_state=42)

    ensemble = VotingClassifier(
        estimators=[("lr", lr), ("dt", dt), ("rf", rf), ("gb", gb)],
        voting="soft"
    )
    ensemble.fit(X_train, y_train)
    return ensemble, le, training_columns


model, label_encoder, training_columns = train_model()

# =========================================================
# OPENAI CLIENT
# =========================================================
client = None
if "OPENAI_API_KEY" in st.secrets:
    clean_key = st.secrets["OPENAI_API_KEY"]
    clean_key = clean_key.replace("\u200b", "").strip()
    clean_key = re.sub(r"[^\x00-\x7F]+", "", clean_key)
    if clean_key:
        client = OpenAI(api_key=clean_key)

# =========================================================
# SESSION STATE
# =========================================================
if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "Login"

# =========================================================
# MASTER DATA
# =========================================================
institutions = [
    "Abia State University", "Abubakar Tafawa Balewa University",
    "Adekunle Ajasin University", "Afe Babalola University",
    "Ahmadu Bello University", "Ajayi Crowther University",
    "American University of Nigeria", "Babcock University",
    "Bayero University Kano", "Benson Idahosa University",
    "Benue State University", "Bowen University", "Covenant University",
    "Delta State University", "Ekiti State University",
    "Federal University of Technology Akure",
    "Federal University of Technology Minna",
    "Federal University of Technology Owerri",
    "Igbinedion University", "Kaduna State University",
    "Kogi State University", "Lagos State University",
    "Lead City University", "Madonna University",
    "Nile University of Nigeria", "Nnamdi Azikiwe University",
    "Obafemi Awolowo University", "Pan Atlantic University",
    "Rivers State University", "University of Abuja",
    "University of Benin", "University of Calabar",
    "University of Ibadan", "University of Ilorin",
    "University of Jos", "University of Lagos",
    "University of Maiduguri", "University of Nigeria Nsukka",
    "University of Port Harcourt", "University of Uyo"
]

programmes = [
    "Accounting", "Adult Education", "Agricultural Engineering",
    "Banking and Finance", "Biochemistry", "Biology",
    "Biomedical Engineering", "Business Administration",
    "Chemical Engineering", "Chemistry", "Civil Engineering",
    "Computer Science", "Curriculum Studies", "Cybersecurity",
    "Data Science", "Economics", "Educational Management",
    "Electrical Engineering", "Geology", "Guidance and Counselling",
    "Information Technology", "Mathematics", "Mechanical Engineering",
    "Mechatronics Engineering", "Microbiology", "Petroleum Engineering",
    "Physics", "Public Administration", "Software Engineering", "Statistics"
]

disciplines = ["Computing", "Education", "Engineering", "Management", "Science"]

# =========================================================
# QUESTION OPTION BANKS
# =========================================================
PHILOSOPHY_OPTIONS = [
    {
        "label": "Clearly defined and similar to those laid down in the CCMAS for the programme",
        "score": 1.0,
    },
    {
        "label": "Not well stated/Not in line with those laid down in the CCMAS for the programme",
        "score": 0.0,
    },
]

RELATIONSHIP_CCMAS_OPTIONS = [
    {
        "label": "The curriculum is adequate for the degree programme as it contains all the core/compulsory courses prescribed by the CCMAS",
        "score": 1.0,
    },
    {
        "label": "Not fully adequate for the degree programme as a few core/compulsory courses are omitted in some levels of study as prescribed by the CCMAS",
        "score": 0.5,
    },
    {
        "label": "Not adequate for the degree programme as it does not contain all the core/compulsory courses across all the levels of study as prescribed by the CCMAS",
        "score": 0.0,
    },
]

INNOVATION_OPTIONS = [
    {
        "label": "Inclusion of four or more additional/innovative courses in the curriculum",
        "score": 1.0,
    },
    {
        "label": "Inclusion of less than four innovative courses in the curriculum",
        "score": 0.5,
    },
    {
        "label": "Non-inclusion of additional/innovative courses in the curriculum",
        "score": 0.0,
    },
]

COVERAGE_OPTIONS = [
    {"label": "The curriculum is adequately covered", "score": 1.0},
    {"label": "The curriculum is substantially covered", "score": 0.5},
    {"label": "The curriculum is not adequately covered", "score": 0.0},
]

ADMISSION_OPTIONS = [
    {
        "label": "All students enrolled in the programme meet the admission requirements",
        "score": 1.0,
    },
    {
        "label": "Some of the students enrolled in the programme did not meet the admission requirements",
        "score": 0.0,
    },
]

ACADEMIC_REG_OPTIONS = [
    {
        "label": "Available, quite clear, are in use and well publicized to students",
        "score": 1.0,
    },
    {
        "label": "Available, not clear, but in use and well publicized to students",
        "score": 0.5,
    },
    {
        "label": "Not available",
        "score": 0.0,
    },
]

TEST_EXAM_OPTIONS = [
    {
        "label": "Very good standard and quality and adequately cover the curriculum",
        "score": 1.0,
    },
    {
        "label": "Good standard and quality but do not cover the curriculum",
        "score": 0.5,
    },
    {
        "label": "Not of good standard and do not adequately cover the curriculum",
        "score": 0.0,
    },
]

EVALUATION_WORK_OPTIONS = [
    {
        "label": "Marking schemes exist, are well-developed and the grading of projects, CA, course work and exam scripts is consistent",
        "score": 1.0,
    },
    {
        "label": "Marking schemes exist, not well-developed and the grading of projects, CA, course work and exam scripts is not consistent",
        "score": 0.5,
    },
    {
        "label": "Marking schemes do not exist, and the grading of projects, CA, course work and exam script is poor and not consistent",
        "score": 0.0,
    },
]

DEGREE_PROJECT_OPTIONS = [
    {
        "label": "Good quality, well supervised, innovative topics and creative",
        "score": 1.0,
    },
    {
        "label": "Innovative and creative but not well supervised",
        "score": 0.5,
    },
    {
        "label": "Not well supervised, lack creativity and not innovative",
        "score": 0.0,
    },
]

PRACTICAL_WORK_OPTIONS = [
    {
        "label": "Practicals conducted, good quality, depth and scope covered",
        "score": 1.0,
    },
    {
        "label": "Practicals conducted, good quality but did not cover the curriculum",
        "score": 0.66,
    },
    {
        "label": "Practicals conducted but not of good quality",
        "score": 0.33,
    },
    {
        "label": "Practical not conducted",
        "score": 0.0,
    },
]

STUDENTS_COURSE_EVAL_OPTIONS = [
    {
        "label": "The course content, learning materials, course delivery, physical facilities are adequate",
        "score": 1.0,
    },
    {
        "label": "The course content, learning materials, course delivery, physical facilities are fairly adequate",
        "score": 0.5,
    },
    {
        "label": "The course content, learning materials, course delivery, physical facilities are not adequate",
        "score": 0.0,
    },
]

SKILLS_ACQUISITION_OPTIONS = [
    {
        "label": "Students demonstrate very good level of hard and soft skills relevant to the programme",
        "score": 1.0,
    },
    {
        "label": "Students demonstrate good level of hard and soft skills relevant to the programme",
        "score": 0.66,
    },
    {
        "label": "Students demonstrate average level of hard and soft skills relevant to the programme",
        "score": 0.33,
    },
    {
        "label": "Students demonstrate poor level of hard and soft skills relevant to the programme",
        "score": 0.0,
    },
]

EXTERNAL_EXAM_OPTIONS = [
    {
        "label": "External examiners system exists. Qualified assessors are engaged and the work done is of good standard",
        "score": 1.0,
    },
    {
        "label": "External examiners system exists. Qualified assessors are engaged but the work done is not of good standard",
        "score": 0.5,
    },
    {
        "label": "External examiners system exists but the quality of assessors engaged is poor OR external examiners system does not exist",
        "score": 0.0,
    },
]

IQA_OPTIONS = [
    {"label": "Exists and effective", "score": 1.0},
    {"label": "Exists not effective", "score": 0.5},
    {"label": "Does not exist", "score": 0.0},
]

COMPETENCE_OPTIONS = [
    {"label": "Competent", "score": 1.0},
    {"label": "Not competent", "score": 0.0},
]

ADMIN_OPTIONS = [
    {
        "label": "Run by a qualified academic staff (Senior Lecturer and above) and very effective and efficient",
        "score": 1.0,
    },
    {
        "label": "Run by a qualified academic staff (Senior Lecturer and above) and efficient",
        "score": 0.5,
    },
    {
        "label": "Run by an inexperienced academic and generally ineffective and inefficient",
        "score": 0.0,
    },
]

LAB_SPACE_OPTIONS = [
    {
        "label": "The space is adequate and meets the provisions of the NUC space standard by 70% or more",
        "score": 1.0,
    },
    {
        "label": "The space meets 60% but less than 70% of the NUC space standards",
        "score": 0.66,
    },
    {
        "label": "The space meets 50% but less than 60% of the NUC space standards",
        "score": 0.33,
    },
    {
        "label": "The space meets less than 50% of the NUC space standards",
        "score": 0.0,
    },
]

LAB_EQUIPMENT_OPTIONS = [
    {"label": "Available equipment are 80% or more", "score": 1.0},
    {"label": "70% but less than 80%", "score": 0.75},
    {"label": "60% but less than 70%", "score": 0.5},
    {"label": "50% but less than 60%", "score": 0.25},
    {"label": "Less than 50%", "score": 0.0},
]

CLASSROOM_SPACE_OPTIONS = [
    {
        "label": "Classroom space available meets the space standards specified in the CCMAS by 70% or more",
        "score": 1.0,
    },
    {"label": "60% but less than 70%", "score": 0.66},
    {"label": "50% but less than 60%", "score": 0.33},
    {"label": "Less than 50%", "score": 0.0},
]

CLASSROOM_EQUIPMENT_OPTIONS = [
    {"label": "Adequate and well maintained", "score": 1.0},
    {"label": "Adequate but not well maintained/slightly inadequate but well maintained", "score": 0.5},
    {"label": "Inadequate and not well maintained", "score": 0.0},
]

OFFICE_OPTIONS = [
    {"label": "Adequate in space and well equipped", "score": 1.0},
    {"label": "Slightly inadequate in space but well equipped", "score": 0.66},
    {"label": "Adequate in space but ill-equipped OR inadequate in space but well equipped", "score": 0.33},
    {"label": "Inadequate in space and ill-equipped or inappropriate", "score": 0.0},
]

SAFETY_OPTIONS = [
    {
        "label": "Safe and comply with all Government Laws relating to fire and environmental sanitation including adequate and functional toilet facilities",
        "score": 1.0,
    },
    {
        "label": "Reasonably safe and comply with most Government Laws relating to fire and environmental sanitation including some functional toilet facilities",
        "score": 0.5,
    },
    {
        "label": "Unsafe and violate Government Laws relating to fire and environmental sanitation including toilet facilities",
        "score": 0.0,
    },
]

LIBRARY_HOLDINGS_OPTIONS = [
    {
        "label": "Good quality and very relevant and adequate in number and coverage",
        "score": 1.0,
    },
    {
        "label": "Good quality and adequate in number and coverage",
        "score": 0.66,
    },
    {
        "label": "Inadequate in number, quality and coverage",
        "score": 0.33,
    },
    {
        "label": "Poor quality and inadequate in number and coverage",
        "score": 0.0,
    },
]

CURRENCY_OPTIONS = [
    {"label": "Very current for both recommended text and journals", "score": 1.0},
    {"label": "Very current for recommended text but current for journals or vice versa", "score": 0.75},
    {"label": "Current for recommended text and journals", "score": 0.5},
    {"label": "Current for recommended text but not for journals or vice versa", "score": 0.25},
    {"label": "Not current at all for both recommended text and journals", "score": 0.0},
]

E_LIBRARY_OPTIONS = [
    {
        "label": "Active subscription to at least 2 relevant databases in addition to open source materials",
        "score": 1.0,
    },
    {
        "label": "Active subscription to at least 1 relevant database in addition to open source materials",
        "score": 0.75,
    },
    {
        "label": "Access to only open source materials",
        "score": 0.5,
    },
    {
        "label": "Access to only offline materials",
        "score": 0.25,
    },
    {
        "label": "No subscription and no access to offline and open source materials",
        "score": 0.0,
    },
]

FUNDING_OPTIONS = [
    {"label": "Very adequate", "score": 1.0},
    {"label": "Adequate", "score": 0.66},
    {"label": "Inadequate", "score": 0.33},
    {"label": "Poor", "score": 0.0},
]

RESEARCH_COLLAB_OPTIONS = [
    {"label": "Available, multidisciplinary approach engaged", "score": 1.0},
    {"label": "Available, no multidisciplinary approach, result applied", "score": 0.66},
    {"label": "Available only", "score": 0.33},
    {"label": "Not available at all", "score": 0.0},
]

TRACER_OPTIONS = [
    {
        "label": "Tracer system is in place and graduates’ performance on the job is very good",
        "score": 1.0,
    },
    {
        "label": "Tracer system not in place but graduates’ performance on the job is good or vice versa",
        "score": 0.5,
    },
    {
        "label": "Tracer system not in place and performance below average",
        "score": 0.0,
    },
]

TRACER_NO_GRAD_OPTIONS = [
    {"label": "Very good", "score": 1.0},
    {"label": "Average", "score": 0.5},
    {"label": "Below average", "score": 0.0},
]

# =========================================================
# HELPERS
# =========================================================
def ask_scored_question(label: str, options: list, key: str):
    option_labels = [opt["label"] for opt in options]
    selected = st.selectbox(
        label,
        option_labels,
        index=None,
        placeholder="Select an option",
        key=key,
    )
    if selected is None:
        return None
    for opt in options:
        if opt["label"] == selected:
            return opt["score"]
    return None


def pct(numerator: int, denominator: int) -> float:
    return 0.0 if denominator <= 0 else (numerator / denominator) * 100


def normalized_from_score(score: int, max_score: int) -> float:
    if max_score <= 0:
        return 0.0
    ratio = score / max_score
    if ratio >= 0.75:
        return 1.0
    if ratio >= 0.4:
        return 0.5
    return 0.0


def calc_score(section: dict):
    values = list(section.values())
    if not values or any(v is None for v in values):
        return None
    return (sum(values) / len(values)) * 100


def display_score_card(title: str, value):
    display_value = "—" if value is None else f"{value:.2f}%"
    st.markdown(
        f'<div class="score-card"><h4>{title}</h4><h2>{display_value}</h2></div>',
        unsafe_allow_html=True
    )


def get_feature_importance(_model, _training_columns):
    try:
        base_model = _model.named_estimators_["rf"]
    except Exception:
        return pd.DataFrame(columns=["feature", "importance"])

    return pd.DataFrame({
        "feature": _training_columns,
        "importance": base_model.feature_importances_
    }).sort_values(by="importance", ascending=False)


def inputs_complete(values):
    return all(v is not None for v in values)

# =========================================================
# STAFFING CALCULATION ENGINE
# =========================================================
def score_staff_student_ratio(staff_count: int, student_count: int):
    if staff_count is None or student_count is None or staff_count <= 0:
        return None, None, None
    actual_ratio = round(student_count / staff_count)
    if actual_ratio <= 20:
        score = 4
    elif actual_ratio <= 25:
        score = 3
    elif actual_ratio <= 30:
        score = 2
    elif actual_ratio <= 35:
        score = 1
    else:
        score = 0
    return score, actual_ratio, normalized_from_score(score, 4)


def score_core_staff(core_staff_count: int, staff_count: int):
    if core_staff_count is None or staff_count is None or staff_count <= 0:
        return None, None, None
    core_pct = pct(core_staff_count, staff_count)
    if core_pct >= 75:
        score = 6
    elif core_pct >= 60:
        score = 4
    elif core_pct >= 50:
        score = 2
    else:
        score = 0
    return score, core_pct, normalized_from_score(score, 6)


def score_staff_mix_by_rank(prof_count: int, senior_count: int, lect1_below_count: int):
    if prof_count is None or senior_count is None or lect1_below_count is None:
        return None, {"prof_pct": None, "senior_pct": None, "others_pct": None}, None

    total = prof_count + senior_count + lect1_below_count
    if total <= 0:
        return None, {"prof_pct": None, "senior_pct": None, "others_pct": None}, None

    prof_pct = round(pct(prof_count, total))
    senior_pct = round(pct(senior_count, total))
    others_pct = 100 - prof_pct - senior_pct

    prof_ok = abs(prof_pct - 20) <= 2
    senior_ok = abs(senior_pct - 35) <= 2
    others_ok = abs(others_pct - 45) <= 2
    categories_met = sum([prof_ok, senior_ok, others_ok])

    if categories_met == 3:
        score = 5
    elif categories_met >= 1:
        score = 3
    else:
        score = 0

    return score, {
        "prof_pct": prof_pct,
        "senior_pct": senior_pct,
        "others_pct": others_pct,
    }, normalized_from_score(score, 5)


def score_phd_qualification(phd_count: int, core_staff_count: int):
    if phd_count is None or core_staff_count is None or core_staff_count <= 0:
        return None, None, None
    phd_pct = pct(phd_count, core_staff_count)
    if phd_pct >= 70:
        score = 6
    elif phd_pct >= 60:
        score = 4
    elif phd_pct >= 50:
        score = 2
    else:
        score = 0
    return score, phd_pct, normalized_from_score(score, 6)


def score_academic_staff_dev(trained_count: int, academic_staff_count: int):
    if trained_count is None or academic_staff_count is None or academic_staff_count <= 0:
        return None, None, None
    dev_pct = pct(trained_count, academic_staff_count)
    if dev_pct >= 70:
        score = 5
    elif dev_pct >= 60:
        score = 3
    elif dev_pct >= 50:
        score = 1
    else:
        score = 0
    return score, dev_pct, normalized_from_score(score, 5)


def score_non_teaching_staff(status_choice: str):
    if status_choice is None:
        return None, None
    mapping = {
        "Adequate in number and quality": (3, 1.0),
        "Not adequate in number but of good quality": (2, 0.5),
        "Inadequate in number and of poor quality": (0, 0.0),
    }
    return mapping[status_choice]


def score_non_academic_staff_dev(trained_count: int, non_academic_staff_count: int):
    if trained_count is None or non_academic_staff_count is None or non_academic_staff_count <= 0:
        return None, None, None
    dev_pct = pct(trained_count, non_academic_staff_count)
    if dev_pct >= 70:
        score = 2
    elif dev_pct >= 50:
        score = 1
    else:
        score = 0
    return score, dev_pct, normalized_from_score(score, 2)

# =========================================================
# REPORT CLEANER
# =========================================================
def clean_report_text(text: str) -> str:
    banned_phrases = [
        "Please let me know if you require assistance with specific sections or further elaboration.",
        "Please let me know if you need assistance with specific sections or further elaboration.",
        "Please let me know if you need any further assistance.",
        "Let me know if you need anything else.",
        "Please let me know if you need anything else.",
    ]
    cleaned = text
    for phrase in banned_phrases:
        cleaned = cleaned.replace(phrase, "")
    return cleaned.strip()

# =========================================================
# ADVISORY GENERATOR
# =========================================================
def generate_advisory_report(
    institution: str,
    programme: str,
    discipline: str,
    self_study_score: float,
    predicted_status: str,
    actual_ratio: int,
    ratio_score_raw: int,
    core_pct: float,
    core_score_raw: int,
    mix_score_raw: int,
    phd_pct: float,
    phd_score_raw: int,
    acad_dev_pct: float,
    acad_dev_score_raw: int,
    non_teach_score_raw: int,
    non_acad_dev_pct: float,
    non_acad_dev_score_raw: int,
    top_weaknesses: str,
) -> str:
    if client is None:
        return "OpenAI API key is not configured, so the personalized advisory report cannot be generated."

    prompt = f"""
You are an accreditation advisory expert.

Prepare a well-formatted accreditation readiness report using markdown headings and bullet points.

Institution: {institution}
Programme: {programme}
Discipline: {discipline}

Programme Score: {round(self_study_score, 2)}%
Predicted Accreditation Status: {predicted_status}

Calculated staffing indicators:
- Staff to Student Ratio: 1:{actual_ratio}
- Staff to Student Ratio Score: {ratio_score_raw}/4
- Core Staff Percentage: {round(core_pct, 2)}%
- Core Staff Score: {core_score_raw}/6
- Staff Mix by Rank Score: {mix_score_raw}/5
- PhD Holders Percentage: {round(phd_pct, 2)}%
- Qualifications of Teaching Staff Score: {phd_score_raw}/6
- Academic Staff Development Percentage: {round(acad_dev_pct, 2)}%
- Academic Staff Development Score: {acad_dev_score_raw}/5
- Non-Teaching Staff Score: {non_teach_score_raw}/3
- Non-Academic Staff Development Percentage: {round(non_acad_dev_pct, 2)}%
- Non-Academic Staff Development Score: {non_acad_dev_score_raw}/2

High-impact weaknesses:
{top_weaknesses}

Format the report using exactly these sections:

## Executive Summary
## Key High-Impact Weaknesses
## Section-by-Section Improvement Plan
## Documentation Checklist
## Risk Mitigation Priorities

Requirements:
- Be specific and practical
- Use concise bullet points under each heading
- Do not add filler text
- Do not end with any offer of further help
- Do not include any sentence like “Please let me know if you need anything else”
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are an accreditation advisory expert and must return neatly formatted markdown."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
    )
    return clean_report_text(response.choices[0].message.content)

# =========================================================
# AUTH PAGES
# =========================================================
def render_login():
    st.subheader("Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Login", use_container_width=True):
            user = authenticate_user(email, password)
            if user:
                st.session_state.user = {
                    "id": user[0],
                    "full_name": user[1],
                    "email": user[2],
                    "role": user[3],
                }
                st.session_state.page = "New Assessment"
                st.rerun()
            else:
                st.error("Invalid email or password.")
    with c2:
        if st.button("Go to Signup", use_container_width=True):
            st.session_state.page = "Signup"
            st.rerun()


def render_signup():
    st.subheader("Create Account")
    full_name = st.text_input("Full Name", key="signup_name")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Create Account", use_container_width=True):
            if not full_name or not email or not password:
                st.error("Please complete all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                ok, msg = create_user(full_name, email, password)
                if ok:
                    st.success(msg)
                    st.session_state.page = "Login"
                    st.rerun()
                else:
                    st.error(msg)
    with c2:
        if st.button("Back to Login", use_container_width=True):
            st.session_state.page = "Login"
            st.rerun()

# =========================================================
# PRE-LOGIN
# =========================================================
if st.session_state.user is None:
    auth_tab1, auth_tab2 = st.tabs(["Login", "Signup"])
    with auth_tab1:
        render_login()
    with auth_tab2:
        render_signup()
    st.stop()

# =========================================================
# SIDEBAR NAV
# =========================================================
with st.sidebar:
    st.markdown(f"### Welcome, {st.session_state.user['full_name']}")
    st.caption(st.session_state.user["email"])

    nav_options = ["New Assessment", "Saved Assessments", "Report History"]
    if st.session_state.user.get("role") == "admin":
        nav_options = ["New Assessment", "Saved Assessments", "Report History", "Admin Dashboard"]

    choice = st.radio("Navigation", nav_options)
    st.session_state.page = choice

    if st.button("Logout", use_container_width=True):
        st.session_state.user = None
        st.session_state.page = "Login"
        st.rerun()

# =========================================================
# NEW ASSESSMENT
# =========================================================
if st.session_state.page == "New Assessment":
    st.header("New Assessment")

    c1, c2, c3 = st.columns(3)
    with c1:
        institution = st.selectbox("Name of Institution", institutions, index=None, placeholder="Select institution")
    with c2:
        discipline = st.selectbox("Discipline", disciplines, index=None, placeholder="Select discipline")
    with c3:
        programme = st.selectbox("Programme", programmes, index=None, placeholder="Select programme")

    st.subheader("Staffing & Enrollment Data")

    s1, s2, s3 = st.columns(3)
    with s1:
        academic_staff_count = st.number_input("Number of academic staff", min_value=1, value=None, placeholder="Enter value")
    with s2:
        student_count = st.number_input("Number of students", min_value=1, value=None, placeholder="Enter value")
    with s3:
        core_staff_count = st.number_input("Number of academic staff core to the subject area", min_value=0, value=None, placeholder="Enter value")

    s4, s5, s6 = st.columns(3)
    with s4:
        professor_reader_count = st.number_input("Number of Professors/Readers", min_value=0, value=None, placeholder="Enter value")
    with s5:
        senior_lecturer_count = st.number_input("Number of Senior Lecturers", min_value=0, value=None, placeholder="Enter value")
    with s6:
        lecturer1_below_count = st.number_input("Number of Lecturers I and below", min_value=0, value=None, placeholder="Enter value")

    s7, s8, s9 = st.columns(3)
    with s7:
        phd_holder_count = st.number_input("Number of Ph.D Holders", min_value=0, value=None, placeholder="Enter value")
    with s8:
        academic_staff_dev_count = st.number_input("Number of academic staff with staff development programme", min_value=0, value=None, placeholder="Enter value")
    with s9:
        non_academic_staff_count = st.number_input("Number of non-teaching staff", min_value=0, value=None, placeholder="Enter value")

    non_academic_staff_dev_count = st.number_input(
        "Number of non-academic staff with staff development programme",
        min_value=0,
        value=None,
        placeholder="Enter value"
    )

    non_teaching_quality_choice = st.selectbox(
        "Non-Teaching Staff",
        [
            "Adequate in number and quality",
            "Not adequate in number but of good quality",
            "Inadequate in number and of poor quality",
        ],
        index=None,
        placeholder="Select status"
    )

    staffing_inputs_complete = inputs_complete([
        academic_staff_count, student_count, core_staff_count,
        professor_reader_count, senior_lecturer_count, lecturer1_below_count,
        phd_holder_count, academic_staff_dev_count,
        non_academic_staff_count, non_academic_staff_dev_count,
        non_teaching_quality_choice
    ])

    if staffing_inputs_complete:
        ratio_score_raw, actual_ratio, staff_ratio_feature = score_staff_student_ratio(
            academic_staff_count, student_count
        )
        core_score_raw, core_pct, core_staff_feature = score_core_staff(
            core_staff_count, academic_staff_count
        )
        mix_score_raw, mix_pct_dict, staff_mix_feature = score_staff_mix_by_rank(
            professor_reader_count, senior_lecturer_count, lecturer1_below_count
        )
        phd_score_raw, phd_pct, phd_feature = score_phd_qualification(
            phd_holder_count, core_staff_count
        )
        acad_dev_score_raw, acad_dev_pct, acad_dev_feature = score_academic_staff_dev(
            academic_staff_dev_count, academic_staff_count
        )
        non_teach_score_raw, non_teach_feature = score_non_teaching_staff(non_teaching_quality_choice)
        non_acad_dev_score_raw, non_acad_dev_pct, non_acad_dev_feature = score_non_academic_staff_dev(
            non_academic_staff_dev_count, non_academic_staff_count
        )

        with st.expander("Computed Staffing Indicators", expanded=True):
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Staff to Student Ratio", f"1 : {actual_ratio}")
                st.metric("Staff to Student Ratio Score", f"{ratio_score_raw}/4")
            with m2:
                st.metric("Percentage of Staff Core to the Subject Area", f"{round(core_pct, 2)}%")
                st.metric("Proportion of Staff Core to the Subject Area Score", f"{core_score_raw}/6")
            with m3:
                st.metric("Ph.D Holders Percentage", f"{round(phd_pct, 2)}%")
                st.metric("Qualifications of Teaching Staff Score", f"{phd_score_raw}/6")

            m4, m5, m6 = st.columns(3)
            with m4:
                st.metric(
                    "Staff Mix by Rank",
                    f"{mix_pct_dict['prof_pct']}:{mix_pct_dict['senior_pct']}:{mix_pct_dict['others_pct']}"
                )
                st.metric("Staff Mix by Rank Score", f"{mix_score_raw}/5")
            with m5:
                st.metric("Academic Staff Development Percentage", f"{round(acad_dev_pct, 2)}%")
                st.metric("Academic Staff Development Score", f"{acad_dev_score_raw}/5")
            with m6:
                st.metric("Non-Academic Staff Development Percentage", f"{round(non_acad_dev_pct, 2)}%")
                st.metric("Non-Academic Staff Development Score", f"{non_acad_dev_score_raw}/2")

            st.metric("Non-Teaching Staff Score", f"{non_teach_score_raw}/3")
    else:
        ratio_score_raw = actual_ratio = staff_ratio_feature = None
        core_score_raw = core_pct = core_staff_feature = None
        mix_score_raw = staff_mix_feature = None
        mix_pct_dict = {"prof_pct": None, "senior_pct": None, "others_pct": None}
        phd_score_raw = phd_pct = phd_feature = None
        acad_dev_score_raw = acad_dev_pct = acad_dev_feature = None
        non_teach_score_raw = non_teach_feature = None
        non_acad_dev_score_raw = non_acad_dev_pct = non_acad_dev_feature = None
        st.info("Enter all staffing and enrollment figures to compute staffing indicators.")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Academic Content",
        "Staffing",
        "Physical Facilities",
        "Library",
        "Funding",
        "Research and Collaboration",
        "Tracer and Employers’ Rating",
    ])

    with tab1:
        academic = {
            "philosophy_objectives_defined": ask_scored_question(
                "Philosophy and Objectives of the Programme",
                PHILOSOPHY_OPTIONS,
                "a0"
            ),
            "curriculum_aligned_with_BMAS": ask_scored_question(
                "Relationship between CCMAS and Curriculum",
                RELATIONSHIP_CCMAS_OPTIONS,
                "a1"
            ),
            "innovative_courses_present": ask_scored_question(
                "Innovation (Additional Courses)",
                INNOVATION_OPTIONS,
                "a2"
            ),
            "curriculum_coverage_complete": ask_scored_question(
                "Coverage of the Curriculum",
                COVERAGE_OPTIONS,
                "a3"
            ),
            "admission_requirements_compliant": ask_scored_question(
                "Admission Requirements into the Programme",
                ADMISSION_OPTIONS,
                "a4"
            ),
            "academic_regulations_defined": ask_scored_question(
                "Academic Regulations",
                ACADEMIC_REG_OPTIONS,
                "a5"
            ),
            "tests_and_examinations_standardized": ask_scored_question(
                "Standard of Tests and Examinations",
                TEST_EXAM_OPTIONS,
                "a6"
            ),
            "evaluation_methods_clear": ask_scored_question(
                "Evaluation of Students’ Work",
                EVALUATION_WORK_OPTIONS,
                "a7"
            ),
            "degree_projects_adequate": ask_scored_question(
                "Degree Projects",
                DEGREE_PROJECT_OPTIONS,
                "a8"
            ),
            "practical_work_adequate": ask_scored_question(
                "Practical Work",
                PRACTICAL_WORK_OPTIONS,
                "a9"
            ),
            "student_course_evaluation_present": ask_scored_question(
                "Students’ Course Evaluation",
                STUDENTS_COURSE_EVAL_OPTIONS,
                "a10"
            ),
            "skills_acquisition_programme": ask_scored_question(
                "Evaluation of Skills Acquisition",
                SKILLS_ACQUISITION_OPTIONS,
                "a11"
            ),
            "external_examiner_system": ask_scored_question(
                "External Examination System",
                EXTERNAL_EXAM_OPTIONS,
                "a12"
            ),
            "internal_quality_assurance": ask_scored_question(
                "Internal Quality Assurance System",
                IQA_OPTIONS,
                "a13"
            ),
        }

    with tab2:
        staffing = {
            "proportion_core_staff_sufficient": core_staff_feature,
            "staff_rank_mix_balanced": staff_mix_feature,
            "academic_staff_qualification_high": phd_feature,
            "staff_competence_verified": ask_scored_question(
                "Competence of Teaching Staff",
                COMPETENCE_OPTIONS,
                "s1"
            ),
            "administrative_support_available": ask_scored_question(
                "Administration of College/School/Faculty/Department",
                ADMIN_OPTIONS,
                "s2"
            ),
            "non_teaching_staff_adequate": non_teach_feature,
            "academic_staff_development_programme": acad_dev_feature,
            "non_academic_staff_development_programme": non_acad_dev_feature,
        }
        st.info("Calculated staffing items are automatically derived from the figures entered above.")

    with tab3:
        facilities = {
            "laboratory_space_adequate": ask_scored_question(
                "Laboratories/Clinics/Studios/Farms/Museums",
                LAB_SPACE_OPTIONS,
                "f1"
            ),
            "laboratory_equipment_adequate": ask_scored_question(
                "Laboratory Equipment",
                LAB_EQUIPMENT_OPTIONS,
                "f2"
            ),
            "classroom_space_adequate": ask_scored_question(
                "Classrooms/Lecture Theatres",
                CLASSROOM_SPACE_OPTIONS,
                "f3"
            ),
            "classroom_equipment_adequate": ask_scored_question(
                "Classroom Equipment",
                CLASSROOM_EQUIPMENT_OPTIONS,
                "f4"
            ),
            "office_accommodation_adequate": ask_scored_question(
                "Office Accommodation",
                OFFICE_OPTIONS,
                "f5"
            ),
            "safety_environment_present": ask_scored_question(
                "Safety and Environment",
                SAFETY_OPTIONS,
                "f6"
            ),
        }

    with tab4:
        library = {
            "library_holdings_adequate": ask_scored_question(
                "Holdings",
                LIBRARY_HOLDINGS_OPTIONS,
                "l1"
            ),
            "library_material_current": ask_scored_question(
                "Currency of Holdings",
                CURRENCY_OPTIONS,
                "l2"
            ),
            "e_library_subscription_available": ask_scored_question(
                "Subscription to e-Books and e-Journals",
                E_LIBRARY_OPTIONS,
                "l3"
            ),
            "e_library_access_good": ask_scored_question(
                "Access to available e-Books and e-Journals",
                E_LIBRARY_OPTIONS,
                "l4"
            ),
        }

    with tab5:
        funding = {
            "programme_funding_adequate": ask_scored_question(
                "Funding",
                FUNDING_OPTIONS,
                "fd0"
            ),
            "budget_release_regular": 1.0,
            "equipment_maintenance_budget_available": 1.0,
        }

    with tab6:
        research_collaboration = {
            "research_collaboration_active": ask_scored_question(
                "Research and Collaboration",
                RESEARCH_COLLAB_OPTIONS,
                "r1"
            ),
            "research_output_present": 1.0,
        }

    with tab7:
        has_graduated_students = st.selectbox(
            "Has the programme graduated students?",
            ["Yes", "No"],
            index=None,
            placeholder="Select an option",
            key="graduated_students"
        )

        tracer_options = None
        if has_graduated_students == "Yes":
            tracer_options = TRACER_OPTIONS
        elif has_graduated_students == "No":
            tracer_options = TRACER_NO_GRAD_OPTIONS

        tracer_rating = {
            "employer_rating_positive": ask_scored_question(
                "Tracer and Employers’ Rating",
                tracer_options,
                "t1"
            ) if tracer_options else None,
            "tracer_study_available": 1.0 if has_graduated_students == "Yes" else 0.5 if has_graduated_students == "No" else None,
        }

    academic_score = calc_score(academic)

    staffing_display_items = {
        "staff_student_ratio_compliant": staff_ratio_feature,
        "proportion_core_staff_sufficient": core_staff_feature,
        "staff_rank_mix_balanced": staff_mix_feature,
        "academic_staff_qualification_high": phd_feature,
        "staff_competence_verified": staffing["staff_competence_verified"],
        "administrative_support_available": staffing["administrative_support_available"],
        "non_teaching_staff_adequate": non_teach_feature,
        "academic_staff_development_programme": acad_dev_feature,
        "non_academic_staff_development_programme": non_acad_dev_feature,
    }

    staffing_score = calc_score(staffing_display_items)
    physical_facilities_score = calc_score(facilities)
    library_score = calc_score(library)
    funding_score = calc_score(funding)
    research_collaboration_score = calc_score(research_collaboration)
    tracer_employers_score = calc_score(tracer_rating)

    if all(v is not None for v in [
        academic_score, staffing_score, physical_facilities_score,
        library_score, funding_score, research_collaboration_score,
        tracer_employers_score
    ]):
        self_study_score = (
            academic_score * 0.25 +
            staffing_score * 0.25 +
            physical_facilities_score * 0.15 +
            library_score * 0.10 +
            funding_score * 0.10 +
            research_collaboration_score * 0.10 +
            tracer_employers_score * 0.05
        )
    else:
        self_study_score = None

    st.subheader("Predict Accreditation Status")

    required_basic = inputs_complete([institution, discipline, programme])
    required_all_sections = all(v is not None for v in [
        academic_score, staffing_score, physical_facilities_score,
        library_score, funding_score, research_collaboration_score,
        tracer_employers_score, self_study_score
    ])

    if st.button("Predict Accreditation Status", type="primary", use_container_width=True):
        if not required_basic:
            st.error("Please complete the institutional information section.")
            st.stop()

        if not staffing_inputs_complete:
            st.error("Please complete all staffing and enrollment inputs.")
            st.stop()

        if not required_all_sections:
            st.error("Please complete all assessment sections before generating the result.")
            st.stop()

        input_data = {}
        input_data.update(academic)
        input_data.update(staffing)
        input_data.update(facilities)
        input_data.update(library)
        input_data.update(funding)
        input_data.update(research_collaboration)
        input_data.update(tracer_rating)
        input_data["staff_student_ratio_compliant"] = staff_ratio_feature
        input_data["discipline"] = discipline

        input_df = pd.DataFrame([input_data])
        input_encoded = pd.get_dummies(input_df)
        input_encoded = input_encoded.reindex(columns=training_columns, fill_value=0)

        prediction = model.predict(input_encoded)
        predicted_status = label_encoder.inverse_transform(prediction)[0]

        st.subheader("Section Scores")

        row1 = st.columns(4)
        row2 = st.columns(4)

        with row1[0]:
            display_score_card("Academic Content", academic_score)
        with row1[1]:
            display_score_card("Staffing", staffing_score)
        with row1[2]:
            display_score_card("Physical Facilities", physical_facilities_score)
        with row1[3]:
            display_score_card("Library", library_score)

        with row2[0]:
            display_score_card("Funding", funding_score)
        with row2[1]:
            display_score_card("Research and Collaboration", research_collaboration_score)
        with row2[2]:
            display_score_card("Tracer and Employers’ Rating", tracer_employers_score)
        with row2[3]:
            display_score_card("Programme Score", self_study_score)

        st.subheader("Predicted Accreditation Outcome")
        st.success(predicted_status)

        importance_df = get_feature_importance(model, training_columns)
        weak = []
        for col in input_df.columns:
            if col in importance_df["feature"].values:
                value = input_df[col].iloc[0]
                if value in [0.0, 0.5]:
                    impact = importance_df.loc[
                        importance_df["feature"] == col,
                        "importance"
                    ].values[0]
                    weak.append((col, value, impact))

        weak = sorted(weak, key=lambda x: x[2], reverse=True)

        if weak:
            st.subheader("Top High-Impact Weak Areas")
            weak_df = pd.DataFrame([
                {
                    "Feature": w[0].replace("_", " ").title(),
                    "Severity": "Critical" if w[1] == 0.0 else "Moderate",
                    "Importance": round(float(w[2]), 4),
                }
                for w in weak[:10]
            ])
            st.dataframe(weak_df, use_container_width=True)
            top_weaknesses = "\n".join(
                [f"- {w[0].replace('_', ' ').title()}" for w in weak[:10]]
            )
        else:
            top_weaknesses = "- No major weaknesses were detected from the submitted responses."
            st.info("No major weaknesses were detected from the submitted responses.")

        with st.spinner("Generating personalized advisory report..."):
            report = generate_advisory_report(
                institution=institution,
                programme=programme,
                discipline=discipline,
                self_study_score=self_study_score,
                predicted_status=predicted_status,
                actual_ratio=actual_ratio,
                ratio_score_raw=ratio_score_raw,
                core_pct=core_pct,
                core_score_raw=core_score_raw,
                mix_score_raw=mix_score_raw,
                phd_pct=phd_pct,
                phd_score_raw=phd_score_raw,
                acad_dev_pct=acad_dev_pct,
                acad_dev_score_raw=acad_dev_score_raw,
                non_teach_score_raw=non_teach_score_raw,
                non_acad_dev_pct=non_acad_dev_pct,
                non_acad_dev_score_raw=non_acad_dev_score_raw,
                top_weaknesses=top_weaknesses,
            )

        st.subheader("Personalized Accreditation Advisory Report")
        st.markdown(f'<div class="report-box">{report}</div>', unsafe_allow_html=True)

        save_assessment(
            user_id=st.session_state.user["id"],
            institution=institution,
            discipline=discipline,
            programme=programme,
            self_study_score=float(self_study_score),
            predicted_status=predicted_status,
            actual_ratio=float(actual_ratio),
            core_pct=float(core_pct),
            phd_pct=float(phd_pct),
            assessment_payload=json.dumps(input_data),
            report_text=report,
        )

        st.success("Assessment and report saved successfully.")

# =========================================================
# SAVED ASSESSMENTS
# =========================================================
elif st.session_state.page == "Saved Assessments":
    st.header("Saved Assessments")
    df_assessments = get_user_assessments(st.session_state.user["id"])

    if df_assessments.empty:
        st.info("No saved assessments yet.")
    else:
        st.dataframe(df_assessments, use_container_width=True)

# =========================================================
# REPORT HISTORY
# =========================================================
elif st.session_state.page == "Report History":
    st.header("Report History")
    df_reports = get_user_report_history(st.session_state.user["id"])

    if df_reports.empty:
        st.info("No report history yet.")
    else:
        for _, row in df_reports.iterrows():
            title = f"{row['institution_name']} | {row['programme_name']} | {row['predicted_status']} | {row['created_at']}"
            with st.expander(title):
                st.write(f"**Programme Score:** {row['self_study_score']:.2f}%")
                st.markdown(f'<div class="report-box">{row["report_text"]}</div>', unsafe_allow_html=True)

# =========================================================
# ADMIN DASHBOARD
# =========================================================
elif st.session_state.page == "Admin Dashboard" and st.session_state.user.get("role") == "admin":
    st.header("Admin Dashboard")

    users_df = get_all_users()
    assessments_df = get_all_assessments()

    d1, d2, d3 = st.columns(3)
    with d1:
        st.metric("Total Users", len(users_df))
    with d2:
        st.metric("Total Assessments", len(assessments_df))
    with d3:
        if not assessments_df.empty:
            st.metric("Average Programme Score", f"{assessments_df['self_study_score'].mean():.2f}%")
        else:
            st.metric("Average Programme Score", "0.00%")

    st.subheader("Users")
    st.dataframe(users_df, use_container_width=True)

    st.subheader("All Assessments")
    st.dataframe(assessments_df, use_container_width=True)
