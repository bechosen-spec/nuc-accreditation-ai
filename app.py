import streamlit as st
import pandas as pd
import joblib
from openai import OpenAI

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="NUC Accreditation AI", layout="wide")
st.title("🎓 NUC Accreditation Readiness & Advisory System")

# =========================================================
# LOAD MODEL
# =========================================================
model = joblib.load("final_nuc_accreditation_model.pkl")
label_encoder = joblib.load("label_encoder.pkl")
training_columns = joblib.load("training_columns.pkl")

clean_key = st.secrets["OPENAI_API_KEY"]
clean_key = clean_key.replace("\u200b", "").strip()

client = OpenAI(api_key=clean_key)

# =========================================================
# REAL DATA LISTS
# =========================================================
institutions = ['Abia State University', 'Abubakar Tafawa Balewa University',
'Adekunle Ajasin University', 'Afe Babalola University',
'Ahmadu Bello University', 'Ajayi Crowther University',
'American University of Nigeria', 'Babcock University',
'Bayero University Kano', 'Benson Idahosa University',
'Benue State University', 'Bowen University', 'Covenant University',
'Delta State University', 'Ekiti State University',
'Federal University of Technology Akure',
'Federal University of Technology Minna',
'Federal University of Technology Owerri',
'Igbinedion University', 'Kaduna State University',
'Kogi State University', 'Lagos State University',
'Lead City University', 'Madonna University',
'Nile University of Nigeria', 'Nnamdi Azikiwe University',
'Obafemi Awolowo University', 'Pan Atlantic University',
'Rivers State University', 'University of Abuja',
'University of Benin', 'University of Calabar',
'University of Ibadan', 'University of Ilorin',
'University of Jos', 'University of Lagos',
'University of Maiduguri', 'University of Nigeria Nsukka',
'University of Port Harcourt', 'University of Uyo']

programmes = ['Accounting', 'Adult Education', 'Agricultural Engineering',
'Banking and Finance', 'Biochemistry', 'Biology',
'Biomedical Engineering', 'Business Administration',
'Chemical Engineering', 'Chemistry', 'Civil Engineering',
'Computer Science', 'Curriculum Studies', 'Cybersecurity',
'Data Science', 'Economics', 'Educational Management',
'Electrical Engineering', 'Geology', 'Guidance and Counselling',
'Information Technology', 'Mathematics',
'Mechanical Engineering', 'Mechatronics Engineering',
'Microbiology', 'Petroleum Engineering', 'Physics',
'Public Administration', 'Software Engineering', 'Statistics']

disciplines = ['Computing', 'Education', 'Engineering', 'Management', 'Science']


# =========================================================
# BASIC INFORMATION
# =========================================================
st.header("🏛 Institutional Information")

institution = st.selectbox("Select Institution", institutions)
programme = st.selectbox("Select Programme", programmes)
discipline = st.selectbox("Select Discipline", disciplines)

# =========================================================
# STAFF-STUDENT RATIO
# =========================================================
st.header("👩‍🏫 Staffing & Enrolment Data")

students = st.number_input("Total Student Enrolment", min_value=1)
core_staff = st.number_input("Number of Core Academic Staff", min_value=1)

ratio = students / core_staff
st.info(f"Calculated Staff-Student Ratio: {round(ratio,2)}")

if ratio <= 30:
    staff_ratio_score = 1
elif ratio <= 40:
    staff_ratio_score = 0.5
else:
    staff_ratio_score = 0

# =========================================================
# HELPER
# =========================================================
def ask_question(label, key):
    return st.selectbox(
        label,
        [1, 0.5, 0],
        format_func=lambda x: {
            1: "Fully Implemented",
            0.5: "Partially Implemented",
            0: "Not Implemented"
        }[x],
        key=key
    )

# =========================================================
# SECTIONS
# =========================================================
with st.expander("📘 Academic Content"):
    academic = {
        "curriculum_aligned_with_BMAS": ask_question("Curriculum aligned with BMAS?", "a1"),
        "innovative_courses_present": ask_question("Innovative courses incorporated?", "a2"),
        "curriculum_coverage_complete": ask_question("Curriculum coverage complete?", "a3"),
        "admission_requirements_compliant": ask_question("Admission requirements compliant?", "a4"),
        "academic_regulations_defined": ask_question("Academic regulations documented?", "a5"),
        "tests_and_examinations_standardized": ask_question("Assessment standardized?", "a6"),
        "evaluation_methods_clear": ask_question("Evaluation methods clear?", "a7"),
        "degree_projects_adequate": ask_question("Degree projects adequate?", "a8"),
        "practical_work_adequate": ask_question("Practical training adequate?", "a9"),
        "student_course_evaluation_present": ask_question("Student evaluation implemented?", "a10"),
        "skills_acquisition_programme": ask_question("Skills acquisition structured?", "a11"),
        "external_examiner_system": ask_question("External examiner system active?", "a12"),
        "internal_quality_assurance": ask_question("Internal QA functional?", "a13")
    }

