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


def test_no_graduates_uses_separate_industrial_experience_question(tmp_path, monkeypatch):
    database = tmp_path / "no-graduates.db"
    monkeypatch.setenv("NUC_DB_PATH", str(database))
    from pathlib import Path

    app_file = Path(__file__).resolve().parents[1] / "app.py"
    at = authenticated_app(app_file, database, "New Assessment")
    graduates = next(
        item for item in at.selectbox
        if item.label == "Has the programme graduated students?"
    )
    graduates.set_value("No").run()

    assert not at.exception
    industrial = next(
        item for item in at.selectbox
        if item.label == "Students' performance during supervised industrial and other similar experience are:"
    )
    assert industrial.options == ["Very good", "Average", "Below average"]
    assert not any(item.label == "Tracer and Employers' Rating" for item in at.selectbox)
    assert not any("Not Yet Assessable" in item.value for item in at.info)


def test_funding_input_keeps_scoring_without_classification_notice(tmp_path, monkeypatch):
    database = tmp_path / "funding.db"
    monkeypatch.setenv("NUC_DB_PATH", str(database))
    from pathlib import Path

    app_file = Path(__file__).resolve().parents[1] / "app.py"
    at = authenticated_app(app_file, database, "New Assessment")
    funding = next(
        item for item in at.number_input
        if item.label == "How much funding is allocated to the programme yearly? (₦)"
    )
    funding.set_value(300_000.0).run()

    assert not at.exception
    assert not any("Funding classification:" in item.value for item in at.info)


def test_generated_report_ui_and_download_use_corrected_findings(tmp_path, monkeypatch):
    database = tmp_path / "corrected-report.db"
    monkeypatch.setenv("NUC_DB_PATH", str(database))
    from pathlib import Path

    app_file = Path(__file__).resolve().parents[1] / "app.py"
    at = authenticated_app(app_file, database, "New Assessment")

    institution = next(item for item in at.selectbox if item.label == "Name of Institution")
    institution.set_value(institution.options[0]).run()
    discipline = next(item for item in at.selectbox if item.label == "Discipline")
    discipline.set_value(discipline.options[0]).run()
    programme = next(item for item in at.selectbox if item.label == "Programme")
    programme.set_value(programme.options[0]).run()

    staffing_values = {
        "Number of academic staff": 10,
        "Number of students": 100,
        "Number of academic staff core to the subject area": 8,
        "Number of Professors/Readers": 3,
        "Number of Senior Lecturers": 3,
        "Number of Lecturers I and below": 4,
        "Number of Ph.D Holders": 8,
        "Number of academic staff with staff development programme": 8,
        "Number of non-teaching staff": 5,
        "Number of non-academic staff with staff development programme": 4,
        "How much funding is allocated to the programme yearly? (₦)": 300_000.0,
    }
    for item in at.number_input:
        if item.label in staffing_values:
            item.set_value(staffing_values[item.label])

    identity_fields = {"Name of Institution", "Discipline", "Programme"}
    for item in at.selectbox:
        if item.label in identity_fields:
            continue
        if item.label == "Has the programme graduated students?":
            item.set_value("No")
        elif item.options:
            item.set_value(item.options[-1])
    at.run()

    industrial = next(
        item for item in at.selectbox
        if item.label == "Students' performance during supervised industrial and other similar experience are:"
    )
    industrial.set_value("Below average").run()

    next(
        button for button in at.button
        if button.label == "Generate Accreditation Results"
    ).click().run()

    assert not at.exception
    report_text = next(
        item.value for item in at.markdown
        if "## Accreditation Status" in item.value
    )
    assert "Programme funding is inadequate." in report_text
    assert "The programme should be adequately funded." in report_text
    assert "Available practical space does not meet the applicable NUC standard." in report_text
    assert "Laboratory equipment does not meet the applicable NUC standard." in report_text
    assert "₦300,000" not in report_text
    assert "50%" not in report_text
    assert "70%" not in report_text
    assert any(
        item.label == "Download Markdown Report"
        for item in at.get("download_button")
    )


def test_programme_with_graduates_keeps_tracer_question(tmp_path, monkeypatch):
    database = tmp_path / "with-graduates.db"
    monkeypatch.setenv("NUC_DB_PATH", str(database))
    from pathlib import Path

    app_file = Path(__file__).resolve().parents[1] / "app.py"
    at = authenticated_app(app_file, database, "New Assessment")
    graduates = next(
        item for item in at.selectbox
        if item.label == "Has the programme graduated students?"
    )
    graduates.set_value("Yes").run()

    assert not at.exception
    tracer = next(item for item in at.selectbox if item.label == "Tracer and Employers' Rating")
    assert tracer.options == [
        "Tracer system is in place and graduates’ performance on the job is very good",
        "Tracer system not in place but graduates’ performance on the job is good or vice versa",
        "Tracer system not in place and performance below average",
    ]
