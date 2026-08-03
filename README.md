# 🏨 Hotel Dynamic Pricing Engine

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-3.3%2B-orange.svg)](https://xgboost.readthedocs.io/)
[![React 19](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind_CSS-v4-38bdf8.svg)](https://tailwindcss.com/)
[![Docker Compose](https://img.shields.io/badge/Docker_Compose-Supported-2496ed.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-style, **cancellation-risk-aware dynamic pricing recommender system** designed for independent and boutique hotels.

The system uses an **XGBoost classification model** (39 engineered features, Optuna hyperparameter tuning, native `scale_pos_weight` class balancing, validation-set threshold optimization) as a **counterfactual demand proxy**. By evaluating predicted cancellation probabilities across a range of room rates, the pricing engine generates a **price-response curve** and recommends the rate that maximizes **expected revenue** under real-world occupancy-pacing constraints.

---

## 📸 System Overview & Features

- **Counterfactual Price Simulator:** Sweeps room prices across a custom grid to model $E[\text{Revenue}] = \text{Price} \times (1 - P_{\text{cancel}})$.
- **Occupancy-Pacing Constraints:** Automatically enforces business rules (e.g., blocking discounts when occupancy $\ge 85\%$, allowing aggressive last-minute discounts when occupancy $\le 30\%$).
- **Calibrated Risk Bands:** Uses a validation-set-tuned decision threshold ($T \approx 0.495$) to classify booking risks into `Low`, `Medium`, and `High` bands.
- **Interactive Recommender Dashboard:** Built with React 19, Tailwind CSS v4, and Recharts for live visualization of expected revenue curves.
- **Auditable Prediction History:** Persists pricing runs to a PostgreSQL database for reporting and auditability.

---

## 🏗️ System Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           React 19 Single Page App                          │
│     Recommender Dashboard   │   Prediction History   │   System Specs       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ POST /predict/*
                                       │ GET  /history
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             FastAPI Backend API                             │
│  ┌───────────────────────────────┐     ┌─────────────────────────────────┐  │
│  │   Inference Module            │     │   Pricing Engine                │  │
│  │   - Feature Engineering (39)  │ ──► │   - Base Price Lookup (Segment) │  │
│  │   - XGBoost Inference         │     │   - Price Grid Simulator        │  │
│  │   - Threshold Classification  │     │   - Occupancy Pacing Rules      │  │
│  └──────────────┬────────────────┘     └────────────────┬────────────────┘  │
└─────────────────┼───────────────────────────────────────┼───────────────────┘
                  │ Loads Artifacts                       │ SQL Queries
                  ▼                                       ▼
┌───────────────────────────────────┐   ┌───────────────────────────────────┐
│     Trained Artifacts Directory   │   │       PostgreSQL Database         │
│  ├── model_v1.joblib (XGBoost)    │   │   - pricing_requests (History)    │
│  ├── encoders_v1.joblib           │   │                                   │
│  └── feature_metadata_v1.json     │   │                                   │
└───────────────────────────────────┘   └───────────────────────────────────┘
```

---

## 🤖 Machine Learning Pipeline

### 1. Data Cleaning & Temporal Splitting

- **Raw Data:** 119,390 hotel booking records spanning 2015 to 2017.
- **Cleaning:** Deduplicated 32,252 exact duplicate rows $\rightarrow$ **87,138 cleaned records**.
- **Temporal Split:** Sorted chronologically by arrival year/week to ensure no future data leaks into the past.
  - **Training Set (70%):** 60,996 records
  - **Validation Set (15%):** 13,071 records
  - **Test Set (15%):** 13,071 records

### 2. Class Balancing & Feature Scale Invariance

- **Native XGBoost Class Balancing:** Class imbalance (~25% cancellation rate) is handled solely through XGBoost's `scale_pos_weight` parameter, which Optuna tunes automatically. SMOTE was intentionally avoided because it (a) breaks mathematical consistency between derived features (e.g., interpolated `lead_time_squared` ≠ `lead_time²`), (b) generates fake in-between LabelEncoded categorical values, and (c) double-corrects for imbalance when combined with `scale_pos_weight`.
- **Scale Invariance:** `StandardScaler` was intentionally omitted as XGBoost is invariant to monotonic feature transformations, simplifying inference and preventing scaler-drift skew.

### 3. Complete Feature Engineering Specification (39 Features)

The pipeline transforms raw booking inputs into **39 engineered numerical features**:

| Category                           | Feature Name                       | Description / Formula                                                        | Value Range / Type              |
| :--------------------------------- | :--------------------------------- | :--------------------------------------------------------------------------- | :------------------------------ |
| **Temporal (8)**             | `lead_time`                      | Days between booking date and arrival date                                   | `0` – `737` (Integer)      |
|                                    | `lead_time_log`                  | $\ln(\text{lead\_time} + 1)$ for non-linear scaling                        | `0.0` – `6.6` (Float)      |
|                                    | `lead_time_squared`              | $(\text{lead\_time})^2$ to amplify far-ahead bookings                      | `0` – `543,169` (Float)    |
|                                    | `is_last_minute`                 | Binary flag for$\text{lead\_time} \le 3$ days                              | `0` or `1` (Binary)         |
|                                    | `is_far_ahead`                   | Binary flag for$\text{lead\_time} > 365$ days                              | `0` or `1` (Binary)         |
|                                    | `is_peak_season`                 | Binary flag for arrival in June, July, Aug, or Dec                           | `0` or `1` (Binary)         |
|                                    | `arrival_date_month`             | Numerical month of arrival                                                   | `1` – `12` (Integer)       |
|                                    | `weekend_nights_ratio`           | $\text{weekend\_nights} / (\text{total\_nights} + 0.001)$                  | `0.0` – `1.0` (Float)      |
| **Guest Behaviour (8)**      | `total_nights`                   | Sum of week and weekend nights                                               | `1` – `365` (Integer)      |
|                                    | `total_guests`                   | Sum of adults, children, and babies                                          | `1` – `10+` (Integer)      |
|                                    | `is_repeated_guest`              | Flag indicating if guest stayed previously                                   | `0` or `1` (Binary)         |
|                                    | `previous_cancellations`         | Count of prior cancelled bookings                                            | `0` – `26+` (Integer)      |
|                                    | `previous_bookings_not_canceled` | Count of prior successful stays                                              | `0` – `72+` (Integer)      |
|                                    | `loyalty_score`                  | $(3 \times \text{repeat}) + (2 \times \text{success}) - \text{cancels}$    | Integer                         |
|                                    | `cancellation_rate_history`      | $\text{cancels} / (\text{cancels} + \text{success} + 1)$                   | `0.0` – `1.0` (Float)      |
|                                    | `is_high_maintenance`            | Flag for$>2$ changes, $>3$ requests, or $>7$ wait days                 | `0` or `1` (Binary)         |
| **Pricing (4)**              | `adr`                            | Average Daily Rate (Price per night)                                         | `$0.0` – `$500.0+` (Float) |
|                                    | `adr_zscore`                     | Normalized ADR vs training set mean/std                                      | Float                           |
|                                    | `is_premium`                     | Binary flag if$\text{adr} > \text{75th percentile}$                        | `0` or `1` (Binary)         |
|                                    | `revenue_per_guest_night`        | $\text{adr} / (\text{total\_guests} + 0.001)$                              | Float                           |
| **Other Details (6)**        | `room_mismatch`                  | Flag if assigned room != reserved room                                       | `0` or `1` (Binary)         |
|                                    | `required_car_parking_spaces`    | Number of requested parking spaces                                           | `0` – `8` (Integer)        |
|                                    | `total_of_special_requests`      | Count of special requests (high floor, twin bed, etc.)                       | `0` – `5` (Integer)        |
|                                    | `days_in_waiting_list`           | Days on waiting list prior to confirmation                                   | `0` – `391` (Integer)      |
|                                    | `booking_changes`                | Number of modifications made to booking                                      | `0` – `21` (Integer)       |
|                                    | `is_small_hotel`                 | Flag for City Hotel (1) vs Resort Hotel (0)                                  | `0` or `1` (Binary)         |
| **Interactions (7)**         | `leadtime_x_adr`                 | $\text{lead\_time} \times \text{adr}$                                      | Float                           |
|                                    | `leadtime_x_changes`             | $\text{lead\_time} \times \text{booking\_changes}$                         | Float                           |
|                                    | `leadtime_x_nights`              | $\text{lead\_time} \times \text{total\_nights}$                            | Float                           |
|                                    | `guests_x_requests`              | $\text{total\_guests} \times \text{total\_of\_special\_requests}$          | Float                           |
|                                    | `adr_x_requests`                 | $\text{adr} \times \text{total\_of\_special\_requests}$                    | Float                           |
|                                    | `nonrefund_x_leadtime`           | $(\text{deposit} == \text{"Non Refund"}) \times \text{lead\_time}$         | Float                           |
|                                    | `repeat_cancel_nodeposit`        | $(\text{prev\_cancels} > 0) \land (\text{deposit} == \text{"No Deposit"})$ | `0` or `1` (Binary)         |
| **Encoded Categoricals (6)** | `deposit_type`                   | `LabelEncoder`: No Deposit, Non Refund, Refundable                         | Encoded Integer                 |
|                                    | `meal`                           | `LabelEncoder`: BB, HB, FB, SC, Undefined                                  | Encoded Integer                 |
|                                    | `distribution_channel`           | `LabelEncoder`: Direct, Corporate, TA/TO, GDS, Undefined                   | Encoded Integer                 |
|                                    | `market_segment`                 | `LabelEncoder`: Direct, Corporate, Online TA, Offline TA/TO, etc.          | Encoded Integer                 |
|                                    | `customer_type`                  | `LabelEncoder`: Transient, Contract, Transient-Party, Group                | Encoded Integer                 |
|                                    | `country`                        | `LabelEncoder`: PRT, GBR, USA, ESP, FRA, DEU, etc.                         | Encoded Integer                 |

### 4. Hyperparameter Optimization & Early Stopping

- **Optuna TPE Sampler:** 30 trials optimizing directly for **Validation ROC-AUC** (instead of standard accuracy).
- **Early Stopping:** Monitored validation AUC using `xgb.callback.EarlyStopping`. The final training run stopped at **iteration 454** (max 1217), preventing overfitting.
- **Tuned Hyperparameters:**
  ```python
  {
    "n_estimators": 1217,
    "max_depth": 7,
    "learning_rate": 0.01798,
    "subsample": 0.6028,
    "colsample_bytree": 0.8188,
    "min_child_weight": 1,
    "gamma": 0.8994,
    "reg_alpha": 1.3793,
    "reg_lambda": 1.9905,
    "scale_pos_weight": 2.6368
  }
  ```

### 5. Validation-Set Threshold Tuning

Rather than defaulting to an arbitrary `0.50` probability threshold, the decision threshold was optimized on the validation set to maximize F1-score:

- **Tuned Threshold:** `0.4954`
- **Impact:** Increases cancellation recall from **53.7%** to **73.53%**, ensuring the pricing engine catches 887+ additional true cancellations on the test set.

### 6. Model Performance Metrics (Temporal Test Set: 13,071 bookings)

| Metric                                  | Baseline Model (37 Features, 10 Trials) | Improved Model (39 Features, 30 Trials, ROC-AUC) |           Delta           |
| :-------------------------------------- | :-------------------------------------: | :----------------------------------------------: | :------------------------: |
| **ROC-AUC**                       |                 79.70%                 |                 **81.45%**                 |     **+1.75pp**     |
| **Recall (Cancellations Caught)** |                 53.70%                 |                 **73.53%**                 |     **+19.83pp**     |
| **F1-Score**                      |                 58.70%                 |                 **64.84%**                 |     **+6.14pp**     |
| **Accuracy**                      |                 74.20%                 |                 **72.76%**                 | -1.44pp (Recall trade-off) |
| **Precision**                     |                 64.80%                 |                 **57.98%**                 | -6.82pp (Recall trade-off) |

---

## 💡 Pricing Engine & Counterfactual Simulator

### 1. Counterfactual Demand Simulation

Because real-world experimental price elasticity data is unobserved in historical datasets, the system uses the trained XGBoost model as a **counterfactual demand proxy**:

1. For a given booking context, lookup the base market price $P_{\text{base}}$ for that `market_segment` $\times$ `season`.
2. Generate a grid of 25 candidate prices spanning $[0.70 \times P_{\text{base}}, 1.50 \times P_{\text{base}}]$.
3. For each candidate price $P$, recompute all price-dependent features (`adr`, `adr_zscore`, `leadtime_x_adr`, `adr_x_requests`, etc.) and evaluate predicted cancellation probability $P_{\text{cancel}}(P)$.
4. Calculate expected revenue:
   $$
   E[\text{Revenue}](P) = P \times (1 - P_{\text{cancel}}(P))
   $$

### 2. Occupancy-Pacing Constraints

To align ML predictions with hotel revenue management principles, the optimizer enforces three pacing rules:

- **Near-Sellout ($\text{Occupancy} \ge 85\%$):** Discounts are strictly blocked ($P \ge P_{\text{base}}$).
- **Last-Minute Distress ($\text{Occupancy} \le 30\%$ and $\text{Lead Time} \le 7$ days):** Allows the full discount range down to $0.70 \times P_{\text{base}}$ to drive volume.
- **Normal Pacing Band (Default):** Restricts recommended price to $[0.85 \times P_{\text{base}}, 1.25 \times P_{\text{base}}]$.

### 3. Risk Category Classification

Cancellation risk is categorized into three bands relative to the tuned decision threshold $T \approx 0.4954$:

- **`Low`:** $P_{\text{cancel}} < 0.75 \times T$ ($P_{\text{cancel}} < 37.1\%$)
- **`Medium`:** $0.75 \times T \le P_{\text{cancel}} \le 1.50 \times T$ ($37.1\% \le P_{\text{cancel}} \le 74.3\%$)
- **`High`:** $P_{\text{cancel}} > 1.50 \times T$ ($P_{\text{cancel}} > 74.3\%$)

---

## ⚡ API Specification (FastAPI)

### Endpoints Overview

| Method   | Endpoint                       | Description                                                       |
| :------- | :----------------------------- | :---------------------------------------------------------------- |
| `GET`  | `/health`                    | Health check endpoint returning database connectivity status      |
| `POST` | `/predict/cancellation-risk` | Returns predicted cancellation probability & risk band            |
| `POST` | `/predict/recommend-price`   | Runs counterfactual price curve simulation & returns optimal rate |
| `GET`  | `/history`                   | Fetches historical price recommendation records from PostgreSQL   |

### Example Request (`POST /predict/recommend-price`)

```json
{
  "hotel_type": "City Hotel",
  "lead_time": 45,
  "arrival_month": 7,
  "total_nights": 3,
  "total_guests": 2,
  "market_segment": "Online TA",
  "distribution_channel": "TA/TO",
  "customer_type": "Transient",
  "deposit_type": "No Deposit",
  "meal": "BB",
  "country": "PRT",
  "is_repeated_guest": false,
  "previous_cancellations": 0,
  "previous_bookings_not_canceled": 0,
  "booking_changes": 0,
  "total_of_special_requests": 1,
  "required_car_parking_spaces": 0,
  "days_in_waiting_list": 0,
  "room_mismatch": false,
  "current_occupancy_rate": 0.65
}
```

### Example Response (`POST /predict/recommend-price`)

```json
{
  "recommended_price": 118.50,
  "price_multiplier": 1.0543,
  "expected_revenue": 76.23,
  "cancellation_probability_at_recommended_price": 0.3567,
  "constraint_applied": "normal pacing band",
  "price_curve": [
    { "price": 78.50, "cancellation_probability": 0.2810, "expected_revenue": 56.44 },
    { "price": 118.50, "cancellation_probability": 0.3567, "expected_revenue": 76.23 },
    { "price": 168.50, "cancellation_probability": 0.6240, "expected_revenue": 63.36 }
  ]
}
```

---

## 🛠️ Quick Start & Local Setup

### Prerequisites

- **Python:** 3.11+
- **Node.js:** 18+
- **Docker Desktop:** Required for containerized execution (PostgreSQL & Backend)

---

### Option A: Running with Docker Compose (Recommended)

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/vatsal/hotel-pricing-engine.git
   cd hotel-pricing-engine
   ```
2. **Train the Model (Generates required artifacts):**

   ```bash
   python training/src/train_cancellation_model.py
   ```
3. **Launch Docker Services:**

   ```bash
   docker compose up --build -d
   ```

   - **Backend API:** Available at `http://localhost:8000` (Swagger docs: `http://localhost:8000/docs`)
   - **PostgreSQL Database:** Port `5432`
4. **Start Frontend Dev Server:**

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

   - **React Application:** Available at `http://localhost:5173`

---

### Option B: Native Development Setup (No Docker)

1. **Backend Setup:**

   ```bash
   cd backend
   # Create a local SQLite environment
   echo DATABASE_URL="sqlite:///./pricing.db" > .env
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
2. **Frontend Setup:**

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 🧪 Testing & Quality Assurance

The project includes an automated **37-test suite** covering feature engineering logic, price curve optimization calculations, and FastAPI endpoint contracts.

### Run All Tests

```bash
python -m pytest backend/tests/ -v --tb=short
```

```
backend/tests/test_api.py::test_health PASSED                            [  2%]
backend/tests/test_api.py::test_cancellation_risk_valid PASSED           [  5%]
backend/tests/test_api.py::test_recommend_price_valid PASSED             [ 13%]
backend/tests/test_features.py::test_produces_39_features PASSED         [ 21%]
backend/tests/test_features.py::test_column_order_matches_feature_names PASSED [ 24%]
backend/tests/test_features.py::test_nonrefund_x_leadtime_active PASSED  [ 78%]
backend/tests/test_features.py::test_repeat_cancel_nodeposit_high_risk PASSED [ 83%]
backend/tests/test_pricing.py::test_recommended_price_maximises_expected_revenue PASSED [ 91%]
backend/tests/test_pricing.py::test_high_occupancy_never_discounts PASSED [ 94%]
======================== 37 passed in 2.52s ========================
```

---

## ⚠️ Honesty & Methodological Disclaimers

> [!IMPORTANT]
> **No Experimental Price Elasticity:** This dataset contains historical observational hotel booking records, not randomized A/B test price elasticity data. The "price-response curve" reflects correlational patterns learned by the XGBoost classifier across historical bookings, not true causal price elasticity. This is a form of **partial-dependence / what-if analysis** on a trained supervised model — a legitimate and practical industry technique whose limitations should be understood upfront.

---

## 📂 Complete Project Structure

```
hotel-pricing-engine/
├── training/                          # ML Training Subsystem
│   ├── data/                          # Raw CSV dataset cache (gitignored)
│   ├── artifacts/                     # Serialized model artifacts (.joblib, .json)
│   │   ├── model_v1.joblib            # Trained XGBoost Classifier
│   │   ├── encoders_v1.joblib         # Fitted Categorical LabelEncoders
│   │   ├── feature_metadata_v1.json   # Constants, Segment-Season lookup & Threshold
│   │   └── metrics_v1.json            # Model evaluation metrics & confusion matrix
│   ├── src/                           # Pipeline Source Modules
│   │   ├── data_loader.py             # Dataset downloader and cacher
│   │   ├── clean.py                   # Deduplication and data cleaning rules
│   │   ├── features.py                # 39-feature engineering specification
│   │   ├── evaluate.py                # Threshold-aware model evaluator
│   │   └── train_cancellation_model.py# Full training & Optuna pipeline
│   └── requirements.txt               # ML pipeline dependencies
├── backend/                           # FastAPI Application Subsystem
│   ├── app/                           # Application Source Code
│   │   ├── main.py                    # FastAPI application entry point & Lifespan hook
│   │   ├── config.py                  # Environment variable configuration
│   │   ├── db.py                      # SQLAlchemy engine & session setup
│   │   ├── models.py                  # SQLAlchemy ORM models (PricingRequest)
│   │   ├── schemas.py                 # Pydantic request/response schemas
│   │   ├── features.py                # Shared feature engineering copy
│   │   ├── inference.py               # Artifact loading & prediction module
│   │   ├── pricing.py                 # Price-response simulator & pacing optimizer
│   │   └── routers/                   # API Route Handlers
│   │       ├── predict.py             # /predict/cancellation-risk & recommend-price
│   │       └── history.py             # /history pagination endpoint
│   ├── tests/                         # Automated Pytest Suite
│   │   ├── test_api.py                # Integration tests for FastAPI endpoints
│   │   ├── test_features.py           # Unit tests for 39 features
│   │   └── test_pricing.py            # Unit tests for pricing optimization rules
│   ├── Dockerfile                     # Container definition for backend service
│   └── requirements.txt               # Backend dependencies
├── frontend/                          # React 19 Frontend Subsystem
│   ├── src/                           # Frontend Source Code
│   │   ├── api/                       # Axios API Client definition
│   │   ├── components/                # UI Components (BookingForm, PriceCurveChart, etc.)
│   │   ├── pages/                     # Application Pages (Recommender, History, About)
│   │   ├── App.tsx                    # React Router configuration & Layout
│   │   └── index.css                  # Tailwind CSS import
│   ├── package.json                   # Frontend dependencies & Vite scripts
│   └── vite.config.ts                 # Vite build configuration
├── .github/workflows/                 # CI/CD Workflows
│   └── backend-ci.yml                 # Automated testing workflow
├── docker-compose.yml                 # Orchestration for DB and Backend services
├── LICENSE                            # MIT License
└── README.md                          # Project Documentation
```

---


## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
