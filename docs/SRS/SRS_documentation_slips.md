# SRS Chapter 8 - Detailed Feature Specifications (Documentation Slips)

**Version:** 0.1  
**Date:** 2026-11-23  
**Note:** Replace `[Author Name]` with the assigned team member's full name before final SRS submission.

---

## UC-01: Authenticate User (`FR-01`)

| Field | Details |
| :--- | :--- |
| **Name** | `UC-01` - Authenticate User (Login / Logout) |
| **Author** | `[Member A Name]` |
| **Date** | 2026-11-23 |
| **Objective** | Allow a registered `User` or `Admin` to securely log in with username and password, establish a role-scoped session, and log out safely. |
| **Precondition** | The application is running; the `users.csv` credential file exists and is readable; the user is not currently authenticated. |
| **Postcondition** | On login: an authenticated session is created with the user's role (`User` or `Admin`) and authorized `Home ID` list, and the dashboard is displayed. On logout: the session is cleared and the login screen is shown. |
| **Invariant** | Unauthenticated visitors cannot access any consumption data, charts, predictions, or export features. |
| **Description** | Verifies user credentials against stored hashed passwords and binds the active session to the user's role and authorized households. |
| **Visible Actions** | `Va1`: User opens the application and sees the login form.<br>`Va2`: User enters username and password.<br>`Va3`: User clicks "Login".<br>`Va4`: System validates credentials and loads the role-appropriate dashboard with a welcome banner.<br>`Va5`: (Later) User clicks "Logout" and returns to the login form. |
| **Scenarios** | `Sc1` (Nominal): Valid username and password -> session initialized -> redirect to dashboard.<br>`ScA1` (Alternative): Authenticated user clicks "Logout" -> session cleared -> redirect to login screen.<br>`ScE1` (Error): Incorrect password -> display `"Invalid username or password"`, no session created.<br>`ScE2` (Error): Non-existent username -> display `"Invalid username or password"`, no session created.<br>`ScE3` (Error): Empty username or password field -> display `"Username and password are required"`. |
| **Business Rules** | `Br1`: Passwords must never be stored or logged in plain text (use salted hash, e.g., SHA-256 / PBKDF2).<br>`Br2`: `User` accounts are strictly restricted to their linked `Home ID`(s); `Admin` accounts receive access to all 500 households.<br>`Br3`: Login verification must complete within 1 second (`NFR-01`). |

---

## UC-02: Ingest Raw Dataset (`FR-02`)

| Field | Details |
| :--- | :--- |
| **Name** | `UC-02` - Ingest Raw Dataset (Load CSV) |
| **Author** | `[Member A Name]` |
| **Date** | 2026-11-23 |
| **Objective** | Allow an `Admin` to load the raw household electricity consumption CSV file into the normalized CSV data model while preserving all raw records unaltered. |
| **Precondition** | Actor is authenticated as `Admin` (`UC-01`); raw CSV file is available on disk or uploaded via the Admin panel. |
| **Postcondition** | Normalized relational CSV tables (`households.csv`, `appliances.csv`, `measurements.csv`) are generated/updated in `data/processed/` with Primary Key and Foreign Key integrity verified; ingestion summary (row count, homes count) is displayed. |
| **Invariant** | Raw values (including temperature fluctuations, seasonal contradictions, and per-row household size) are preserved 100% faithfully in storage (`NFR-02`). |
| **Description** | Parses the raw `cp1252`-encoded CSV file (100,000 rows, 500 European smart homes), validates required columns and key integrity, normalizes entities into linked CSV tables without dropping or altering inconsistent measurements, and writes them to `data/processed/`. |
| **Visible Actions** | `Va1`: Admin navigates to the "Data Management" section.<br>`Va2`: Admin selects/uploads the raw CSV file and clicks "Load Dataset".<br>`Va3`: System parses, validates schema, normalizes into relational CSV files, and shows a progress indicator.<br>`Va4`: System displays confirmation with total records loaded (100,000) and unique households (500). |
| **Scenarios** | `Sc1` (Nominal): Valid `cp1252` CSV with all 8 required columns -> normalized files written -> success summary shown.<br>`ScA1` (Alternative): Processed CSV files already exist -> Admin confirms reload -> existing normalized files are cleanly overwritten.<br>`ScE1` (Error): Non-Admin attempts to access ingestion -> access denied.<br>`ScE2` (Error): Missing required column(s) or corrupted file -> ingestion aborted, existing data preserved, error message displayed.<br>`ScE3` (Error): File not found or unreadable encoding -> graceful error message displayed. |
| **Business Rules** | `Br1`: Only `Admin` role can trigger data ingestion (`NFR-03`).<br>`Br2`: Parser must explicitly handle `cp1252` encoding (for the `"°"` character in `Outdoor Temperature (°C)`).<br>`Br3`: No raw rows may be dropped or overwritten during ingestion; cleaning is strictly prohibited before the AI module (`NFR-02`). |

