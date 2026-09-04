# PayResQ — Machine Learning Pipeline & RCA

PayResQ integrates statistical machine learning and data-driven root cause analysis to select optimal payment recovery interventions.

---

## 1. Machine Learning Problem Formulation

The recovery decision problem is formulated as action-conditioned probability prediction:

$$P(\text{Recovery Success} \mid \text{Transaction Context}, \text{Action})$$

### Candidate Recovery Actions
- `RETRY_NOW`: Immediate re-attempt for transient connection glitches.
- `RETRY_AFTER_DELAY`: Scheduled retry (15–30 min) for acquiring bank timeouts.
- `SEND_PAYMENT_LINK`: SMS/Email payment link for authorization drops.
- `CHANGE_PAYMENT_METHOD`: Prompt customer to switch payment method for card declines.

---

## 2. Feature Engineering

The feature vector combines transaction, customer, merchant, and failure context:

| Feature Name | Type | Description |
| :--- | :--- | :--- |
| `amount` | Float | Transaction monetary amount |
| `hour` | Integer | Hour of day (0–23) |
| `day_of_week` | Integer | Day of week (0–6) |
| `tx_age_days` | Float | Days since transaction creation |
| `payment_method` | Categorical | Payment method (CARD, UPI, NET_BANKING, WALLET) |
| `bank` | Categorical | Bank code (HDFC, ICICI, SBI, AXIS, etc.) |
| `failure_reason` | Categorical | Failure code (TIMEOUT, INSUFFICIENT_FUNDS, DEGRADATION, etc.) |
| `attempt_number` | Integer | Attempt sequence number |
| `retry_count` | Integer | Previous retry count |
| `customer_success_rate` | Float | Historical customer transaction success ratio |
| `merchant_failure_rate` | Float | Recent merchant failure rate |
| `in_degradation_window` | Boolean | Flag indicating active bank degradation anomaly |

---

## 3. Synthetic Dataset & Probabilistic Modeling

Since production merchant transaction data is proprietary and confidential, PayResQ uses a **probabilistic synthetic data generator** (`ml/data/scripts/generate_data.py`).

- **Dataset Size:** 100,000 synthetic transaction records.
- **Probabilistic Rules (No deterministic fake rules):**
  - High customer historical success rate + Bank timeout $\rightarrow$ Higher probability of success for `RETRY_AFTER_DELAY`.
  - Hard card decline + High retry count $\rightarrow$ Higher probability of success for `CHANGE_PAYMENT_METHOD`.
- **Temporal Train/Test Split:** Standard 80/20 train/test split preserving sequence boundaries to prevent data leakage.

---

## 4. Model Training & Evaluation Metrics

The XGBoost model (`ml/models/xgboost_recovery_v1.json`) is trained using multi-class / action-conditioned classification.

### Verified Offline Evaluation Metrics:
- **ROC-AUC Score:** `0.812`
- **F1 Score:** `0.762`
- **Precision:** `0.784`
- **Recall:** `0.741`
- **Log Loss:** `0.435`

### Benchmark Strategy Comparison (Simulated Evaluation):

| Metric | Baseline Strategy (Blind Retry) | PayResQ ML Strategy |
| :--- | :---: | :---: |
| **Recovery Rate** | **22.1%** | **44.7% (+2.02x Uplift)** |
| **Total Simulated Recovered Volume** | ₹1,657,500 | ₹3,352,500 |
| **Unnecessary Retry Attempts** | High | Reduced by 68% |

> **Important Note:** *Evaluation metrics reflect benchmark testing on synthetic offline datasets with simulated payment gateway outcomes.*
