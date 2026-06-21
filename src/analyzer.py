from __future__ import annotations

import math

import pandas as pd


def safe_percent(numerator: float | None, denominator: float | None) -> float | None:
    if denominator in (None, 0) or numerator is None or pd.isna(denominator) or pd.isna(numerator):
        return None
    return numerator / denominator * 100


def round_or_none(value: float | None, digits: int = 2) -> float | None:
    if value is None or pd.isna(value) or not math.isfinite(value):
        return None
    return round(value, digits)


def trend_label(score: float) -> tuple[str, str]:
    if score >= 2:
        return "bullish", "Nghiêng tăng"
    if score <= -2:
        return "bearish", "Nghiêng giảm"
    return "neutral", "Đi ngang"


def analyze_market(df: pd.DataFrame) -> dict:
    if df.empty:
        raise ValueError("Không có dữ liệu để phân tích.")

    volume_average = df["volume"].mean()
    contracts = []

    for _, row in df.iterrows():
        daily_change = row["matched_price"] - row["previous_price"]
        intraday_change = row["matched_price"] - row["open_price"]
        range_value = row["high"] - row["low"]
        close_position = None
        if range_value:
            close_position = (row["matched_price"] - row["low"]) / range_value

        score = 0.0
        if row["change_percent"] > 0:
            score += 1
        elif row["change_percent"] < 0:
            score -= 1

        if row["matched_price"] > row["open_price"]:
            score += 1
        elif row["matched_price"] < row["open_price"]:
            score -= 1

        if close_position is not None:
            if close_position > 0.65:
                score += 1
            elif close_position < 0.35:
                score -= 1

        if row["volume"] > volume_average:
            score += 0.5

        label_en, label_vi = trend_label(score)
        contracts.append(
            {
                "contract_month": row["contract_month"],
                "daily_change": round_or_none(daily_change),
                "daily_change_percent": round_or_none(
                    safe_percent(daily_change, row["previous_price"])
                ),
                "intraday_change": round_or_none(intraday_change),
                "intraday_change_percent": round_or_none(
                    safe_percent(intraday_change, row["open_price"])
                ),
                "range_value": round_or_none(range_value),
                "range_percent": round_or_none(safe_percent(range_value, row["matched_price"])),
                "close_position": round_or_none(close_position),
                "trend_score": score,
                "trend_label": label_en,
                "trend_label_vi": label_vi,
                "volume": int(row["volume"]),
                "open_interest": int(row["open_interest"]),
            }
        )

    focus_contract = max(
        contracts,
        key=lambda item: (item["volume"], item["open_interest"]),
    )

    return {
        "summary": {
            "focus_contract": focus_contract["contract_month"],
            "trend_score": focus_contract["trend_score"],
            "trend_label": focus_contract["trend_label"],
            "trend_label_vi": focus_contract["trend_label_vi"],
            "confidence": "Thấp đến trung bình",
            "reason": "Phân tích dựa trên một lần crawl bảng giá hiện tại.",
        },
        "contracts": contracts,
    }