---

## UC-03: View Aggregated Consumption (`FR-03`)

| Field | Details |
| :--- | :--- |
| **Name** | `UC-03` - View Aggregated Consumption (Day / Month / Year) |
| **Author** | `[Member B Name]` |
| **Date** | 2026-11-23 |
| **Objective** | Display electricity consumption time-series for a selected authorized household, defaulting to daily aggregation with interactive switching to monthly or yearly views. |
| **Precondition** | Actor is authenticated (`UC-01`); normalized dataset is loaded (`UC-02`); actor has at least one authorized `Home ID`. |
| **Postcondition** | A labeled consumption chart (total kWh over time) and key summary metrics (total kWh, daily average, peak date) are rendered for the chosen household and granularity. |
| **Invariant** | Displayed data strictly belongs to authorized `Home ID`(s) and reflects unaltered raw measurements (`NFR-02`, `NFR-03`). |
| **Description** | Aggregates `Energy Consumption (kWh)` by the chosen time granularity (`Daily` by default, `Monthly`, or `Yearly`) and optional date range, rendering a responsive Matplotlib/Seaborn chart. |
| **Visible Actions** | `Va1`: User lands on the Dashboard; system automatically loads the first authorized household in **Daily** view.<br>`Va2`: User selects another authorized `Home ID` (if multiple are available).<br>`Va3`: User switches aggregation granularity between `Daily`, `Monthly`, and `Yearly`.<br>`Va4`: System updates the chart and summary KPIs within 2 seconds. |
| **Scenarios** | `Sc1` (Nominal): Authorized household selected, default Daily view -> chart renders with daily kWh totals.<br>`ScA1` (Alternative): User switches to `Monthly` or `Yearly` -> x-axis and totals re-aggregate accordingly.<br>`ScA2` (Alternative): User narrows the date range -> chart zooms to selected dates.<br>`ScE1` (Error): `User` attempts to query an unassigned `Home ID` -> backend blocks request and displays `"Access denied"`.<br>`ScE2` (Error): No records exist for the selected date range -> display `"No consumption data available for the selected filters"`. |
| **Business Rules** | `Br1`: Default granularity upon dashboard load MUST be **Daily** (`FR-03`).<br>`Br2`: Rendering must complete within 2.0 seconds (`NFR-01`).<br>`Br3`: Chart must include clear axis labels (`Date / Period`, `Energy Consumption (kWh)`), title, and legend. |

---

## UC-04: Compare Households (`FR-04`)

| Field               | Details                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| :------------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Name**            | `UC-04` - Compare Households (Up to 5 Homes)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **Author**          | `[Member B Name]`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| **Date**            | 2026-11-23                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **Objective**       | Enable simultaneous visual comparison of up to 5 authorized households on a single chart, each rendered in a distinct color.                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **Precondition**    | Actor is authenticated (`UC-01`); normalized dataset is loaded (`UC-02`); actor has access to at least 2 authorized households.                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| **Postcondition**   | An overlaid multi-series chart displays the selected households (2 to 5) with a distinct color per household and a clear legend.                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **Invariant**       | Maximum 5 households may be compared simultaneously; every compared household must pass RBAC authorization (`NFR-03`).                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **Description**     | Allows `Admin` (from all 500 homes) or multi-home `User` (from their assigned homes) to select between 2 and 5 households and compare their daily, monthly, or yearly consumption curves side by side.                                                                                                                                                                                                                                                                                                                                                                                               |
| **Visible Actions** | `Va1`: User opens the household multi-selector control.<br>`Va2`: User selects 2 to 5 authorized `Home ID`s.<br>`Va3`: User chooses granularity (`Daily` / `Monthly` / `Yearly`).<br>`Va4`: System plots each household's curve in a unique, high-contrast color with a matching legend.                                                                                                                                                                                                                                                                                                             |
| **Scenarios**       | `Sc1` (Nominal): User selects 3 authorized households -> 3 distinct colored curves rendered on shared axes.<br>`ScA1` (Alternative): User removes one household -> chart updates immediately to 2 curves.<br>`ScE1` (Error): User attempts to select a 6th household -> UI prevents selection and displays `"Maximum 5 households can be compared simultaneously"`.<br>`ScE2` (Error): A `User` linked to only 1 household opens comparison -> info message explains only 1 household is assigned.<br>`ScE3` (Error): Unauthorized `Home ID` injected in request -> backend raises permission error. |
| **Business Rules**  | `Br1`: Hard upper limit of 5 simultaneous households (`FR-04`).<br>`Br2`: Distinct colorblind-friendly palette must be used so no two households share the same color.<br>`Br3`: Works seamlessly with `UC-05` (global average overlay) and `UC-06` (appliance filter).                                                                                                                                                                                                                                                                                                                              |

