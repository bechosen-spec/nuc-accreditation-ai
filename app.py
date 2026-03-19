# import streamlit as st
# import pandas as pd
# from openai import OpenAI

# from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import LabelEncoder
# from sklearn.linear_model import LogisticRegression
# from sklearn.tree import DecisionTreeClassifier
# from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
# from sklearn.ensemble import VotingClassifier


# # =========================================================
# # PAGE CONFIG
# # =========================================================
# st.set_page_config(page_title="NUC Accreditation AI", layout="wide")
# st.title("🎓 NUC Accreditation Readiness & Advisory System")

# # =========================================================
# # LOAD MODEL
# # =========================================================
# # model = joblib.load("final_nuc_accreditation_model.pkl")
# # label_encoder = joblib.load("label_encoder.pkl")
# # training_columns = joblib.load("training_columns.pkl")

# @st.cache_resource
# def train_model():

#     # Load dataset
#     df = pd.read_csv("nuc_dataset_22150_questionnaire_full.csv")

#     target = "actual_accreditation_status"

#     drop_cols = [
#         "programme_id",
#         "institution_name",
#         "programme_name",

#         # prevent leakage
#         "self_study_score",
#         "academic_score",
#         "staffing_score",
#         "physical_facilities_score",
#         "library_score",
#         "funding_score",
#         "research_score",

#         target
#     ]

#     # Features and target
#     X = df.drop(columns=drop_cols)
#     y = df[target]

#     # Encode target
#     le = LabelEncoder()
#     y = le.fit_transform(y)

#     # One-hot encode features
#     X = pd.get_dummies(X, drop_first=True)

#     # Save training columns for inference alignment
#     training_columns = X.columns

#     # Train-test split
#     X_train, X_test, y_train, y_test = train_test_split(
#         X,
#         y,
#         test_size=0.2,
#         random_state=42,
#         stratify=y
#     )

#     # Base models
#     lr = LogisticRegression(max_iter=1000)
#     dt = DecisionTreeClassifier()
#     rf = RandomForestClassifier(n_estimators=150)
#     gb = GradientBoostingClassifier()

#     # Ensemble model
#     ensemble = VotingClassifier(
#         estimators=[
#             ('lr', lr),
#             ('dt', dt),
#             ('rf', rf),
#             ('gb', gb)
#         ],
#         voting='soft'
#     )

#     ensemble.fit(X_train, y_train)

#     return ensemble, le, training_columns


# # Train model once
# model, label_encoder, training_columns = train_model()

# clean_key = st.secrets["OPENAI_API_KEY"]
# clean_key = clean_key.replace("\u200b", "").strip()

# client = OpenAI(api_key=clean_key)

# # =========================================================
# # REAL DATA LISTS
# # =========================================================
# institutions = ['Abia State University', 'Abubakar Tafawa Balewa University',
# 'Adekunle Ajasin University', 'Afe Babalola University',
# 'Ahmadu Bello University', 'Ajayi Crowther University',
# 'American University of Nigeria', 'Babcock University',
# 'Bayero University Kano', 'Benson Idahosa University',
# 'Benue State University', 'Bowen University', 'Covenant University',
# 'Delta State University', 'Ekiti State University',
# 'Federal University of Technology Akure',
# 'Federal University of Technology Minna',
# 'Federal University of Technology Owerri',
# 'Igbinedion University', 'Kaduna State University',
# 'Kogi State University', 'Lagos State University',
# 'Lead City University', 'Madonna University',
# 'Nile University of Nigeria', 'Nnamdi Azikiwe University',
# 'Obafemi Awolowo University', 'Pan Atlantic University',
# 'Rivers State University', 'University of Abuja',
# 'University of Benin', 'University of Calabar',
# 'University of Ibadan', 'University of Ilorin',
# 'University of Jos', 'University of Lagos',
# 'University of Maiduguri', 'University of Nigeria Nsukka',
# 'University of Port Harcourt', 'University of Uyo']

