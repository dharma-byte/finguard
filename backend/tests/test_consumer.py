import numpy as np

from consumer import FEATURE_COLS, PCA_FEATURE_COLS, build_feature_vector, top_shap_features


def test_build_feature_vector_orders_features_correctly():
    features = {col: float(i) for i, col in enumerate(PCA_FEATURE_COLS)}
    message = {
        "features": features,
        "time_offset_seconds": 7200.0,  # hour 2
        "amount": np.expm1(3.0),  # amount_log ~= 3.0
    }

    vector = build_feature_vector(message)

    assert vector.shape == (1, len(PCA_FEATURE_COLS) + 2)
    np.testing.assert_allclose(vector[0, : len(PCA_FEATURE_COLS)], list(features.values()))
    assert vector[0, -2] == 2.0  # hour_of_day
    assert np.isclose(vector[0, -1], 3.0, atol=1e-6)  # amount_log


class _FakeExplainer:
    def __init__(self, values):
        self._values = values

    def shap_values(self, x):
        return [self._values]


def test_top_shap_features_returns_top_n_by_absolute_impact():
    values = [0.01] * len(FEATURE_COLS)
    values[5] = -0.9
    values[10] = 0.5
    values[2] = 0.3
    explainer = _FakeExplainer(values)

    top = top_shap_features(explainer, x=None, n=3)

    assert [f["feature"] for f in top] == [FEATURE_COLS[5], FEATURE_COLS[10], FEATURE_COLS[2]]
    assert top[0]["impact"] == -0.9
