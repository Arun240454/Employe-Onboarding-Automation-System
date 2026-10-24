# AI Powered Employee Onboarding System

A Streamlit app that automates employee onboarding. Enter an employee's **name**, **role** and **department** and it generates:

1. A professional welcome email
2. A structured 7-day onboarding plan
3. A required-documents checklist
4. A department-specific IT access checklist
5. FAQs for new hires
6. Role-based training resources

Content is tailored with rule-based logic (role family, leadership detection, department). It runs entirely locally, with no external APIs. The full package can be downloaded as Markdown.

## Run

```bash
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501.

## Customise

All reference data (documents, IT access, training, role keywords) sits at the top of `app.py`. Edit those dictionaries to match your organisation.