# programmes = ['Accounting', 'Adult Education', 'Agricultural Engineering',
# 'Banking and Finance', 'Biochemistry', 'Biology',
# 'Biomedical Engineering', 'Business Administration',
# 'Chemical Engineering', 'Chemistry', 'Civil Engineering',
# 'Computer Science', 'Curriculum Studies', 'Cybersecurity',
# 'Data Science', 'Economics', 'Educational Management',
# 'Electrical Engineering', 'Geology', 'Guidance and Counselling',
# 'Information Technology', 'Mathematics',
# 'Mechanical Engineering', 'Mechatronics Engineering',
# 'Microbiology', 'Petroleum Engineering', 'Physics',
# 'Public Administration', 'Software Engineering', 'Statistics']

# disciplines = ['Computing', 'Education', 'Engineering', 'Management', 'Science']


# # =========================================================
# # BASIC INFORMATION
# # =========================================================
# st.header("🏛 Institutional Information")

# institution = st.selectbox("Select Institution", institutions)
# programme = st.selectbox("Select Programme", programmes)
# discipline = st.selectbox("Select Discipline", disciplines)

# # =========================================================
# # STAFF-STUDENT RATIO
# # =========================================================
# st.header("👩‍🏫 Staffing & Enrolment Data")

# students = st.number_input("Total Student Enrolment", min_value=1)
# core_staff = st.number_input("Number of Core Academic Staff", min_value=1)

# ratio = students / core_staff
# st.info(f"Calculated Staff-Student Ratio: {round(ratio,2)}")

# if ratio <= 30:
#     staff_ratio_score = 1
# elif ratio <= 40:
#     staff_ratio_score = 0.5
# else:
#     staff_ratio_score = 0

# # =========================================================
# # HELPER
# # =========================================================
# def ask_question(label, key):
#     return st.selectbox(
#         label,
#         [1, 0.5, 0],
#         format_func=lambda x: {
#             1: "Fully Implemented",
#             0.5: "Partially Implemented",
#             0: "Not Implemented"
#         }[x],
#         key=key
#     )

# # =========================================================
# # SECTIONS
# # =========================================================
# with st.expander("📘 Academic Content"):
#     academic = {
#         "curriculum_aligned_with_BMAS": ask_question("Curriculum aligned with BMAS?", "a1"),
#         "innovative_courses_present": ask_question("Innovative courses incorporated?", "a2"),
#         "curriculum_coverage_complete": ask_question("Curriculum coverage complete?", "a3"),
#         "admission_requirements_compliant": ask_question("Admission requirements compliant?", "a4"),
#         "academic_regulations_defined": ask_question("Academic regulations documented?", "a5"),
#         "tests_and_examinations_standardized": ask_question("Assessment standardized?", "a6"),
#         "evaluation_methods_clear": ask_question("Evaluation methods clear?", "a7"),
#         "degree_projects_adequate": ask_question("Degree projects adequate?", "a8"),
#         "practical_work_adequate": ask_question("Practical training adequate?", "a9"),
#         "student_course_evaluation_present": ask_question("Student evaluation implemented?", "a10"),
#         "skills_acquisition_programme": ask_question("Skills acquisition structured?", "a11"),
#         "external_examiner_system": ask_question("External examiner system active?", "a12"),
#         "internal_quality_assurance": ask_question("Internal QA functional?", "a13")
#     }

# with st.expander("👨‍🏫 Staffing"):
#     staffing = {
#         "proportion_core_staff_sufficient": ask_question("Core staff proportion sufficient?", "s1"),
#         "staff_rank_mix_balanced": ask_question("Staff rank mix balanced?", "s2"),
#         "academic_staff_qualification_high": ask_question("Staff qualification adequate?", "s3"),
#         "staff_competence_verified": ask_question("Staff competence verified?", "s4"),
#         "administrative_support_available": ask_question("Administrative support adequate?", "s5"),
#         "non_teaching_staff_adequate": ask_question("Non-teaching staff sufficient?", "s6"),
#         "academic_staff_development_programme": ask_question("Staff development active?", "s7"),
#         "non_academic_staff_development_programme": ask_question("Non-academic training ongoing?", "s8")
#     }

