# Software Requirements Specification (SRS) - Requirements & Use Cases Draft

**Version:** 0.1  
**Date:** 2026-11-23  
**Module:** Technical Project - Household Electricity Consumption Analysis  

---

## 1. Project Objectives
- **Define the Goal:** Design, implement, and validate a production-ready Python application that manages, visualizes, analyzes, and predicts household electricity consumption based on smart home measurements across Europe.
- **Address the Need:** Provide smart grid operators, municipal administrators, and individual residents with clear consumption insights, peer benchmark comparisons, and data-driven load predictions.
- **Expected Benefits:** 
  - Enable households to identify high-consumption appliances and reduce energy waste.
  - Provide grid operators with macroscopic demand patterns and temperature-correlated load forecasts.
  - Enforce end-to-end software quality using the V-Model life cycle.

---

## 2. Actors & Role-Based Access Control (RBAC)

### 2.1 Actors Definition
- **User (Standard Resident):** An authenticated resident associated with one or more specific `Home ID`s. Access is strictly confined to assigned households.
- **Admin (System Administrator):** System operator with unrestricted read access across all 500 households, plus exclusive privileges to ingest/reload datasets and manage system configurations.
- **Hierarchy:** `Admin` inherits all general analytic capabilities of `User` (`Admin ▷ User`).

### 2.2 RBAC Permission Matrix

| Feature / Action | User (Resident) | Admin | Security & Access Rule |
| :--- | :---: | :---: | :--- |
| **Login / Logout** (`UC-01`) | Allowed | Allowed | Authenticated session with encrypted/hashed credentials. |
| **Ingest / Reload CSV** (`UC-02`) | **Denied** | Allowed | Hidden from User UI; validated strictly on backend. |
| **View Household Consumption** (`UC-03`) | Assigned Homes Only | All 500 Homes | Backend rejects unauthorized `home_id` queries. |
| **Compare Households (2–5)** (`UC-04`) | Within Assigned Homes | Any Homes (2–5) | Requires $\ge 2$ distinct homes; distinct colors per home. |
| **Overlay Benchmark Curve** (`UC-05`) | Allowed | Allowed | Aggregated system-wide average; exposes no third-party raw records. |
| **Filter Appliance Sources** (`UC-06`) | Allowed | Allowed | Applied dynamically on current query scope. |
| **Predict Consumption (AI)** (`UC-07`) | Assigned Homes Only | All 500 Homes | Feature inputs scoped to user-authorized parameters. |
| **Export Summary Report** (`UC-08`) | Assigned Homes Only | All / Any Homes | Report generation restricted to authorized data scope. |

---

## 3. Functional Requirements (FR) & Use Case (UC) Traceability

| FR ID | Functional Requirement Description | Target UC ID | Primary Actor |
| :--- | :--- | :--- | :--- |
| **FR-01** | **Authentication & Session:** The system shall authenticate users via username and password and maintain role-specific session states. | `UC-01` Authenticate User | User, Admin |
| **FR-02** | **Raw Data Ingestion:** The system shall ingest the raw electricity consumption CSV file (`cp1252` encoding) into normalized relational structures without modifying or discarding inconsistent raw records. | `UC-02` Ingest Raw Dataset | Admin |
| **FR-03** | **Periodic Consumption Analytics:** The system shall render time-series electricity consumption for selected households, defaulting to daily resolution with dynamic aggregation to monthly and yearly views. | `UC-03` View Aggregated Consumption | User, Admin |
| **FR-04** | **Multi-Household Comparison:** The system shall support simultaneous comparison of 2 up to 5 households on an overlaid visualization using distinct color palettes. | `UC-04` Compare Households | User, Admin |
| **FR-05** | **System Benchmark Overlay:** The system shall compute and plot the global average consumption curve (day/month/year) across all households over the active time range. | `UC-05` Overlay Benchmark Curve | User, Admin |
| **FR-06** | **Appliance-Level Filtering:** The system shall enable selective inclusion or exclusion of individual appliance types (e.g., exclude Fridge or isolate Heating/AC). | `UC-06` Filter Appliance Sources | User, Admin |
| **FR-07** | **AI-Powered Predictive Baseline:** The system shall provide trained machine learning baseline models (Statsmodels OLS & Scikit-learn) to predict consumption based on outside temperature and household attributes, isolating data cleaning strictly within the ML training pipeline. | `UC-07` Predict Consumption with AI | User, Admin |
| **FR-08** | **Summary Report Generation (Bonus):** The system shall export monthly and yearly summary reports containing total and per-resident consumption metrics to a downloadable file (CSV/Excel). | `UC-08` Export Consumption Report | User, Admin |

---

## 4. Non-Functional Requirements (NFR)

- **NFR-01 (Performance & Responsiveness):** 
  - Default daily/monthly visualization queries on 100,000 records shall render within $\le 2.0$ seconds.
  - Interactive filter adjustments shall re-render within $\le 500$ ms.
- **NFR-02 (Data Fidelity & Ingestion Rule):** 
  - Raw records (including seasonal contradictions and fluctuating temperatures) shall remain unaltered in storage and standard visualization views.
  - Data cleaning (e.g., outlier filtering, mode imputations) is permitted **only** inside the training pipeline of `UC-07`.
- **NFR-03 (Security & Integrity):** 
  - Strict horizontal authorization checks: regular users shall not access consumption records belonging to unassigned households.
  - Relational CSV structures must enforce Primary Key and Foreign Key referential integrity.
- **NFR-04 (HMI & Usability):** 
  - The UI shall provide clear error boundaries, loading feedback during heavy analytics, and consistent visual styling across tabs.
