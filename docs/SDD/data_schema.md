# Data Schema & Cleaning Boundary Specification

**Version:** 1.0 (Finalized)  
**Date:** 2026-11-24  
**Storage Format:** Normalized Relational CSV Files (`data/processed/`)

---

## 1. SRS Chapter 4 Version (Conceptual Data Architecture — No Types/Constraints)

*Per `TEMPLATE - Software Requirements Specification`, Section 4 defines the main entities and attributes without technical data types or constraints:*

- **Users:** users_id, users_name, password_hash, role
- **Households:** home_id
- **User_Households:** user_households_id, users_id, home_id
- **Appliances:** appliance_id, appliance_name
- **Measurements:** measurement_id, home_id, appliance_id, energy_consumption, time, date, outdoor_temperature, season, household_size

---

## 2. SDD Chapter 2 Version (Normalized Relational CSV Schema)

*Per `5 - Files and data structures` (PAGE 12–21), all tables are stored as separate CSV files enforcing Primary Keys (`PK`), Foreign Keys (`FK`), Unique (`UN`), Not Null (`NN`), and Referential Integrity in application code.*

### 2.1 Table Definitions

1. **`users.csv`**
   - `users_id` `[PK]` (int) — Unique user identifier
   - `users_name` `[UN, NN]` (str) — Login username
   - `password_hash` `[NN]` (str) — Salted cryptographic password hash
   - `role` `[NN]` (str) — Role enum: `"User"` or `"Admin"`

2. **`households.csv`**
   - `home_id` `[PK]` (int) — Unique anonymized smart home identifier (500 European homes)

3. **`user_households.csv`** *(Junction table for M:N User ↔ Household)*
   - `user_households_id` `[PK]` (int) — Unique mapping record identifier
   - `users_id` `[FK -> users.users_id, NN]` (int)
   - `home_id` `[FK -> households.home_id, NN]` (int)
   - **Table Constraint:** `UN(users_id, home_id)` — Prevents duplicate user-to-home assignments

4. **`appliances.csv`** *(Lookup table eliminating string redundancy across 100,000 rows)*
   - `appliance_id` `[PK]` (int) — Unique appliance identifier (1–10)
   - `appliance_name` `[UN, NN]` (str) — Appliance category name (e.g., Fridge, Heater, Air Conditioning)

5. **`measurements.csv`** *(Fact table preserving all 100,000 raw records)*
   - `measurement_id` `[PK]` (int) — Auto-generated unique measurement identifier (1–100,000)
   - `home_id` `[FK -> households.home_id, NN]` (int)
   - `appliance_id` `[FK -> appliances.appliance_id, NN]` (int)
   - `energy_consumption` `[NN]` (float) — Energy consumed in kWh
   - `time` `[NN]` (str) — Measurement time in 24-hour format (`HH:MM`)
   - `date` `[NN]` (str) — Measurement date (`YYYY-MM-DD`)
   - `outdoor_temperature` `[NN]` (float) — Raw outdoor temperature in °C
   - `season` `[NN]` (str) — Raw season label (`Winter`, `Summer`, `Fall`, `Spring`)
   - `household_size` `[NN]` (int) — Raw recorded household size

### 2.2 Entity Relationships & Multiplicity
- `Users` (1) ↔ `User_Households` (0..*): One user can be linked to zero, one, or multiple households (Admin has global access without requiring explicit links).
- `Households` (1) ↔ `User_Households` (0..*): One household can be linked to zero, one, or multiple users.
- `Households` (1) ↔ `Measurements` (1..*): Each measurement belongs to exactly one household; each household has many measurements.
- `Appliances` (1) ↔ `Measurements` (1..*): Each measurement records exactly one appliance type; each appliance appears in many measurements.

### 2.3 Referential Integrity Rules (Enforced in `src/data/`)
- Every `users_id` in `user_households.csv` MUST exist in `users.csv`.
- Every `home_id` in `user_households.csv` and `measurements.csv` MUST exist in `households.csv`.
- Every `appliance_id` in `measurements.csv` MUST exist in `appliances.csv`.
- Deleting a parent record referenced by child rows is rejected (cascade protection).

---

## 3. ETL Fidelity & AI Pipeline Cleaning Boundary (`NFR-02`)

### 3.1 Ingestion / Storage / Visualization Layer (Strict Zero-Modification Rule)
- Read raw CSV explicitly with `encoding="cp1252"` (handles `"°"` = `0xB0` in `Outdoor Temperature (°C)`).
- **Preserve all 100,000 rows unaltered**: do NOT drop temperature outliers, do NOT overwrite `season` values that conflict with `date`, and do NOT collapse per-row `household_size` into a single static value in storage.
- For **per-resident consumption** (`UC-08` Bonus export), compute `total_kwh / mean(household_size)` per home and period dynamically from raw measurements (guarding against division by zero).

### 3.2 AI Prediction Pipeline Only (`src/services/prediction_service.py`)
- Cleaning is strictly isolated to an in-memory DataFrame copy created inside the ML training pipeline and is **never** written back to `data/processed/*.csv`:
  1. Recompute a calendar-consistent `derived_season` from `date` (fixing the 33.2% raw `Season` vs `Date` contradiction for model features).
  2. Aggregate per-home `household_size` (e.g., mode or mean per `home_id`) to stabilize house-level features.
  3. Optionally filter or clip extreme temperature outliers (e.g., IQR / physical European bounds) and compare raw vs. cleaned metrics (`R²`, `MAE`, `RMSE`) honestly.