# with st.expander("🏗 Facilities"):
#     facilities = {
#         "laboratory_space_adequate": ask_question("Laboratory space adequate?", "f1"),
#         "laboratory_equipment_adequate": ask_question("Laboratory equipment adequate?", "f2"),
#         "classroom_space_adequate": ask_question("Classroom space adequate?", "f3"),
#         "classroom_equipment_adequate": ask_question("Classroom equipment adequate?", "f4"),
#         "office_accommodation_adequate": ask_question("Office accommodation adequate?", "f5"),
#         "safety_environment_present": ask_question("Safety environment compliant?", "f6")
#     }

# with st.expander("📚 Library"):
#     library = {
#         "library_holdings_adequate": ask_question("Library holdings adequate?", "l1"),
#         "library_material_current": ask_question("Library materials current?", "l2"),
#         "e_library_subscription_available": ask_question("E-library subscription available?", "l3"),
#         "e_library_access_good": ask_question("E-library access reliable?", "l4")
#     }

# with st.expander("💰 Funding"):
#     funding = {
#         "programme_funding_adequate": ask_question("Programme funding adequate?", "fd1"),
#         "budget_release_regular": ask_question("Budget release regular?", "fd2"),
#         "equipment_maintenance_budget_available": ask_question("Maintenance budget available?", "fd3")
#     }

# with st.expander("🔬 Research"):
#     research = {
#         "research_collaboration_active": ask_question("Research collaboration active?", "r1"),
#         "research_output_present": ask_question("Research output evident?", "r2"),
#         "employer_rating_positive": ask_question("Employer rating positive?", "r3"),
#         "tracer_study_available": ask_question("Tracer study available?", "r4")
#     }

# # =========================================================
# # BUILD INPUT
# # =========================================================
# input_data = {}
# input_data.update(academic)
# input_data.update(staffing)
# input_data.update(facilities)
# input_data.update(library)
# input_data.update(funding)
# input_data.update(research)
# input_data["staff_student_ratio_compliant"] = staff_ratio_score
# input_data["discipline"] = discipline

# # =========================================================
# # SELF STUDY SCORE
# # =========================================================
# def calc_score(section):
#     return sum(section.values()) / len(section) * 100

# academic_score = calc_score(academic)
# staffing_score = calc_score(staffing)
# facilities_score = calc_score(facilities)
# library_score = calc_score(library)
# funding_score = calc_score(funding)

# self_study_score = (
#     academic_score*0.3 +
#     staffing_score*0.28 +
#     facilities_score*0.22 +
#     library_score*0.15 +
#     funding_score*0.05
# )

# st.subheader("📊 Computed Self-Study Score")
# st.success(f"{round(self_study_score,2)} %")

# # =========================================================
# # FEATURE IMPORTANCE
# # =========================================================
# def get_feature_importance(model):
#     try:
#         base_model = model.named_estimators_["rf"]
#     except:
#         base_model = model

#     importance = base_model.feature_importances_

#     return pd.DataFrame({
#         "feature": training_columns,
#         "importance": importance
#     }).sort_values(by="importance", ascending=False)

# # =========================================================
# # PREDICTION + GPT
# # =========================================================
# if st.button("🎯 Generate Accreditation Decision & Advisory"):

#     input_df = pd.DataFrame([input_data])
#     input_encoded = pd.get_dummies(input_df)
#     input_encoded = input_encoded.reindex(columns=training_columns, fill_value=0)

#     prediction = model.predict(input_encoded)
#     predicted_status = label_encoder.inverse_transform(prediction)[0]

#     st.subheader("🏆 Predicted Accreditation Outcome")
#     st.success(predicted_status)

#     importance_df = get_feature_importance(model)

#     # Detect model-driven weaknesses
#     weak = []
#     for col in input_df.columns:
#         if col in importance_df["feature"].values:
#             value = input_df[col].iloc[0]
#             if value in [0, 0.5]:
#                 impact = importance_df.loc[
#                     importance_df["feature"] == col, "importance"
#                 ].values[0]
#                 weak.append((col, value, impact))

#     weak = sorted(weak, key=lambda x: x[2], reverse=True)

#     top_weaknesses = "\n".join(
#         [f"- {w[0].replace('_',' ').title()}" for w in weak[:10]]
#     )

#     prompt = f"""
# You are an accreditation advisory expert.

# Institution: {institution}
# Programme: {programme}
# Discipline: {discipline}

