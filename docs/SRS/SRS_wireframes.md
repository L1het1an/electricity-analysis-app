# SRS Chapter 5 - Interface Design (Wireframes)

**Version:** 0.1  
**Date:** 2026-11-23  
**Purpose:** Visual layout blueprints for the two core screens of the Streamlit application. Convert these two layouts into clean PNGs (using draw.io / Excalidraw / Figma) and insert them into **SRS Section 5 (Interface design)**.

---

## Screen 1: Login Screen (`UC-01`)

```text
+------------------------------------------------------------------------+
|                  ⚡ Household Electricity Analysis                      |
|                       European Smart Home Portal                       |
+------------------------------------------------------------------------+
|                                                                        |
|                    +------------------------------+                    |
|                    |        Sign In               |                    |
|                    |                              |                    |
|                    |  Username                    |                    |
|                    |  [ ________________________ ]|                    |
|                    |                              |                    |
|                    |  Password                    |                    |
|                    |  [ •••••••••••••••••••••••• ]|                    |
|                    |                              |                    |
|                    |  [         Login          ]  |                    |
|                    |                              |                    |
|                    |  (Error banner if invalid)   |                    |
|                    +------------------------------+                    |
|                                                                        |
+------------------------------------------------------------------------+
```

**Design Guidelines:**
- Centered card layout, clean white/light-grey background, high-contrast primary action button.
- Password input masked by default; inline validation error displayed below the button without crashing or exposing whether the username exists.

---

## Screen 2: Main Dashboard, Comparison & AI Prediction (`UC-02`–`UC-08`)

```text
+------------------------------------------------------------------------+
| ⚡ Household Electricity Analysis   | Logged in as: admin (Admin) [Logout] |
+--------------------+---------------------------------------------------+
|   SIDEBAR CONTROLS |  [ 📊 Analytics & Compare ] [ 🤖 AI Predict ]     |
|                    |  [ 📄 Export Report ]  [ ⚙️ Admin Data (Admin) ]  |
|  1. Households     +---------------------------------------------------+
|  [ Home_001   x ]  |  KPI Row:                                         |
|  [ Home_012   x ]  |  [ Total: 1,245 kWh ] [ Avg/Day: 3.4 kWh ]        |
|  (+ up to 5 max)   |  [ Peak Date: 2023-07-18 ] [ Selected: 2 Homes ]  |
|                    +---------------------------------------------------+
|  2. Granularity    |                                                   |
|  (•) Daily         |     Consumption Over Time (Daily, kWh)            |
|  ( ) Monthly       |   kWh ^                                           |
|  ( ) Yearly        |       |   /\    /\_  Home_001 (Blue)              |
|                    |       |  /  \  /   \ Home_012 (Orange)            |
|  3. Benchmark      |       | - - - - - -  All-Homes Avg (Dashed Black) |
|  [x] Show Global   |       +------------------------------------> Date |
|      Average Curve |                                                   |
|                    +---------------------------------------------------+
|  4. Appliance      |  Appliance Breakdown / Summary Table              |
|     Filter         |  +------------+-----------+-----------------+     |
|  [x] AC  [x] Heater|  | Home ID    | Total kWh | Per-Resident kWh|     |
|  [ ] Fridge        |  +------------+-----------+-----------------+     |
|  [x] Oven  ...     |  | Home_001   | 640.2     | 213.4           |     |
|  [Reset All]       |  +------------+-----------+-----------------+     |
+--------------------+---------------------------------------------------+
```

**Design Guidelines:**
- **Left Sidebar:** Persistent global filters (RBAC-filtered household multi-select capped at 5, Daily/Monthly/Yearly radio, Global Average checkbox, 10-appliance checkboxes).
- **Top Navigation Tabs:** Clean separation of **Analytics & Compare**, **AI Prediction**, **Export Report**, and **Admin Data** (hidden for `User` role).
- **Visual Clarity:** Colorblind-safe distinct palette for up to 5 homes + dashed black line for the global average curve.