---

## UC-05: Overlay Benchmark Curve (`FR-05`)

| Field | Details |
| :--- | :--- |
| **Name** | `UC-05` - Overlay Global Average Benchmark Curve |
| **Author** | `[Member B Name]` |
| **Date** | 2026-11-23 |
| **Objective** | Overlay the average electricity consumption curve (per day, month, or year) across all 500 households onto the active household chart. |
| **Precondition** | Actor is viewing a valid consumption or comparison chart (`UC-03` or `UC-04`). |
| **Postcondition** | A visually distinct benchmark line (e.g., dashed black/grey line labeled `"All-Households Average"`) is overlaid on the existing chart at matching time granularity. |
| **Invariant** | The benchmark curve reflects the anonymized mean across all households and exposes no individual data of other residents (`NFR-03`). |
| **Description** | Computes the mean per-household consumption across all 500 homes for each day, month, or year (respecting active appliance filters when applicable) and plots it over the selected household series. |
| **Visible Actions** | `Va1`: User toggles the "Show Global Average Curve" checkbox on.<br>`Va2`: System computes (or retrieves cached) all-household mean for the active granularity.<br>`Va3`: Chart refreshes with the dashed average curve overlaid and added to the legend. |
| **Scenarios** | `Sc1` (Nominal): User enables overlay on Daily view -> dashed global average curve appears over selected home(s).<br>`ScA1` (Alternative): User switches from Daily to Monthly while overlay is active -> benchmark curve automatically recalculates at Monthly granularity.<br>`ScA2` (Alternative): User toggles overlay off -> benchmark curve disappears.<br>`ScE1` (Error): All appliances are excluded via `UC-06` -> no curve plotted, empty-filter warning shown. |
| **Business Rules** | `Br1`: Global average is computed as `sum(kWh across all homes in period) / number_of_active_homes_in_period` (mean per household, not raw total).<br>`Br2`: Visually differentiated from household curves (e.g., dashed line style) so it cannot be confused with an individual home.<br>`Br3`: Accessible to both `User` and `Admin` roles. |

---

## UC-06: Filter Appliance Sources (`FR-06`)

| Field | Details |
| :--- | :--- |
| **Name** | `UC-06` - Filter Appliance Sources |
| **Author** | `[Member B Name]` |
| **Date** | 2026-11-23 |
| **Objective** | Allow users to filter electricity consumption by including or excluding specific appliance types (e.g., excluding Refrigerators) across visualizations. |
| **Precondition** | Actor is viewing `UC-03` or `UC-04`; the 10 appliance types are loaded from `appliances.csv`. |
| **Postcondition** | The consumption chart, KPI totals, and (if active) global average curve update to reflect only the selected appliance types. |
| **Invariant** | Filtering operates on in-memory query views only and never modifies underlying stored CSV files (`NFR-02`). |
| **Description** | Provides a multi-select or checkbox filter over all 10 appliance categories (Air Conditioning, Heater, Fridge, Oven, Microwave, Washing Machine, Dishwasher, TV, Computer, Lights), supporting quick "Select All" and "Exclude Fridge" workflows. |
| **Visible Actions** | `Va1`: User views the Appliance Filter panel (all 10 appliances selected by default).<br>`Va2`: User unchecks one or more appliances (e.g., `Fridge`).<br>`Va3`: System recomputes aggregated kWh excluding unchecked appliances and redraws the chart within 500 ms. |
| **Scenarios** | `Sc1` (Nominal): User unchecks `Fridge` -> chart re-renders showing total consumption excluding refrigerators.<br>`ScA1` (Alternative): User selects only `Air Conditioning` and `Heater` -> chart isolates HVAC consumption.<br>`ScA2` (Alternative): User clicks "Reset / Select All" -> full consumption restored.<br>`ScE1` (Error): User deselects all appliances -> system displays `"Please select at least one appliance type"` instead of crashing. |
| **Business Rules** | `Br1`: All 10 appliance types are included by default.<br>`Br2`: Filter re-render latency must be under 500 ms (`NFR-01`).<br>`Br3`: When `UC-05` (Global Average) is active, the same appliance filter is applied to the benchmark for apples-to-apples comparison. |

---

## UC-07: Predict Consumption with AI (`FR-07`)

