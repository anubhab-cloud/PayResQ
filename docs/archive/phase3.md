# PayResQ — Phase 3: Intelligence

## Objective

Build the intelligence layer of PayResQ.

This phase must provide:

1. realistic ML training data,
2. feature engineering,
3. XGBoost recovery prediction,
4. root-cause analysis,
5. model evaluation,
6. baseline comparison,
7. prediction API.

Do NOT implement the LLM agent, policy engine, recovery executor, or frontend in this phase.

---

# 1. ML PROBLEM

The primary ML task is:

Given a failed payment and a candidate recovery action, estimate the probability that the action will successfully recover the payment.

Conceptually:

X = transaction context + customer history + merchant context + failure context + candidate action

Y = recovery success (0/1)

The model should output:

P(recovery_success | context, action)

Candidate actions:

- RETRY_NOW
- RETRY_AFTER_DELAY
- SEND_PAYMENT_LINK
- CHANGE_PAYMENT_METHOD

The system should evaluate each candidate action for a failed transaction.

Example:

RETRY_NOW = 0.24
RETRY_AFTER_DELAY = 0.71
SEND_PAYMENT_LINK = 0.39
CHANGE_PAYMENT_METHOD = 0.55

The highest predicted probability may be used as the recommended action for the ML layer, but final autonomous action selection belongs to the Phase 4 agent/policy layer.

---

# 2. DATASET SIZE

The current development dataset is small.

Scale synthetic data for ML training to approximately:

50,000–100,000 transactions.

The generator must remain configurable.

Do not hardcode a specific dataset size.

Example:

python -m ml.data.scripts.generate_data --transactions 100000 --seed 42

The ML pipeline should be able to train on the generated dataset.

---

# 3. TRAINING DATA

Construct an ML dataset from historical payment/recovery information.

Features should include useful information such as:

## Transaction

- amount
- currency
- payment method
- transaction hour
- transaction day
- transaction age

## Customer

- historical transaction count
- historical successful transaction count
- historical success rate
- average transaction amount
- previous failed attempts
- customer age/history length

## Merchant

- merchant transaction volume
- merchant historical failure rate
- merchant historical recovery rate

## Payment / Failure

- bank
- failure type
- failure code
- attempt number
- retry count
- time since previous attempt
- recent bank failure rate
- recent merchant failure rate

## Candidate Action

- action type
- delay minutes where applicable

The exact feature set may be adjusted based on the actual data.

Do not create meaningless features just to increase feature count.

---

# 4. DATA LEAKAGE

This is critical.

Do NOT allow information that would only become known after the recovery action into the input features.

For example, the model must NOT use:

- future recovery outcome
- future payment attempt status
- future recovery success
- future events

to predict the recovery outcome.

Historical features must be computed using information available before the candidate recovery action.

Document how leakage is avoided.

---

# 5. TRAIN/TEST SPLIT

Prefer a time-aware split for this problem because this represents a temporal payment system.

Earlier transactions should generally be used for training and later transactions for validation/test.

Avoid randomly mixing future information into training when that would create unrealistic evaluation.

Document:

- training period
- validation period if used
- test period

Do not use test data for training or hyperparameter tuning.

---

# 6. MODEL

Use XGBoost for the recovery prediction model.

Start with a classification model appropriate for binary recovery success.

The model should estimate probability rather than only output a hard class.

Use reasonable baseline hyperparameters first.

Do not spend excessive time on hyperparameter optimization.

We have a strict hackathon deadline.

---

# 7. CATEGORICAL FEATURES

Handle categorical variables correctly.

Possible categorical features:

- bank
- payment_method
- failure_reason
- candidate_action

Use an approach that is compatible with XGBoost and reproducible.

Avoid fragile manual mappings.

Document the chosen approach.

---

# 8. FEATURE PIPELINE

The transformation from database data to ML features must be reproducible.

Create a clear pipeline:

Database / historical data
        ↓
Feature extraction
        ↓
Feature transformation
        ↓
XGBoost

The same feature transformation must be usable during inference.

Avoid training-time-only transformations that cannot be reproduced when predicting a live transaction.

---

# 9. MODEL ARTIFACT

Save the trained model as a versioned artifact.

For example:

ml/models/recovery_model.json

Also save enough metadata to reproduce/use the model safely, such as:

- feature names
- model version
- training timestamp
- training dataset information
- evaluation metrics
- preprocessing configuration

Do not commit huge generated datasets or unnecessary binary artifacts to Git.

---

# 10. ROOT CAUSE ANALYSIS

Build a deterministic/data-driven root-cause analysis component.

The system should identify abnormal failure patterns.

Analyze dimensions such as:

- bank
- payment method
- merchant
- time window
- failure type

Example:

Normal ICICI card timeout rate:
4%

Recent timeout rate:
16%

Possible output:

root_cause = temporary_bank_degradation

confidence = appropriate statistical confidence

evidence:
- recent timeout rate significantly above baseline
- affected bank
- affected payment method
- affected time window

Do NOT allow an LLM to invent root causes.

