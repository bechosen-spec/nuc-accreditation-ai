from streamlit.testing.v1 import AppTest


def test_authentication_dashboard_and_assessment_navigation(tmp_path, monkeypatch):
    database = tmp_path / "workflow.db"
    monkeypatch.setenv("NUC_DB_PATH", str(database))

    from pathlib import Path

    app_file = Path(__file__).resolve().parents[1] / "app.py"

    at = AppTest.from_file(str(app_file), default_timeout=45).run()
    assert not at.exception
    assert [button.label for button in at.button] == ["Login", "Create an account"]

    at.button[1].click().run()
    assert not at.exception
    fields = {field.label: field for field in at.text_input}
    fields["Full Name"].set_value("Test Assessor")
    fields["Email"].set_value("assessor@example.com")
    fields["Password"].set_value("StrongPass123!")
    fields["Confirm Password"].set_value("StrongPass123!")
    next(button for button in at.button if button.label == "Create Account").click().run()
    assert not at.exception
    assert database.exists()

    login_fields = {field.label: field for field in at.text_input}
    login_fields["Email"].set_value("assessor@example.com")
    login_fields["Password"].set_value("StrongPass123!")
    next(button for button in at.button if button.label == "Login").click().run()
    assert not at.exception
    assert any(button.label == "Start Accreditation Assessment" for button in at.button)

    # Use a fresh simulated browser session for navigation so AppTest does not
    # retain orphaned login widget state across Streamlit's explicit rerun.
    navigation = AppTest.from_file(str(app_file), default_timeout=45)
    navigation.session_state["user"] = {
        "id": 1,
        "full_name": "Test Assessor",
        "email": "assessor@example.com",
        "role": "user",
    }
    navigation.session_state["page"] = "Dashboard"
    navigation.run()
    next(
        button
        for button in navigation.button
        if button.label == "Start Accreditation Assessment"
    ).click().run()
    assert not navigation.exception
    assert any(selectbox.label == "Name of Institution" for selectbox in navigation.selectbox)
    assert not any(button.label == "Change Assessment Type" for button in navigation.button)
