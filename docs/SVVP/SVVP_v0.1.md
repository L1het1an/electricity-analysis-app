# Software Verification and Validation Plan (SVVP)

**Version:** 0.1 (Pre-Development Baseline)  
**Date:** 2026-11-24  
**Project:** Household Electricity Consumption Analysis Application  

---

## Summary
1. Test Environment
2. Test Scenarios
3. Success Metrics
4. Acceptance Criteria

---

## 1. Test Environment

All verification and validation tests will be executed in the following controlled environment *(update exact minor versions in v1.0 during S12 execution)*:

- **Operating System:** Windows 11 (64-bit)
- **Web Server / App Runner:** Streamlit Local Server (`streamlit >= 1.32.0`)
- **Web Browser:** Google Chrome / Microsoft Edge (latest stable)
- **Backend Framework & Libraries:** Python 3.11+, Pandas (`>=2.1.0`), NumPy (`>=1.26.0`), Matplotlib (`>=3.8.0`), Seaborn (`>=0.13.0`), Statsmodels (`>=0.14.0`), Scikit-learn (`>=1.4.0`), Pytest (`>=8.0.0`)
- **Database / Storage System:** Normalized Relational CSV Files (`data/processed/`: `users.csv`, `households.csv`, `user_households.csv`, `appliances.csv`, `measurements.csv`) ingested from `cp1252`-encoded raw CSV (`100,000` rows, `500` European households)
- **Client Device:** Desktop / Laptop PC with 1920x1080 display resolution

---

## 2. Test Scenarios

Each atomic test scenario traces directly back to a Use Case (`UC-xx`) and Requirement (`FR-xx` / `NFR-xx`) from the SRS, covering **valid**, **boundary**, and **invalid/unauthorized** inputs (`2-PAGE 23`, `7-PAGE 7–11`).  
*Status is set to `PENDING` in v0.1 and will be updated to `OK` or `KO` with execution evidence during Phase C (S12).*

