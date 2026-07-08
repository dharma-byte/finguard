# ml

Offline model training: feature engineering, Logistic Regression baseline,
XGBoost classifier, SHAP explainability. Produces the model file loaded by
the backend's scoring service.

## Setup

1. Download the [Kaggle Credit Card Fraud Detection dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)
   and place `creditcard.csv` in `../data/`.
2. `pip install -r requirements.txt`
3. `python train.py`

Outputs `models/fraud_model.joblib` and `models/metrics.json` (precision,
recall, F1, ROC-AUC for both the Logistic Regression baseline and XGBoost,
plus single-row inference latency for the XGBoost model -- mean/p95/max in
milliseconds, approximating per-transaction scoring latency in the
real-time consumer pipeline).
