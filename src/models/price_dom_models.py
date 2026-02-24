from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Optional, Sequence

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import ElasticNet
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


TARGET_PRICE_PSQFT = "price_per_sqft"
TARGET_DOM = "days_on_market"


def _build_preprocessor(
    numeric_features: Sequence[str],
    categorical_features: Sequence[str],
) -> ColumnTransformer:
    numeric_transformer = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
        ]
    )
    categorical_transformer = Pipeline(
        steps=[
            ("oh", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, list(numeric_features)),
            ("cat", categorical_transformer, list(categorical_features)),
        ]
    )


@dataclass
class BaselineMarketModels:
    """
    Baseline models for:
    - price per square foot
    - days on market

    These provide:
    - A quantitative view of how design and location features map to outcomes.
    - Inputs to optimization routines (e.g., revenue expectations).
    """

    numeric_features: Sequence[str]
    categorical_features: Sequence[str]
    price_model: Optional[Pipeline] = None
    dom_model: Optional[Pipeline] = None

    def fit(self, df: pd.DataFrame) -> "BaselineMarketModels":
        X = df[self.numeric_features + self.categorical_features]

        price_y = df[TARGET_PRICE_PSQFT].astype(float)
        dom_y = df[TARGET_DOM].astype(float)

        preprocessor = _build_preprocessor(
            numeric_features=self.numeric_features,
            categorical_features=self.categorical_features,
        )

        price_pipe = Pipeline(
            steps=[
                ("pre", preprocessor),
                ("model", ElasticNet(alpha=0.1, l1_ratio=0.5)),
            ]
        )

        dom_pipe = Pipeline(
            steps=[
                ("pre", preprocessor),
                ("model", ElasticNet(alpha=0.1, l1_ratio=0.5)),
            ]
        )

        self.price_model = price_pipe.fit(X, price_y)
        self.dom_model = dom_pipe.fit(X, dom_y)
        return self

    def predict(
        self,
        df: pd.DataFrame,
    ) -> Tuple[np.ndarray, np.ndarray]:
        if self.price_model is None or self.dom_model is None:
            raise RuntimeError("Models not fitted. Call `fit` first.")

        X = df[self.numeric_features + self.categorical_features]
        price_pred = self.price_model.predict(X)
        dom_pred = self.dom_model.predict(X)
        return price_pred, dom_pred

