from pathlib import Path


APP_SOURCE = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
ACTIVE_SOURCE = APP_SOURCE.split("\nimport re\n", 1)[1]
ASSESSMENT_UI = ACTIVE_SOURCE.split('elif st.session_state.page == "New Assessment":', 1)[1]
ASSESSMENT_UI = ASSESSMENT_UI.split("# SAVED ASSESSMENTS", 1)[0]
SAVED_UI = ACTIVE_SOURCE.split('elif st.session_state.page == "Saved Assessments":', 1)[1]
SAVED_UI = SAVED_UI.split("# REPORT HISTORY", 1)[0]
HISTORY_UI = ACTIVE_SOURCE.split('elif st.session_state.page == "Report History":', 1)[1]
HISTORY_UI = HISTORY_UI.split("# ADMIN DASHBOARD", 1)[0]
DASHBOARD_UI = ACTIVE_SOURCE.split('if st.session_state.page == "Dashboard":', 1)[1]
DASHBOARD_UI = DASHBOARD_UI.split("# NEW ASSESSMENT", 1)[0]


def test_required_interface_copy_is_present():
    assert "NUC Accreditation Readiness System" in ACTIVE_SOURCE
    assert "Monitor programme accreditation readiness and track assessment progress." in ACTIVE_SOURCE
    assert "Start Accreditation Assessment" in ACTIVE_SOURCE
    assert "Evaluate programme accreditation readiness using the required assessment criteria." in ACTIVE_SOURCE
    assert "Generate Accreditation Report" in ASSESSMENT_UI
    assert "Download Markdown Report" in ASSESSMENT_UI


def test_unwanted_homepage_and_result_copy_is_absent():
    assert "Rule-based accreditation classification" not in ACTIVE_SOURCE
    assert "Accreditation Assessment Results" not in ASSESSMENT_UI
    assert 'st.subheader("Programme Score")' not in ASSESSMENT_UI
    assert "Core Accreditation Performance" not in ASSESSMENT_UI
    assert "Deficiencies and Recommended Remedies" not in ASSESSMENT_UI
    assert "Advisory Disclaimer" not in ASSESSMENT_UI


def test_raw_score_downloads_are_absent():
    assert "Download JSON Assessment Record" not in ACTIVE_SOURCE
    assert "Download CSV Score Summary" not in ACTIVE_SOURCE
    assert "Download Markdown Report" in ASSESSMENT_UI


def test_saved_assessments_uses_the_five_column_view():
    assert "get_saved_assessments_view" in SAVED_UI
    assert "get_user_assessments" not in SAVED_UI


def test_report_history_hides_workflow_and_score_metadata():
    assert "Assessment Type" not in HISTORY_UI
    assert "assessment_type" not in HISTORY_UI
    assert "standard_manual" not in HISTORY_UI
    assert "programme_score" not in HISTORY_UI
    assert "evidence_coverage" not in HISTORY_UI
    assert "public_report_from_history" in HISTORY_UI


def test_dashboard_removes_average_programme_score_and_keeps_distribution():
    assert "Average Programme Score" not in DASHBOARD_UI
    assert "FULL / INTERIM / DENIED Distribution" in DASHBOARD_UI


def test_obsolete_and_predictive_controls_are_not_in_active_assessment_ui():
    for text in [
        "Change Assessment Type",
        "Selected route:",
        "Upload Computing Documents",
        "Calculated staffing items are automatically derived",
        "Random Forest Prediction",
        "Model Prediction",
        "Prediction Confidence",
        "Top High-Impact Weak Areas",
        "Score-Based Readiness Classification",
    ]:
        assert text not in ASSESSMENT_UI


def test_academic_matters_name_is_used_in_active_assessment_ui():
    assert "Academic Content" not in ASSESSMENT_UI
    assert "ACADEMIC_MATTERS" in ASSESSMENT_UI
