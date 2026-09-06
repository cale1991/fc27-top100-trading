from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class StructuredMarketModel:
    """Small wrapper over XGBoost/LightGBM with chronological data supplied by the caller.

    Imports are intentionally lazy so the cloud API/collectors do not need ML dependencies.
    GPU configuration belongs to the RTX worker, not the 24/7 services.
    """

    backend: str = "xgboost"
    params: dict[str, Any] | None = None
    model: Any = None

    def fit(self, X, y, *, sample_weight=None):
        params = dict(self.params or {})
        if self.backend == "xgboost":
            from xgboost import XGBRegressor
            params.setdefault("n_estimators", 500)
            params.setdefault("max_depth", 7)
            params.setdefault("learning_rate", 0.04)
            params.setdefault("subsample", 0.85)
            params.setdefault("colsample_bytree", 0.85)
            self.model = XGBRegressor(**params)
        elif self.backend == "lightgbm":
            from lightgbm import LGBMRegressor
            params.setdefault("n_estimators", 500)
            params.setdefault("learning_rate", 0.04)
            self.model = LGBMRegressor(**params)
        else:
            raise ValueError("backend must be xgboost or lightgbm")
        self.model.fit(X, y, sample_weight=sample_weight)
        return self

    def predict(self, X):
        if self.model is None:
            raise RuntimeError("model is not fitted")
        return self.model.predict(X)