# Self Study Score: {round(self_study_score,2)}%
# Predicted Accreditation Status: {predicted_status}

# The following high-impact weaknesses strongly influenced this prediction:

# {top_weaknesses}

# Provide:
# 1. Strategic preparation advice.
# 2. Section-by-section improvement plan.
# 3. Documentation checklist.
# 4. Risk mitigation strategy.
# """

#     with st.spinner("Generating Personalized Advisory Report..."):

#         response = client.chat.completions.create(
#             model="gpt-4.1-mini",
#             messages=[
#                 {"role": "system", "content": "You are an accreditation advisory expert."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7
#         )

#         report = response.choices[0].message.content

#     st.subheader("🧠 Personalized Accreditation Advisory Report")
#     st.write(report)




import re
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
st.set_page_config(page_title="NUC Accreditation Prediction System", layout="wide")
st.title("🎓 NUC Accreditation Prediction System")
st.caption("Predict accreditation outcome, compute self-study score, and generate readiness recommendations.")

# =========================================================
# TRAIN MODEL IN-APP
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
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    lr = LogisticRegression(max_iter=1000)
    dt = DecisionTreeClassifier(random_state=42)
    rf = RandomForestClassifier(n_estimators=150, random_state=42)
    gb = GradientBoostingClassifier(random_state=42)

    ensemble = VotingClassifier(
        estimators=[
            ("lr", lr),
            ("dt", dt),
            ("rf", rf),
            ("gb", gb),
        ],
        voting="soft",
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
# REAL DATA LISTS
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
# HELPERS
# =========================================================
def ask_question(label: str, key: str) -> float:
    return st.selectbox(
        label,
        [1.0, 0.5, 0.0],
        format_func=lambda x: {
            1.0: "Fully Satisfactory",
            0.5: "Partially Satisfactory",
            0.0: "Unsatisfactory",
        }[x],
        key=key,
    )

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

def calc_score(section: dict) -> float:
    return 0.0 if not section else (sum(section.values()) / len(section)) * 100

def get_feature_importance(_model, _training_columns):
    try:
        base_model = _model.named_estimators_["rf"]
    except Exception:
        return pd.DataFrame(columns=["feature", "importance"])

    importance = base_model.feature_importances_
    return pd.DataFrame({
        "feature": _training_columns,
        "importance": importance
    }).sort_values(by="importance", ascending=False)

# =========================================================
# NUC STAFFING CALCULATION ENGINE
# =========================================================
def score_staff_student_ratio(staff_count: int, student_count: int):
    if staff_count <= 0:
        return 0, 0.0, 0.0
    actual_ratio = student_count / staff_count
    # Based on your uploaded staffing page example where compliance gets full marks
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
    total = prof_count + senior_count + lect1_below_count
    if total <= 0:
        return 0, {"prof_pct": 0.0, "senior_pct": 0.0, "others_pct": 0.0}, 0.0

    prof_pct = pct(prof_count, total)
    senior_pct = pct(senior_count, total)
    others_pct = pct(lect1_below_count, total)

    # NUC target structure approx 20:35:45 with tolerance
    prof_ok = abs(prof_pct - 20) <= 5
    senior_ok = abs(senior_pct - 35) <= 5
    others_ok = abs(others_pct - 45) <= 5

    categories_met = sum([prof_ok, senior_ok, others_ok])

    if categories_met == 3 or prof_pct > 25:
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
    mapping = {
        "Adequate in number and quality": (3, 1.0),
        "Not adequate in number but of good quality": (2, 0.5),
        "Inadequate in number and of poor quality": (0, 0.0),
    }
    return mapping[status_choice]

def score_non_academic_staff_dev(trained_count: int, non_academic_staff_count: int):
    dev_pct = pct(trained_count, non_academic_staff_count)
    if dev_pct >= 70:
        score = 2
    elif dev_pct >= 50:
        score = 1
    else:
        score = 0
    return score, dev_pct, normalized_from_score(score, 2)

# =========================================================
# BASIC INFORMATION
# =========================================================
st.header("Institutional Information")

col1, col2, col3 = st.columns(3)
with col1:
    institution = st.selectbox("Name of Institution", institutions)
with col2:
    discipline = st.selectbox("Discipline", disciplines)
with col3:
    programme = st.selectbox("Programme", programmes)

# =========================================================
# STAFFING & ENROLLMENT
# =========================================================
st.header("Staffing & Enrollment Data")

c1, c2, c3 = st.columns(3)
with c1:
    academic_staff_count = st.number_input("Number of Academic Staff", min_value=1, value=10)
with c2:
    student_count = st.number_input("Number of Students", min_value=1, value=100)
with c3:
    core_staff_count = st.number_input("Number of Academic Staff Core to the Subject Area", min_value=0, value=8)

c4, c5, c6 = st.columns(3)
with c4:
    professor_reader_count = st.number_input("Number of Professors/Readers", min_value=0, value=2)
with c5:
    senior_lecturer_count = st.number_input("Number of Senior Lecturers", min_value=0, value=3)
with c6:
    lecturer1_below_count = st.number_input("Number of Lecturers I and Below", min_value=0, value=5)

c7, c8, c9 = st.columns(3)
with c7:
    phd_holder_count = st.number_input("Number of Ph.D Holders", min_value=0, value=5)
with c8:
    academic_staff_dev_count = st.number_input("Number of Academic Staff with Staff Development Programme", min_value=0, value=4)
with c9:
    non_academic_staff_count = st.number_input("Number of Non-Academic Staff", min_value=0, value=5)

non_academic_staff_dev_count = st.number_input(
    "Number of Non-Academic Staff with Staff Development Programme",
    min_value=0,
    value=3
)

non_teaching_quality_choice = st.selectbox(
    "Non-Teaching Staff Status",
    [
        "Adequate in number and quality",
        "Not adequate in number but of good quality",
        "Inadequate in number and of poor quality",
    ]
)

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
    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("Staff to Student Ratio", f"1 : {round(actual_ratio, 2)}")
        st.metric("Staff/Student Ratio Score", f"{ratio_score_raw}/4")
    with s2:
        st.metric("Core Staff Percentage", f"{round(core_pct, 2)}%")
        st.metric("Core Staff Score", f"{core_score_raw}/6")
    with s3:
        st.metric("Ph.D Holder Percentage", f"{round(phd_pct, 2)}%")
        st.metric("Ph.D Qualification Score", f"{phd_score_raw}/6")

    s4, s5, s6 = st.columns(3)
    with s4:
        st.metric(
            "Staff Mix %",
            f"{round(mix_pct_dict['prof_pct'],1)} : {round(mix_pct_dict['senior_pct'],1)} : {round(mix_pct_dict['others_pct'],1)}"
        )
        st.metric("Staff Mix by Rank Score", f"{mix_score_raw}/5")
    with s5:
        st.metric("Academic Staff Dev. Percentage", f"{round(acad_dev_pct, 2)}%")
        st.metric("Academic Staff Dev. Score", f"{acad_dev_score_raw}/5")
    with s6:
        st.metric("Non-Academic Staff Dev. Percentage", f"{round(non_acad_dev_pct, 2)}%")
        st.metric("Non-Academic Staff Dev. Score", f"{non_acad_dev_score_raw}/2")

    st.metric("Non-Teaching Staff Score", f"{non_teach_score_raw}/3")

# =========================================================
# QUESTION HELPERS
# =========================================================
def ask_section_question(label: str, key: str) -> float:
    return st.selectbox(
        label,
        [1.0, 0.5, 0.0],
        format_func=lambda x: {
            1.0: "Meets Standard",
            0.5: "Partially Meets Standard",
            0.0: "Does Not Meet Standard",
        }[x],
        key=key,
    )

# =========================================================
# ACADEMIC CONTENT
# =========================================================
with st.expander("Academic Content", expanded=False):
    academic = {
        "curriculum_aligned_with_BMAS": ask_section_question("Relationship between CCMAS/BMAS and the curriculum is satisfactory", "a1"),
        "innovative_courses_present": ask_section_question("Innovation (additional courses) is satisfactory", "a2"),
        "curriculum_coverage_complete": ask_section_question("Coverage of the curriculum is satisfactory", "a3"),
        "admission_requirements_compliant": ask_section_question("Admission requirements comply with NUC standards", "a4"),
        "academic_regulations_defined": ask_section_question("Academic regulations are adequate and current", "a5"),
        "tests_and_examinations_standardized": ask_section_question("Tests and examinations are properly standardized", "a6"),
        "evaluation_methods_clear": ask_section_question("Evaluation of students' work is satisfactory", "a7"),
        "degree_projects_adequate": ask_section_question("Degree projects are satisfactory", "a8"),
        "practical_work_adequate": ask_section_question("Practical work is satisfactory", "a9"),
        "student_course_evaluation_present": ask_section_question("Students' course evaluation is implemented", "a10"),
        "skills_acquisition_programme": ask_section_question("Skills acquisition component is satisfactory", "a11"),
        "external_examiner_system": ask_section_question("External examination system is satisfactory", "a12"),
        "internal_quality_assurance": ask_section_question("Internal quality assurance is satisfactory", "a13"),
    }

# =========================================================
# STAFFING
# =========================================================
with st.expander("Staffing", expanded=False):
    staffing = {
        "proportion_core_staff_sufficient": core_staff_feature,
        "staff_rank_mix_balanced": staff_mix_feature,
        "academic_staff_qualification_high": phd_feature,
        "staff_competence_verified": ask_section_question("Competence of the teaching staff is satisfactory", "s1"),
        "administrative_support_available": ask_section_question("Administration of College/School/Faculty/Department is satisfactory", "s2"),
        "non_teaching_staff_adequate": non_teach_feature,
        "academic_staff_development_programme": acad_dev_feature,
        "non_academic_staff_development_programme": non_acad_dev_feature,
    }
    st.info("Calculated items in this section are automatically derived from the figures entered above.")

# =========================================================
# PHYSICAL FACILITIES
# =========================================================
with st.expander("Physical Facilities", expanded=False):
    facilities = {
        "laboratory_space_adequate": ask_section_question("Laboratory space meets the required standard", "f1"),
        "laboratory_equipment_adequate": ask_section_question("Laboratory equipment is adequate and functional", "f2"),
        "classroom_space_adequate": ask_section_question("Classroom space is adequate", "f3"),
        "classroom_equipment_adequate": ask_section_question("Classroom equipment is adequate", "f4"),
        "office_accommodation_adequate": ask_section_question("Office accommodation is adequate", "f5"),
        "safety_environment_present": ask_section_question("Safety and environment requirements are satisfactorily met", "f6"),
    }

# =========================================================
# LIBRARY
# =========================================================
with st.expander("Library", expanded=False):
    library = {
        "library_holdings_adequate": ask_section_question("Library holdings are adequate", "l1"),
        "library_material_current": ask_section_question("Currency of holdings is satisfactory", "l2"),
        "e_library_subscription_available": ask_section_question("Subscription to e-books and e-journals is satisfactory", "l3"),
        "e_library_access_good": ask_section_question("Access to available e-books and e-journals is satisfactory", "l4"),
    }

# =========================================================
# FUNDING
# =========================================================
with st.expander("Funding", expanded=False):
    funding_amount = st.number_input(
        "How much funding is allocated to the programme yearly? (₦)",
        min_value=0.0,
        step=100000.0,
        value=5000000.0,
    )

    funding_band = st.selectbox(
        "Overall funding adequacy",
        ["Adequate", "Moderately Adequate", "Inadequate"],
        index=1
    )

    funding_map = {
        "Adequate": 1.0,
        "Moderately Adequate": 0.5,
        "Inadequate": 0.0,
    }

    funding = {
        "programme_funding_adequate": funding_map[funding_band],
        "budget_release_regular": ask_section_question("Budget release is regular", "fd1"),
        "equipment_maintenance_budget_available": ask_section_question("Equipment maintenance budget is available", "fd2"),
    }

# =========================================================
# RESEARCH / COLLABORATION
# =========================================================
with st.expander("Research and Collaboration", expanded=False):
    research = {
        "research_collaboration_active": ask_section_question("Research and collaboration activities are satisfactory", "r1"),
        "research_output_present": ask_section_question("Research output is satisfactory", "r2"),
        "employer_rating_positive": ask_section_question("Tracer and employers' rating is satisfactory", "r3"),
        "tracer_study_available": ask_section_question("Tracer study evidence is available", "r4"),
    }

# =========================================================
# BUILD INPUT FOR MODEL
# =========================================================
input_data = {}
input_data.update(academic)
input_data.update(staffing)
input_data.update(facilities)
input_data.update(library)
input_data.update(funding)
input_data.update(research)
input_data["staff_student_ratio_compliant"] = staff_ratio_feature
input_data["discipline"] = discipline

# =========================================================
# SCORE BREAKDOWN
# =========================================================
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
research_score = calc_score(research)

self_study_score = (
    academic_score * 0.30 +
    staffing_score * 0.28 +
    physical_facilities_score * 0.22 +
    library_score * 0.15 +
    funding_score * 0.05
)

st.subheader("Score Summary")
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Academic Score", f"{academic_score:.2f}%")
    st.metric("Staffing Score", f"{staffing_score:.2f}%")
with m2:
    st.metric("Physical Facilities Score", f"{physical_facilities_score:.2f}%")
    st.metric("Library Score", f"{library_score:.2f}%")
with m3:
    st.metric("Funding Score", f"{funding_score:.2f}%")
    st.metric("Self Study Score", f"{self_study_score:.2f}%")

# =========================================================
# PREDICTION + ADVISORY
# =========================================================
if st.button("Generate Accreditation Decision and Advisory", type="primary"):
    input_df = pd.DataFrame([input_data])
    input_encoded = pd.get_dummies(input_df)
    input_encoded = input_encoded.reindex(columns=training_columns, fill_value=0)

    prediction = model.predict(input_encoded)
    predicted_status = label_encoder.inverse_transform(prediction)[0]

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
        weak_df = pd.DataFrame(
            [
                {
                    "Feature": w[0].replace("_", " ").title(),
                    "Severity": "Critical" if w[1] == 0.0 else "Moderate",
                    "Importance": round(float(w[2]), 4),
                }
                for w in weak[:10]
            ]
        )
        st.dataframe(weak_df, use_container_width=True)
        top_weaknesses = "\n".join(
            [f"- {w[0].replace('_', ' ').title()}" for w in weak[:10]]
        )
    else:
        top_weaknesses = "- No major weaknesses were detected from the submitted responses."
        st.info("No major weaknesses were detected from the submitted responses.")

    if client is None:
        st.warning("OpenAI API key is not configured, so the personalized advisory report cannot be generated.")
    else:
        prompt = f"""
You are an accreditation advisory expert.

Institution: {institution}
Programme: {programme}
Discipline: {discipline}

Self Study Score: {round(self_study_score, 2)}%
Predicted Accreditation Status: {predicted_status}

Calculated staffing indicators:
- Staff to Student Ratio: 1:{round(actual_ratio, 2)}
- Staff to Student Ratio Score: {ratio_score_raw}/4
- Core Staff Percentage: {round(core_pct, 2)}%
- Core Staff Score: {core_score_raw}/6
- Staff Mix Score: {mix_score_raw}/5
- PhD Qualification Percentage: {round(phd_pct, 2)}%
- PhD Qualification Score: {phd_score_raw}/6
- Academic Staff Development Percentage: {round(acad_dev_pct, 2)}%
- Academic Staff Development Score: {acad_dev_score_raw}/5
- Non-Teaching Staff Score: {non_teach_score_raw}/3
- Non-Academic Staff Development Percentage: {round(non_acad_dev_pct, 2)}%
- Non-Academic Staff Development Score: {non_acad_dev_score_raw}/2

The following high-impact weaknesses strongly influenced this prediction:
{top_weaknesses}

Provide:
1. Strategic preparation advice before accreditation visit.
2. Section-by-section improvement plan.
3. Documentation checklist required.
4. Risk mitigation strategy.
5. Short practical readiness roadmap.

Write in a professional but clear tone.
"""

        with st.spinner("Generating personalized advisory report..."):
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an accreditation advisory expert."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
            report = response.choices[0].message.content

        st.subheader("Personalized Accreditation Advisory Report")
        st.write(report)