| Field | Details |
| :--- | :--- |
| **Name** | `UC-07` - Predict Electricity Consumption with AI |
| **Author** | `[Member C Name]` |
| **Date** | 2026-11-23 |
| **Objective** | Train predictive baseline models on the dataset (with cleaning isolated inside the ML pipeline) and predict electricity consumption given forecast outdoor temperature and household characteristics. |
| **Precondition** | Actor is authenticated (`UC-01`); normalized dataset is loaded (`UC-02`); actor selects an authorized `Home ID` or valid house characteristics. |
| **Postcondition** | Predicted consumption (kWh) is displayed alongside transparent model evaluation metrics (`R²`, `MAE`, `RMSE`) for both baselines (Statsmodels OLS and Scikit-learn Tree/Ensemble model). |
| **Invariant** | Any data cleaning performed for model training occurs strictly on an in-memory copy inside the ML module and NEVER alters the persisted CSV files (`NFR-02`). |
| **Description** | Cleans a training copy of the dataset inside `prediction_service.py` (e.g., deriving consistent Season from Date, handling per-home Household Size summary, optional outlier checks), trains two baseline models (Statsmodels OLS + Scikit-learn Random Forest / Gradient Boosting), evaluates them on a hold-out test split, and runs inference for user-supplied forecast temperature, season, household size, and appliance/scope. |
| **Visible Actions** | `Va1`: User opens the "AI Prediction" tab.<br>`Va2`: User selects an authorized household (auto-filling its characteristics) or enters forecast `Outdoor Temperature (°C)`, `Household Size`, `Season`, and optional `Appliance Type`.<br>`Va3`: User selects model (Statsmodels OLS or Scikit-learn baseline) and clicks "Predict".<br>`Va4`: System displays predicted kWh, model performance metrics (`R²`, `MAE`, `RMSE`), and a diagnostic note on weather-consumption correlation. |
| **Scenarios** | `Sc1` (Nominal): User enters `Outdoor Temperature = 28.0°C`, `Household Size = 3`, `Season = Summer` -> system outputs predicted kWh and test metrics.<br>`ScA1` (Alternative): User switches between Statsmodels OLS and Scikit-learn model -> predictions and metrics update for comparison.<br>`ScE1` (Error): Out-of-range temperature (e.g., `-100°C` or `100°C`) or non-positive household size (`0` or `-2`) -> validation error displayed, no prediction run.<br>`ScE2` (Error): Model training fails due to missing dataset -> clear error message shown. |
| **Business Rules** | `Br1`: Data cleaning is strictly isolated inside the ML training pipeline (`NFR-02`).<br>`Br2`: Model metrics (`R²`, `MAE`, `RMSE`) must be reported honestly on a train/test split; if weather-to-energy correlation is near zero, the UI must transparently report low predictive power rather than fabricating high accuracy.<br>`Br3`: Must include a `Statsmodels` model to fulfill course prerequisites (`Project_Subject PAGE 1`). |

---

## UC-08: Export Summary Report (`FR-08` - Bonus)

| Field | Details |
| :--- | :--- |
| **Name** | `UC-08` - Export Summary Report (Bonus) |
| **Author** | `[Member C Name]` |
| **Date** | 2026-11-23 |
| **Objective** | Generate and download a monthly and yearly summary report containing total and per-resident electricity consumption for selected authorized households. |
| **Precondition** | Actor is authenticated (`UC-01`); normalized dataset is loaded (`UC-02`); at least one authorized household is selected. |
| **Postcondition** | A structured summary report file (`.csv`) is generated and downloaded to the user's machine with columns for Household, Period (Month/Year), Total Consumption (kWh), Reference Household Size, and Per-Resident Consumption (kWh/person). |
| **Invariant** | Exported report contains only households authorized for the active user (`NFR-03`) and is computed from unaltered stored records (`NFR-02`). |
| **Description** | Aggregates monthly and yearly total consumption for the selected authorized household(s), computes per-resident consumption using a documented household-size rule (mean/latest recorded household size for that period), previews the summary table on screen, and provides a one-click file download. |
| **Visible Actions** | `Va1`: User navigates to the "Export Report" section.<br>`Va2`: User selects one or more authorized households and report period (`Monthly`, `Yearly`, or `Both`).<br>`Va3`: User clicks "Generate Preview".<br>`Va4`: System displays the summary table preview.<br>`Va5`: User clicks "Download CSV Report" and saves the file locally. |
| **Scenarios** | `Sc1` (Nominal): User selects 2 authorized homes and `Monthly` -> preview renders -> CSV downloads successfully.<br>`ScA1` (Alternative): Admin selects all 500 homes for a `Yearly` summary -> report generates and downloads within performance limits.<br>`ScE1` (Error): No household selected -> "Download" disabled with warning `"Select at least one household"`.<br>`ScE2` (Error): `User` attempts to export an unassigned household -> backend blocks export with permission error. |
| **Business Rules** | `Br1`: Per-resident consumption formula must be explicitly defined and documented (`Total kWh / Mean Household Size for that home & period`, preventing division by zero).<br>`Br2`: Exported CSV uses UTF-8 encoding with clear English column headers.<br>`Br3`: Export generation for up to 500 homes must complete within 2.0 seconds (`NFR-01`). |
