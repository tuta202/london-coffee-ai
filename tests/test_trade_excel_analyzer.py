import pandas as pd
import pytest

from src.trade_excel_analyzer import (
    analyze_trade_excel,
    build_trade_ai_prompt,
    normalize_trade_data,
)


def sample_trade_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Date": 44928,
                "Source": "Indonesia",
                "Importer": "Buyer A",
                "Exporter": "Exporter A",
                "HS": 9011130,
                "Product Description": "ROBUSTA COFFEE BEANS",
                "Quantity": "19,200 KILOGRAM",
                "WEIGHT(kg)": "19,200 KG",
                "Price": 57600,
                "C/O": "Indonesia",
                "C/D": "Singapore",
                "P/O": "PANJANG",
                "P/D": "SINGAPORE",
            },
            {
                "Date": 45293,
                "Source": "Indonesia",
                "Importer": "Buyer B",
                "Exporter": "Exporter B",
                "HS": 9011130,
                "Product Description": "ROBUSTA COFFEE BEANS",
                "Quantity": "38,400 KILOGRAM",
                "WEIGHT(kg)": "38,400 KG",
                "Price": 153600,
                "C/O": "Indonesia",
                "C/D": "Italy",
                "P/O": "TANJUNG PRIOK",
                "P/D": "SALERNO",
            },
            {
                "Date": 45658,
                "Source": "Indonesia",
                "Importer": "Buyer C",
                "Exporter": "Exporter C",
                "HS": 9011120,
                "Product Description": "ARABICA GREEN COFFEE",
                "Quantity": "10 METRIC TON",
                "WEIGHT(kg)": "10,000 KG",
                "Price": 70000,
                "C/O": "Indonesia",
                "C/D": "France",
                "P/O": "BELAWAN",
                "P/D": "ANTWERP",
            },
        ]
    )


def test_normalize_trade_data_parses_excel_serial_and_numbers():
    df = normalize_trade_data(sample_trade_df())

    assert df.loc[0, "date"].year == 2023
    assert df.loc[0, "volume_ton"] == 19.2
    assert df.loc[1, "value"] == 153600
    assert df.loc[2, "unit_value_per_ton"] == 7000


def test_analyze_trade_excel_returns_growth_tables():
    analysis = analyze_trade_excel(sample_trade_df())

    assert not analysis.annual_raw.empty
    assert "volume_ton_growth_%" in analysis.annual_raw.columns
    assert analysis.hs_summary.iloc[0]["HS"] == 9011130


def test_build_trade_ai_prompt_uses_aggregate_payload_only():
    analysis = analyze_trade_excel(sample_trade_df())
    prompt = build_trade_ai_prompt(analysis)

    assert "Payload aggregate" in prompt
    assert "Chỉ sử dụng dữ liệu aggregate" in prompt
    assert "computed_key_metrics" in prompt
    assert "review_flag_sample" in prompt
    assert "top_origin_ports" not in prompt
    assert "Buyer A" in prompt
    assert "ROBUSTA COFFEE BEANS" not in prompt


def test_normalize_trade_data_rejects_missing_columns():
    bad_df = sample_trade_df().drop(columns=["Price"])

    with pytest.raises(ValueError, match="Thiếu các cột bắt buộc"):
        normalize_trade_data(bad_df)