The LLM will be introduced later.

---

# 11. ROOT CAUSE OUTPUT

Create a structured result similar to:

{
  "root_cause": "TEMPORARY_BANK_DEGRADATION",
  "confidence": 0.89,
  "affected_bank": "ICICI",
  "affected_method": "CARD",
  "evidence": [
    "Recent timeout rate is significantly above baseline",
    "Increase is concentrated in the affected bank and method"
  ]
}

The exact implementation can differ.

Do not claim causal certainty from simple correlations.

Use language such as:

"likely root cause" or "strong contributing factor" where appropriate.

---

# 12. RECOVERY PREDICTION SERVICE

Create a reusable service that accepts a transaction ID and produces predictions for candidate actions.

Conceptually:

get_recovery_predictions(transaction_id)

returns:

{
  "transaction_id": "...",
  "predictions": {
    "RETRY_NOW": 0.24,
    "RETRY_AFTER_DELAY": 0.71,
    "SEND_PAYMENT_LINK": 0.39,
    "CHANGE_PAYMENT_METHOD": 0.55
  }
}

Also return:

- model version
- feature version if appropriate
- timestamp

Do not execute recovery actions.

This service only predicts.

---

# 13. API

Add an API endpoint such as:

POST /api/v1/intelligence/recovery-predict

Input:

{
  "transaction_id": 123
}

Output should contain:

- transaction ID
- candidate action probabilities
- model version
- recommended ML action
- timestamp

Add an endpoint for root-cause analysis if appropriate:

GET /api/v1/intelligence/root-cause/{transaction_id}

Keep route handlers thin.

Business logic belongs in services.

---

# 14. BASELINE

Implement a simple baseline strategy.

Example:

Always choose RETRY_NOW.

Compare the baseline against the ML strategy on the held-out test set.

Measure:

- recovery rate
- recovered revenue
- number of successful recoveries
- unsuccessful interventions

The ML model should be evaluated against the same test period as the baseline.

Do not fabricate improvement.

If the ML model does not outperform the baseline, report that honestly and investigate the reason.

---

# 15. MODEL EVALUATION

Report appropriate metrics:

- ROC-AUC
- Precision
- Recall
- F1
- Log Loss

Also evaluate probability quality where practical.

Because the output is used as a probability estimate, calibration is important.

Include a confusion matrix if useful.

Save evaluation results in a machine-readable format.

Example:

ml/models/evaluation.json

---

# 16. BUSINESS METRICS

In addition to ML metrics, calculate:

- total failed payments
- recovery attempts
- successful recoveries
- recovery rate
- revenue at risk
- recovered revenue

These metrics will eventually be displayed in the frontend.

Clearly label synthetic-data results as simulated/experimental.

Do not present them as real-world Razorpay performance.

---

# 17. TESTING

Add tests for:

### Feature engineering

- expected feature columns exist
- no future/outcome leakage
- transformations are reproducible

### Model

- model trains successfully
- prediction probabilities are between 0 and 1
- all candidate actions produce predictions

### Root cause

- elevated failure pattern is detected
- normal pattern does not incorrectly trigger an incident
- root-cause evidence is returned

### API

- prediction endpoint works
- invalid transaction IDs handled correctly
- root-cause endpoint works

Tests must use small datasets and must not retrain a huge model unnecessarily.

---

# 18. PERFORMANCE

Do not train 100k rows through an API request.

Training is an offline process.

Use:

training script
    ↓
model artifact

Inference:

API
    ↓
feature extraction
    ↓
loaded model
    ↓
prediction

Load the model once where practical instead of retraining/loading it for every request.

---

# 19. REPRODUCIBILITY

Use deterministic seeds where appropriate.

The same dataset seed + training configuration should produce reproducible results within reasonable expectations.

Record:

- random seed
- model version
- feature version
- training dataset size
- training timestamp

---

# 20. DO NOT IMPLEMENT

Do NOT implement:

- LLM
- AI agent
- tool calling
- policy engine
- autonomous recovery execution
- Redis recovery queues
- frontend
- authentication
- Kafka
- Kubernetes
- microservices
- GraphQL
- vector database
- CQRS
- event sourcing

Those belong to later phases.

---

# 21. DEFINITION OF DONE

Phase 3 is complete only when:

1. ML dataset can be generated.
2. Feature engineering works.
3. XGBoost trains successfully.
4. Model artifact is saved.
5. Evaluation metrics are produced.
6. Baseline comparison is available.
7. Root-cause analysis works.
8. Recovery prediction service works.
9. Prediction API works.
10. Tests pass.
11. No obvious data leakage exists.
12. Results are clearly documented.
13. Synthetic results are clearly labeled as experimental.

---

# 22. STOP CONDITION

This is Phase 3 only.

After completing and testing Phase 3:

STOP.

Do not start Phase 4.

Report:

- dataset size
- feature count
- feature list
- model configuration
- training/test split
- evaluation metrics
- baseline metrics
- root-cause examples
- prediction examples
- API endpoints
- model artifact location
- tests passed
- performance observations
- limitations and assumptions