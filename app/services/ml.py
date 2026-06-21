from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression


@dataclass
class CostPrediction:
    predicted_daily_cost: float
    confidence: float
    details: str


def metrics_to_dataframe(metrics) -> pd.DataFrame:
    rows = [
        {
            "cpu": metric.cpu_percent,
            "memory": metric.memory_percent,
            "disk": metric.disk_percent,
            "network_in": metric.network_in_mb,
            "network_out": metric.network_out_mb,
            "response_time": metric.response_time_ms,
        }
        for metric in metrics
    ]
    return pd.DataFrame(rows)


def detect_anomalies(metrics) -> list[int]:
    df = metrics_to_dataframe(metrics)
    if len(df) < 8:
        return []

    model = IsolationForest(contamination=0.12, random_state=42)
    labels = model.fit_predict(df)
    return [index for index, label in enumerate(labels) if label == -1]


def predict_daily_cost(cost_records) -> CostPrediction:
    if len(cost_records) < 3:
        total = sum(record.estimated_cost for record in cost_records)
        return CostPrediction(round(total, 2), 0.2, "Not enough history for strong prediction.")

    y = np.array([record.estimated_cost for record in cost_records])
    x = np.arange(len(y)).reshape(-1, 1)
    model = LinearRegression()
    model.fit(x, y)

    future_x = np.arange(len(y), len(y) + 24).reshape(-1, 1)
    predicted = model.predict(future_x)
    daily_cost = max(float(predicted.sum()), 0.0)
    confidence = max(min(float(model.score(x, y)), 1.0), 0.0)

    return CostPrediction(
        predicted_daily_cost=round(daily_cost, 2),
        confidence=round(confidence, 2),
        details="Linear regression based on historical hourly cost records.",
    )