with st.expander("👨‍🏫 Staffing"):
    staffing = {
        "proportion_core_staff_sufficient": ask_question("Core staff proportion sufficient?", "s1"),
        "staff_rank_mix_balanced": ask_question("Staff rank mix balanced?", "s2"),
        "academic_staff_qualification_high": ask_question("Staff qualification adequate?", "s3"),
        "staff_competence_verified": ask_question("Staff competence verified?", "s4"),
        "administrative_support_available": ask_question("Administrative support adequate?", "s5"),
        "non_teaching_staff_adequate": ask_question("Non-teaching staff sufficient?", "s6"),
        "academic_staff_development_programme": ask_question("Staff development active?", "s7"),
        "non_academic_staff_development_programme": ask_question("Non-academic training ongoing?", "s8")
    }

with st.expander("🏗 Facilities"):
    facilities = {
        "laboratory_space_adequate": ask_question("Laboratory space adequate?", "f1"),
        "laboratory_equipment_adequate": ask_question("Laboratory equipment adequate?", "f2"),
        "classroom_space_adequate": ask_question("Classroom space adequate?", "f3"),
        "classroom_equipment_adequate": ask_question("Classroom equipment adequate?", "f4"),
        "office_accommodation_adequate": ask_question("Office accommodation adequate?", "f5"),
        "safety_environment_present": ask_question("Safety environment compliant?", "f6")
    }

with st.expander("📚 Library"):
    library = {
        "library_holdings_adequate": ask_question("Library holdings adequate?", "l1"),
        "library_material_current": ask_question("Library materials current?", "l2"),
        "e_library_subscription_available": ask_question("E-library subscription available?", "l3"),
        "e_library_access_good": ask_question("E-library access reliable?", "l4")
    }

with st.expander("💰 Funding"):
    funding = {
        "programme_funding_adequate": ask_question("Programme funding adequate?", "fd1"),
        "budget_release_regular": ask_question("Budget release regular?", "fd2"),
        "equipment_maintenance_budget_available": ask_question("Maintenance budget available?", "fd3")
    }

with st.expander("🔬 Research"):
    research = {
        "research_collaboration_active": ask_question("Research collaboration active?", "r1"),
        "research_output_present": ask_question("Research output evident?", "r2"),
        "employer_rating_positive": ask_question("Employer rating positive?", "r3"),
        "tracer_study_available": ask_question("Tracer study available?", "r4")
    }

# =========================================================
# BUILD INPUT
# =========================================================
input_data = {}
input_data.update(academic)
input_data.update(staffing)
input_data.update(facilities)
input_data.update(library)
input_data.update(funding)
input_data.update(research)
input_data["staff_student_ratio_compliant"] = staff_ratio_score
input_data["discipline"] = discipline

# =========================================================
# SELF STUDY SCORE
# =========================================================
def calc_score(section):
    return sum(section.values()) / len(section) * 100

academic_score = calc_score(academic)
staffing_score = calc_score(staffing)
facilities_score = calc_score(facilities)
library_score = calc_score(library)
funding_score = calc_score(funding)

self_study_score = (
    academic_score*0.3 +
    staffing_score*0.28 +
    facilities_score*0.22 +
    library_score*0.15 +
    funding_score*0.05
)

st.subheader("📊 Computed Self-Study Score")
st.success(f"{round(self_study_score,2)} %")

# =========================================================
# FEATURE IMPORTANCE
# =========================================================
def get_feature_importance(model):
    try:
        base_model = model.named_estimators_["rf"]
    except:
        base_model = model

    importance = base_model.feature_importances_

    return pd.DataFrame({
        "feature": training_columns,
        "importance": importance
    }).sort_values(by="importance", ascending=False)

# =========================================================
# PREDICTION + GPT
# =========================================================
if st.button("🎯 Generate Accreditation Decision & Advisory"):

    input_df = pd.DataFrame([input_data])
    input_encoded = pd.get_dummies(input_df)
    input_encoded = input_encoded.reindex(columns=training_columns, fill_value=0)

    prediction = model.predict(input_encoded)
    predicted_status = label_encoder.inverse_transform(prediction)[0]

    st.subheader("🏆 Predicted Accreditation Outcome")
    st.success(predicted_status)

    importance_df = get_feature_importance(model)

    # Detect model-driven weaknesses
    weak = []
    for col in input_df.columns:
        if col in importance_df["feature"].values:
            value = input_df[col].iloc[0]
            if value in [0, 0.5]:
                impact = importance_df.loc[
                    importance_df["feature"] == col, "importance"
                ].values[0]
                weak.append((col, value, impact))

    weak = sorted(weak, key=lambda x: x[2], reverse=True)

    top_weaknesses = "\n".join(
        [f"- {w[0].replace('_',' ').title()}" for w in weak[:10]]
    )

    prompt = f"""
You are an accreditation advisory expert.

Institution: {institution}
Programme: {programme}
Discipline: {discipline}

Self Study Score: {round(self_study_score,2)}%
Predicted Accreditation Status: {predicted_status}

The following high-impact weaknesses strongly influenced this prediction:

{top_weaknesses}

Provide:
1. Strategic preparation advice.
2. Section-by-section improvement plan.
3. Documentation checklist.
4. Risk mitigation strategy.
5. 90-day roadmap.
"""

    with st.spinner("Generating Personalized Advisory Report..."):

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are an accreditation advisory expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        report = response.choices[0].message.content

    st.subheader("🧠 Personalized Accreditation Advisory Report")
    st.write(report)