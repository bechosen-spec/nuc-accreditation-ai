from pathlib import Path


APP_SOURCE = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
ACTIVE_SOURCE = APP_SOURCE.split("import re", 1)[1]
ASSESSMENT_UI = ACTIVE_SOURCE.split('elif st.session_state.page == "New Assessment":', 1)[1]
ASSESSMENT_UI = ASSESSMENT_UI.split("# SAVED ASSESSMENTS", 1)[0]


def test_required_interface_copy_is_present():
    assert "NUC Accreditation Readiness System" in ACTIVE_SOURCE
    assert "Monitor programme accreditation readiness and track assessment progress." in ACTIVE_SOURCE
    assert "Start Accreditation Assessment" in ACTIVE_SOURCE
    assert "Evaluate programme accreditation readiness using the required assessment criteria." in ACTIVE_SOURCE
    assert "Accreditation Assessment Results" in ASSESSMENT_UI
    assert "Deficiencies and Recommended Remedies" in ASSESSMENT_UI


def test_obsolete_workflow_controls_are_not_in_active_assessment_ui():
    assert "Change Assessment Type" not in ASSESSMENT_UI
    assert "Selected route:" not in ASSESSMENT_UI
    assert "Upload Computing Documents" not in ASSESSMENT_UI
    assert "Calculated staffing items are automatically derived" not in ASSESSMENT_UI


def test_predictive_results_are_not_in_active_assessment_ui():
    assert "Random Forest Prediction" not in ASSESSMENT_UI
    assert "Model Prediction" not in ASSESSMENT_UI
    assert "Prediction Confidence" not in ASSESSMENT_UI
    assert "Top High-Impact Weak Areas" not in ASSESSMENT_UI
    assert "Score-Based Readiness Classification" not in ASSESSMENT_UI


def test_academic_matters_name_is_used_in_active_assessment_ui():
    assert "Academic Content" not in ASSESSMENT_UI
    assert "ACADEMIC_MATTERS" in ASSESSMENT_UI
