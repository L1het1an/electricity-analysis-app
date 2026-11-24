# Household Electricity Consumption Analysis Application

Python application for managing, analyzing, visualizing, and predicting household electricity consumption (100,000 records across 500 smart homes in Europe).

## Team & Responsibilities (Phase B Parallel Tracks)
- **Member A (Data & Auth):** ETL & data normalization, CSV repository with PK/FK integrity, authentication & RBAC (`src/data/`, `src/services/auth_service.py`).
- **Member B (UI & Visualization):** Streamlit dashboard, daily/monthly/yearly aggregation charts, 5-household comparison, global average overlay, appliance filtering (`src/ui/`, `src/services/analytics_service.py`).
- **Member C (Prediction, Export & QA):** Dual-baseline prediction models (Statsmodels OLS + Scikit-learn), monthly/yearly summary report export, performance checks & test suite (`src/services/prediction_service.py`, `src/services/export_service.py`, `tests/`).

## Quick Start
```bash
# 1. Create and activate virtual environment (Windows PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Place raw CSV in data/raw/household_electricity_consumption.csv

# 4. Run the application
streamlit run app.py

# 5. Run unit tests
pytest
```

## Project Schedule (V-Model)
- **Nov 23–24:** Specification & Design (SRS, SVVP v0.1, SDD)
- **Nov 25–30:** Parallel Development (Data/Auth, UI, AI & Export)
- **Dec 01–02:** Testing, Validation & Documentation Finalization (SVVP results)
- **Dec 03:** Final Presentation & Demo