| Test ID     | Traceability                | Scenario Description                            | Input Data                                                                           | User Actions                                                                                         | Expected Output                                                                                                                                                                                               |  OK / KO  | Comments |
| :---------- | :-------------------------- | :---------------------------------------------- | :----------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :-------: | :------- |
| **AUTH-01** | `UC-01` / `FR-01`           | Valid Admin login                               | Username: `admin`<br>Password: `[valid_admin_pwd]`                                   | 1. Open app login page.<br>2. Enter Admin credentials.<br>3. Click "Login".                          | Session created with `role="Admin"`; redirected to dashboard; Admin Data tab visible; access to all 500 homes.                                                                                                | `OK` | OK — test_auth_01_valid_admin_login, test_admin_login_opens_the_data_management_screen; admin scope = 500 homes |
| **AUTH-02** | `UC-01` / `FR-01`           | Valid User login (multi-home)                   | Username: `user_multi`<br>Password: `[valid_user_pwd]` (linked to Homes 1, 2, 3)     | 1. Enter valid User credentials.<br>2. Click "Login".                                                | Session created with `role="User"`; redirected to dashboard; Admin Data tab hidden; only Homes 1, 2, 3 available.                                                                                             | `OK` | OK — test_auth_02_valid_user_login_is_scoped_to_linked_homes, test_standard_user_login_hides_the_admin_screen; user_multi linked to homes 1, 2, 3 |
| **AUTH-03** | `UC-01` / `FR-01`           | Invalid password or unknown user                | Username: `admin`<br>Password: `WrongPass!`                                          | 1. Enter invalid credentials.<br>2. Click "Login".                                                   | Remain on login page; error `"Invalid username or password"` displayed; no session created.                                                                                                                   | `OK` | OK — test_auth_03_wrong_password_is_rejected, test_auth_03b_unknown_user_is_indistinguishable, test_wrong_password_keeps_the_login_form |
| **AUTH-04** | `UC-01` / `FR-01`           | Empty credentials & Logout                      | Empty username/password; then valid login + Logout                                   | 1. Click "Login" with empty fields.<br>2. Log in validly, then click "Logout".                       | Validation warning on empty fields; after Logout, session cleared and login form shown.                                                                                                                       | `OK` | OK — test_auth_04_empty_credentials_are_reported, test_auth_04b_sign_out_clears_the_session, test_logout_clears_the_session |
| **RBAC-01** | `UC-03`, `UC-04` / `NFR-03` | Unauthorized home access blocked                | Authenticated `user_multi` (Homes 1, 2, 3) requesting `home_id=99`                   | 1. Invoke backend/service query with `home_id=99`.                                                   | `PermissionError` raised / access denied; no records for Home 99 returned.                                                                                                                                    | `OK` | OK — test_rbac_01_unauthorized_home_is_refused: PermissionError on home_id=99, no rows returned |
| **DATA-01** | `UC-02` / `FR-02`, `NFR-02` | Valid CSV ingestion & raw fidelity              | Raw `household_electricity_consumption.csv` (`cp1252`, 100,000 rows)                 | 1. Logged in as Admin.<br>2. Trigger dataset ingestion in Admin Data tab.                            | 5 normalized CSVs written to `data/processed/`; `measurements.csv` has exactly 100,000 rows; `households.csv` has 500 rows; `appliances.csv` has 10 rows; raw temp/season/household_size preserved unaltered. | `OK` | OK — test_data_01_ingestion_button_rebuilds_the_tables, test_ingest_raw_csv_preserves_raw_records; 100,000 / 500 / 10 rows |
| **DATA-02** | `UC-02` / `FR-02`, `NFR-03` | Referential integrity & corrupted CSV rejection | Missing required column CSV; orphan FK check (`home_id=9999`)                        | 1. Admin attempts to load malformed CSV.<br>2. Run `validate_referential_integrity()`.               | Malformed CSV rejected cleanly with error message (existing data intact); integrity check passes on valid tables and fails on orphan FK.                                                                      | `OK` | OK — test_data_02_bad_path_is_rejected_and_tables_survive, test_ingest_rejects_missing_columns, test_validate_integrity_detects_orphan_fk |
| **VIS-01**  | `UC-03` / `FR-03`           | Default daily consumption view                  | Authorized `home_id=1`                                                               | 1. Log in and open Analytics tab without changing filters.                                           | Chart renders automatically in **Daily** granularity with labeled axes (`Date`, `Energy Consumption (kWh)`) and KPI cards.                                                                                    | `PENDING` |          |
| **VIS-02**  | `UC-03` / `FR-03`           | Granularity switch (Monthly / Yearly)           | Authorized `home_id=1`; switch `Daily` -> `Monthly` -> `Yearly`                      | 1. Click `Monthly` radio button.<br>2. Click `Yearly` radio button.                                  | Chart re-aggregates accurately to monthly (12–13 periods) and yearly totals; sum across periods equals total kWh.                                                                                             | `PENDING` |          |
| **VIS-03**  | `UC-04` / `FR-04`           | Compare 5 households (boundary valid)           | Admin selects 5 homes: `[1, 2, 3, 4, 5]`                                             | 1. Select 5 homes in multi-selector.<br>2. View comparison chart.                                    | Exactly 5 curves plotted on shared axes, each in a distinct color with matching legend entries.                                                                                                               | `PENDING` |          |
| **VIS-04**  | `UC-04` / `FR-04`           | Compare >5 households (boundary invalid)        | Admin attempts to select 6th home `[1, 2, 3, 4, 5, 6]`                               | 1. Attempt to add a 6th household in multi-selector.                                                 | UI enforces maximum of 5 households and displays warning `"Maximum 5 households can be compared simultaneously"`.                                                                                             | `PENDING` |          |
| **VIS-05**  | `UC-05` / `FR-05`           | Global average curve overlay                    | Selected `[1, 2]`; toggle "Show Global Average Curve" ON for Daily/Monthly/Yearly    | 1. Check "Show Global Average Curve".<br>2. Switch granularity.                                      | Dashed benchmark curve (`All-Households Average`) overlaid across all 500 homes, recalculating dynamically per granularity.                                                                                   | `PENDING` |          |
| **VIS-06**  | `UC-06` / `FR-06`           | Appliance filtering (Exclude Fridge & Empty)    | Uncheck `Fridge`; then uncheck all 10 appliances                                     | 1. Uncheck `Fridge` in Appliance Filter.<br>2. Uncheck all appliances.                               | Total kWh decreases by exact Fridge sum when excluded; empty selection shows friendly warning without crashing.                                                                                               | `PENDING` |          |
| **AI-01**   | `UC-07` / `FR-07`, `NFR-02` | Dual-baseline training & isolated cleaning      | Normalized dataset loaded; train Statsmodels OLS + Sklearn Tree                      | 1. Open AI Prediction tab.<br>2. Inspect model metrics and verify `measurements.csv` hash/row count. | Both models train cleanly; honest `R²`, `MAE`, `RMSE` displayed (acknowledging low weather signal); on-disk CSV files remain 100% unmodified.                                                                 | `PENDING` |          |
| **AI-02**   | `UC-07` / `FR-07`           | Valid prediction inference                      | Temp: `25.0°C`, Household Size: `3`, Season: `Summer`, Appliance: `Air Conditioning` | 1. Enter valid forecast inputs.<br>2. Select model and click "Predict".                              | Returns positive numeric kWh prediction within plausible appliance range without errors.                                                                                                                      | `PENDING` |          |
| **AI-03**   | `UC-07` / `FR-07`           | Invalid prediction inputs (boundary)            | Temp: `150.0°C` or Household Size: `0`                                               | 1. Enter out-of-range temperature or non-positive household size.<br>2. Click "Predict".             | Validation error displayed; model inference not executed with invalid input.                                                                                                                                  | `PENDING` |          |
| **EXP-01**  | `UC-08` / `FR-08`           | Monthly & Yearly summary report export (Bonus)  | Authorized homes `[1, 2]`; Period: `Monthly` and `Yearly`                            | 1. Open Export tab.<br>2. Select homes & period.<br>3. Preview and click "Download CSV Report".      | Valid UTF-8 CSV downloaded containing `home_id`, `period`, `total_kwh`, `avg_household_size`, `per_resident_kwh` (`total_kwh / avg_household_size`).                                                          | `PENDING` |          |
| **NFR-01**  | `UC-03`, `UC-06` / `NFR-01` | Performance & latency benchmark                 | Full 100,000-row dataset (500 homes)                                                 | 1. Measure default Daily chart load time.<br>2. Measure appliance filter re-render time.             | Default chart aggregation/render `<= 2.0 s`; filter update `<= 500 ms`.                                                                                                                                       | `PENDING` |          |

