from streamlit.testing.v1 import AppTest


def authenticated_app(app_file, database, page, user_id=1):
    at = AppTest.from_file(str(app_file), default_timeout=45)
    at.session_state["user"] = {
        "id": user_id,
        "full_name": "Test Assessor",
        "email": "assessor@example.com",
        "role": "user",
    }
    at.session_state["page"] = page
    return at.run()


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


def test_library_options_are_complete_in_the_live_form(tmp_path, monkeypatch):
    database = tmp_path / "library-options.db"
    monkeypatch.setenv("NUC_DB_PATH", str(database))
    from pathlib import Path

    app_file = Path(__file__).resolve().parents[1] / "app.py"
    at = authenticated_app(app_file, database, "New Assessment")
    assert not at.exception

    selectboxes = {item.label: item for item in at.selectbox}
    assert selectboxes["Holdings"].options == [
        "Good quality and very relevant and adequate in number and coverage",
        "Good quality and adequate in number and coverage",
        "Good quality but inadequate in number and coverage",
        "Inadequate in number, quality and coverage",
        "Poor quality and inadequate in number and coverage",
    ]
    assert selectboxes["Currency of Holdings"].options[3] == (
        "Current for recommended text but not current for journals or vice versa"
    )


def test_saved_assessments_shows_exactly_five_public_columns(tmp_path, monkeypatch):
    import sqlite3
    from pathlib import Path

    database = tmp_path / "saved-view.db"
    monkeypatch.setenv("NUC_DB_PATH", str(database))
    app_file = Path(__file__).resolve().parents[1] / "app.py"

    # First execution creates and migrates the isolated schema.
    AppTest.from_file(str(app_file), default_timeout=45).run()
    conn = sqlite3.connect(database)
    conn.execute(
        "INSERT INTO users(full_name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)",
        ("Test Assessor", "assessor@example.com", "x", "user", "2026-10-01"),
    )
    user_id = conn.execute("SELECT id FROM users").fetchone()[0]
    conn.execute(
        """
        INSERT INTO assessments(
            user_id, institution_name, discipline, programme_name,
            programme_score, predicted_status, actual_ratio, core_pct, phd_pct,
            created_at, assessment_payload, report_text, rule_based_status,
            assessment_type, assessment_date
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            user_id, "Test University", "Computing", "Computer Science",
            88.0, "FULL", 20, 80, 75, "2026-11-02T10:00:00", "{}", "legacy",
            "FULL", "standard_manual", "2026-10-31",
        ),
    )
    conn.commit()
    conn.close()

    at = authenticated_app(app_file, database, "Saved Assessments", user_id=user_id)
    assert not at.exception
    displayed = at.dataframe[0].value
    assert list(displayed.columns) == [
        "Institution Name",
        "Discipline",
        "Programme Name",
        "Accreditation Status",
        "Assessment Date",
    ]
    assert displayed.iloc[0].to_dict() == {
        "Institution Name": "Test University",
        "Discipline": "Computing",
        "Programme Name": "Computer Science",
        "Accreditation Status": "FULL ACCREDITATION",
        "Assessment Date": "31 Oct 2026",
    }
