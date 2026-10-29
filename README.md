# 🎓 NUC Accreditation Readiness System

### Rule-Based Accreditation Readiness and Advisory System

The NUC Accreditation Readiness System is a decision-support platform that evaluates recorded programme evidence with deterministic scoring rules and generates actionable deficiencies and remedies without requiring an external AI service.

The system helps university departments assess their accreditation readiness before panel visits.

---

## 🚀 What It Does

* 📋 Collects structured self-study questionnaire responses
* 📊 Displays every category score as a percentage
* ✅ Classifies FULL, INTERIM, or DENIED from the four core-category percentages
* 🔎 Identifies deficiencies directly from recorded assessment findings
* 🧭 Generates deterministic, actionable recommended remedies

---

## 🏗 System Components

* Central deterministic scoring and accreditation-rules engine
* Historical machine-learning research artifacts remain in the repository but are not loaded or used by the active application
* Streamlit Web Interface
* SQLite assessment history and report persistence
* Offline deterministic report generator

---

## 📊 Dataset

The dataset is a **hybrid structured dataset** combining:

* Real Nigerian universities
* Real academic programme names
* Simulated but logically generated accreditation responses
* Realistic accreditation distribution patterns

Total observations: **22,150 programme-year records**

This ensures realism while preserving ethical compliance.

---

## 📈 Evaluation Logic

Authoritative section maxima:

* Academic Matters – 37
* Staffing – 35
* Physical Facilities – 27
* Library – 18
* Funding – 3
* Research and Collaboration – 3
* Tracer and Employers' Rating – 2

The maxima total 125 points. The overall programme percentage is a separate performance indicator and does not determine accreditation status.

Accreditation is classified from exactly four core categories:

* FULL: all four core categories are at least 70%.
* INTERIM: no core category is below 60%, and at least one is below 70%.
* DENIED: any core category is below 60%.

Funding uses the corrected bands: below ₦300,000 = 1 point; ₦300,000 to below ₦1,000,000 = 2 points; ₦1,000,000 and above = 3 points. The correction makes ₦300,000 the boundary for the second band. Zero is treated as a valid amount in the stated below-₦300,000 band and therefore receives 1 point.

---

## ▶️ Run Locally

```bash
git clone https://github.com/yourusername/nuc-accreditation-ai.git
cd nuc-accreditation-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

---

## ⚠ Disclaimer

This system is an accreditation-readiness decision-support tool for preparation purposes.
It does not represent official NUC accreditation decisions.