---

## 3. Success Metrics

Per `7 - Software Verification and Validation Plan (PAGE 16)`, the validation success rate is calculated as:

$$\text{Success Rate (\%)} = \frac{\text{Tests Passed (OK)}}{\text{Total Tests Executed}} \times 100\%$$

| Metric                       | Value (To be completed in S12) |
| :--------------------------- | :----------------------------: |
| **Total Test Cases Planned** |               18               |
| **Total Tests Executed**     |             `TBD`              |
| **Tests Passed (`OK`)**      |             `TBD`              |
| **Tests Failed (`KO`)**      |             `TBD`              |
| **Success Rate (%)**         |             `TBD`              |

---

## 4. Acceptance Criteria

Per `7 - Software Verification and Validation Plan (PAGE 17)`, release acceptance follows three thresholds:

- [ ] **Unconditional Acceptance (`100%` success rate):** All 18 test cases pass (`OK`), zero critical/major defects, ready for final demonstration and delivery.
- [ ] **Conditional Acceptance (`85% – 99%` success rate):** Only minor non-critical defects remain with documented workarounds and an agreed fix schedule.
- [ ] **Rejection (`< 85%` success rate):** Critical functional failures, RBAC security flaws, or raw-data integrity violations present; return to development required.

**Final Decision (S12):** `PENDING`
