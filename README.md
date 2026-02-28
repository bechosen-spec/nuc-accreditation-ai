# 🎓 NUC Accreditation AI

### AI-Powered Accreditation Readiness & Advisory System

NUC Accreditation AI is a hybrid decision-support platform that simulates NUC-style programme evaluation using ensemble machine learning and GPT-based advisory generation.

The system helps university departments assess their accreditation readiness before panel visits.

---

## 🚀 What It Does

* 📋 Collects structured self-study questionnaire responses
* 📊 Computes weighted section scores
* 🧠 Predicts accreditation outcome (FULL, INTERIM, DENIED) using an ensemble model
* 🔎 Identifies high-impact weaknesses using feature importance
* 🤖 Generates personalized strategic advisory reports using GPT

---

## 🏗 System Components

* Logistic Regression
* Decision Tree
* Random Forest
* Gradient Boosting
* Voting Ensemble (Final Model)
* Streamlit Web Interface
* OpenAI GPT Advisory Engine

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

Section weights:

* Academic Content – 30%
* Staffing – 28%
* Physical Facilities – 22%
* Library – 15%
* Funding – 5%

Final accreditation status is predicted by the ensemble ML model (not rule-based).

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

Create `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "your-api-key"
```

---

## ⚠ Disclaimer

This system is a predictive simulation tool for research and preparation purposes.
It does not represent official NUC accreditation decisions.
