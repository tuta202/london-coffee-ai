from __future__ import annotations

import re
from dataclasses import dataclass
import json

import pandas as pd


REQUIRED_COLUMNS = [
    "Date",
    "Source",
    "Importer",
    "Exporter",
    "HS",
    "Product Description",
    "Quantity",
    "WEIGHT(kg)",
    "Price",
    "C/O",
    "C/D",
    "P/O",
    "P/D",
]

UNIT_VALUE_MIN = 500
UNIT_VALUE_MAX = 30000


@dataclass
class TradeAnalysis:
    clean_data: pd.DataFrame
    annual_raw: pd.DataFrame
    annual_filtered: pd.DataFrame
    monthly: pd.DataFrame
    hs_year: pd.DataFrame
    hs_summary: pd.DataFrame
    top_destinations: pd.DataFrame
    top_importers: pd.DataFrame
    top_exporters: pd.DataFrame
    top_origin_ports: pd.DataFrame
    top_destination_ports: pd.DataFrame
    outliers: pd.DataFrame
    narrative: str
    warnings: list[str]


def parse_number(value: object) -> float | None:
    if pd.isna(value):
        return None
    matches = re.findall(r"-?\d[\d,.]*", str(value))
    if not matches:
        return None
    return float(matches[0].replace(",", ""))


def validate_trade_columns(df: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(
            "File Excel không đúng cấu trúc. Thiếu các cột bắt buộc: "
            + ", ".join(missing)
        )


def normalize_trade_data(df: pd.DataFrame) -> pd.DataFrame:
    validate_trade_columns(df)

    clean = df.copy()
    if pd.api.types.is_numeric_dtype(clean["Date"]):
        clean["date"] = pd.to_datetime(clean["Date"], unit="D", origin="1899-12-30")
    else:
        clean["date"] = pd.to_datetime(clean["Date"], errors="coerce")

    clean["weight_kg"] = clean["WEIGHT(kg)"].map(parse_number)
    clean["volume_ton"] = clean["weight_kg"] / 1000
    clean["value"] = clean["Price"].map(parse_number)
    clean["unit_value_per_ton"] = clean["value"] / clean["volume_ton"]
    clean["year"] = clean["date"].dt.year
    clean["month_num"] = clean["date"].dt.month
    clean["month"] = clean["date"].dt.to_period("M").astype(str)

    invalid_rows = clean[
        clean["date"].isna()
        | clean["volume_ton"].isna()
        | clean["value"].isna()
        | (clean["volume_ton"] <= 0)
    ]
    if len(invalid_rows) == len(clean):
        raise ValueError("Không đọc được Date, WEIGHT(kg) hoặc Price từ file Excel.")

    return clean.drop(index=invalid_rows.index).reset_index(drop=True)


def add_growth_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    result = df.copy()
    for column in columns:
        result[f"{column}_growth_%"] = result[column].pct_change() * 100
    return result


def aggregate_by_year(df: pd.DataFrame) -> pd.DataFrame:
    annual = (
        df.groupby("year")
        .agg(
            shipments=("Date", "size"),
            volume_ton=("volume_ton", "sum"),
            value=("value", "sum"),
        )
        .reset_index()
    )
    annual["unit_value_per_ton"] = annual["value"] / annual["volume_ton"]
    return add_growth_columns(annual, ["shipments", "volume_ton", "value", "unit_value_per_ton"])


def aggregate_by_month(df: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        df.groupby("month")
        .agg(
            shipments=("Date", "size"),
            volume_ton=("volume_ton", "sum"),
            value=("value", "sum"),
        )
        .reset_index()
    )
    monthly["unit_value_per_ton"] = monthly["value"] / monthly["volume_ton"]
    monthly["volume_mom_%"] = monthly["volume_ton"].pct_change() * 100
    monthly["value_mom_%"] = monthly["value"].pct_change() * 100
    monthly["volume_yoy_%"] = monthly["volume_ton"].pct_change(12) * 100
    monthly["value_yoy_%"] = monthly["value"].pct_change(12) * 100
    return monthly


def aggregate_by_hs(df: pd.DataFrame) -> pd.DataFrame:
    hs = (
        df.groupby("HS")
        .agg(
            shipments=("Date", "size"),
            volume_ton=("volume_ton", "sum"),
            value=("value", "sum"),
        )
        .reset_index()
    )
    hs["unit_value_per_ton"] = hs["value"] / hs["volume_ton"]
    hs["volume_share_%"] = hs["volume_ton"] / hs["volume_ton"].sum() * 100
    hs["value_share_%"] = hs["value"] / hs["value"].sum() * 100
    return hs.sort_values("volume_ton", ascending=False)


def aggregate_hs_year(df: pd.DataFrame) -> pd.DataFrame:
    hs_year = (
        df.groupby(["year", "HS"])
        .agg(
            shipments=("Date", "size"),
            volume_ton=("volume_ton", "sum"),
            value=("value", "sum"),
        )
        .reset_index()
    )
    hs_year["unit_value_per_ton"] = hs_year["value"] / hs_year["volume_ton"]
    return hs_year.sort_values(["year", "volume_ton"], ascending=[True, False])


def top_by(df: pd.DataFrame, column: str, limit: int = 10) -> pd.DataFrame:
    result = (
        df.groupby(column, dropna=False)
        .agg(
            shipments=("Date", "size"),
            volume_ton=("volume_ton", "sum"),
            value=("value", "sum"),
        )
        .reset_index()
    )
    result["unit_value_per_ton"] = result["value"] / result["volume_ton"]
    return result.sort_values("volume_ton", ascending=False).head(limit)


def comparable_period(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    years = sorted(df["year"].dropna().unique())
    if len(years) < 2:
        return df, "Dữ liệu chỉ có một năm, chưa đủ để tính tăng trưởng YoY."

    latest_year = int(max(years))
    latest_max_month = int(df.loc[df["year"] == latest_year, "month_num"].max())
    comparable = df[df["month_num"] <= latest_max_month]
    note = (
        f"So sánh theo cùng kỳ tháng 01-{latest_max_month:02d} "
        "để tránh lệch do năm mới nhất chưa đủ 12 tháng."
    )
    return comparable, note


def summarize_latest_growth(annual: pd.DataFrame) -> dict[str, float | int | None]:
    if len(annual) < 2:
        return {}
    latest = annual.iloc[-1]
    previous = annual.iloc[-2]
    return {
        "previous_year": int(previous["year"]),
        "latest_year": int(latest["year"]),
        "shipments_growth": latest["shipments_growth_%"],
        "volume_growth": latest["volume_ton_growth_%"],
        "value_growth": latest["value_growth_%"],
        "unit_growth": latest["unit_value_per_ton_growth_%"],
        "latest_volume": latest["volume_ton"],
        "latest_value": latest["value"],
    }


def first_record(df: pd.DataFrame) -> dict | None:
    if df.empty:
        return None
    return dataframe_records(df.head(1))[0]


def first_compact_record(df: pd.DataFrame, columns: list[str]) -> dict | None:
    records = compact_records(df, columns, limit=1)
    return records[0] if records else None


def build_key_metrics(analysis: TradeAnalysis) -> dict:
    raw_growth = summarize_latest_growth(analysis.annual_raw)
    filtered_growth = summarize_latest_growth(analysis.annual_filtered)
    top_columns = ["shipments", "volume_ton", "value", "unit_value_per_ton"]
    return {
        "valid_rows": len(analysis.clean_data),
        "date_min": str(analysis.clean_data["date"].min().date()),
        "date_max": str(analysis.clean_data["date"].max().date()),
        "raw_latest_vs_previous": raw_growth,
        "filtered_latest_vs_previous": filtered_growth,
        "top_hs_by_volume": first_compact_record(
            analysis.hs_summary,
            ["HS", "volume_ton", "value", "unit_value_per_ton", "volume_share_%"],
        ),
        "top_destination_by_volume": first_compact_record(
            analysis.top_destinations,
            ["C/D", *top_columns],
        ),
        "top_importer_by_volume": first_compact_record(
            analysis.top_importers,
            ["Importer", *top_columns],
        ),
        "top_exporter_by_volume": first_compact_record(
            analysis.top_exporters,
            ["Exporter", *top_columns],
        ),
        "outlier_count": int(
            (~analysis.clean_data["unit_value_per_ton"].between(UNIT_VALUE_MIN, UNIT_VALUE_MAX)).sum()
        ),
        "outlier_rule": f"unit_value_per_ton outside {UNIT_VALUE_MIN}-{UNIT_VALUE_MAX}",
    }


def format_hs_code(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return str(int(number)) if number.is_integer() else str(value)


def build_narrative(
    clean: pd.DataFrame,
    annual_raw: pd.DataFrame,
    annual_filtered: pd.DataFrame,
    hs_summary: pd.DataFrame,
    warnings: list[str],
) -> str:
    raw_growth = summarize_latest_growth(annual_raw)
    filtered_growth = summarize_latest_growth(annual_filtered)
    top_hs = hs_summary.iloc[0] if not hs_summary.empty else None

    lines = [
        "### Nhận định nhanh",
        f"- File có **{len(clean):,} dòng hợp lệ**, giai đoạn **{clean['date'].min().date()} đến {clean['date'].max().date()}**.",
    ]

    if raw_growth:
        lines.append(
            "- Theo dữ liệu raw cùng kỳ, volume tăng "
            f"**{raw_growth['volume_growth']:.1f}%**, value tăng **{raw_growth['value_growth']:.1f}%** "
            f"trong {raw_growth['latest_year']} so với {raw_growth['previous_year']}."
        )

    if filtered_growth:
        lines.append(
            "- Sau khi lọc outlier unit value ngoài khoảng "
            f"{UNIT_VALUE_MIN:,}-{UNIT_VALUE_MAX:,}/tấn, volume tăng **{filtered_growth['volume_growth']:.1f}%**, "
            f"value tăng **{filtered_growth['value_growth']:.1f}%**, unit value thay đổi **{filtered_growth['unit_growth']:.1f}%**."
        )

    if top_hs is not None:
        hs_code = format_hs_code(top_hs["HS"])
        lines.append(
            f"- HS **{hs_code}** là nhóm lớn nhất theo volume, chiếm "
            f"**{top_hs['volume_share_%']:.1f}%** volume sau lọc outlier."
        )

    if warnings:
        lines.append("- Cần chú ý: " + " ".join(warnings))

    lines.append(
        "- Kết luận: ưu tiên đọc tăng trưởng volume trước; tăng trưởng value cần kiểm tra outlier và đơn vị tiền tệ/giá trị."
    )
    return "\n".join(lines)


def dataframe_records(df: pd.DataFrame, limit: int | None = None) -> list[dict]:
    export_df = df.copy()
    if limit is not None:
        export_df = export_df.head(limit)
    for column in export_df.columns:
        if pd.api.types.is_datetime64_any_dtype(export_df[column]):
            export_df[column] = export_df[column].astype(str)
    return export_df.where(pd.notna(export_df), None).to_dict(orient="records")


def compact_records(
    df: pd.DataFrame,
    columns: list[str],
    limit: int | None = None,
    digits: int = 2,
) -> list[dict]:
    available = [column for column in columns if column in df.columns]
    export_df = df[available].copy()
    if limit is not None:
        export_df = export_df.head(limit)
    for column in export_df.columns:
        if pd.api.types.is_datetime64_any_dtype(export_df[column]):
            export_df[column] = export_df[column].astype(str)
        elif pd.api.types.is_numeric_dtype(export_df[column]):
            export_df[column] = export_df[column].round(digits)
    return export_df.where(pd.notna(export_df), None).to_dict(orient="records")


def build_trade_ai_prompt(analysis: TradeAnalysis) -> str:
    annual_columns = [
        "year",
        "shipments",
        "volume_ton",
        "value",
        "unit_value_per_ton",
        "volume_ton_growth_%",
        "value_growth_%",
        "unit_value_per_ton_growth_%",
    ]
    monthly_columns = [
        "month",
        "shipments",
        "volume_ton",
        "value",
        "unit_value_per_ton",
        "volume_yoy_%",
        "value_yoy_%",
    ]
    group_columns = [
        "shipments",
        "volume_ton",
        "value",
        "unit_value_per_ton",
        "volume_share_%",
        "value_share_%",
    ]
    top_columns = ["shipments", "volume_ton", "value", "unit_value_per_ton"]

    payload = {
        "metadata": {
            "valid_rows": len(analysis.clean_data),
            "date_min": str(analysis.clean_data["date"].min().date()),
            "date_max": str(analysis.clean_data["date"].max().date()),
            "warnings": analysis.warnings,
            "outlier_rule": f"unit_value_per_ton outside {UNIT_VALUE_MIN}-{UNIT_VALUE_MAX}",
        },
        "computed_key_metrics": build_key_metrics(analysis),
        "annual_raw": compact_records(analysis.annual_raw, annual_columns),
        "annual_filtered": compact_records(analysis.annual_filtered, annual_columns),
        "monthly_last_12": compact_records(analysis.monthly.tail(12), monthly_columns),
        "hs_summary_top_5": compact_records(analysis.hs_summary, ["HS", *group_columns], limit=5),
        "top_destinations": compact_records(analysis.top_destinations, ["C/D", *top_columns], limit=5),
        "top_importers": compact_records(analysis.top_importers, ["Importer", *top_columns], limit=5),
        "top_exporters": compact_records(analysis.top_exporters, ["Exporter", *top_columns], limit=5),
        "outlier_sample": dataframe_records(
            analysis.outliers[
                [
                    "date",
                    "Importer",
                    "Exporter",
                    "HS",
                    "volume_ton",
                    "value",
                    "unit_value_per_ton",
                    "C/D",
                ]
            ],
            limit=5,
        ),
    }

    return f"""
Bạn là chuyên gia phân tích dữ liệu thương mại cà phê. Người đọc là người có chuyên môn về xuất nhập khẩu,
chuỗi cung ứng, mua bán cà phê hoặc quản trị rủi ro.

Yêu cầu quan trọng:
- Chỉ sử dụng dữ liệu aggregate trong payload bên dưới. Không tự suy diễn từ dữ liệu ngoài.
- Ưu tiên dùng `computed_key_metrics` cho các con số chính; các bảng còn lại chỉ dùng để bổ trợ.
- Không bịa nguyên nhân thị trường. Nếu không thể suy ra từ số liệu, ghi rõ "chưa đủ dữ liệu để kết luận".
- Không lặp lại toàn bộ bảng. Tập trung vào insight từ volume, value, unit value, HS code, destination/importer/exporter và outlier.
- Phân biệt rõ dữ liệu raw và dữ liệu đã lọc outlier unit value.
- Không tự tính lại số nếu `computed_key_metrics` đã có sẵn.
- Báo cáo bằng tiếng Việt, súc tích, tối đa 700 từ.

Trả lời đúng cấu trúc:

## 1. Executive summary
- 3-5 ý chính quan trọng nhất.

## 2. Tăng trưởng volume và value
- So sánh năm mới nhất với năm trước theo cùng kỳ.
- Nêu khác biệt giữa raw và sau lọc outlier.

## 3. Cơ cấu sản phẩm / HS
- HS nào đóng góp chính vào volume/value.
- HS nào thay đổi đáng chú ý.

## 4. Thị trường và đối tác chính
- Destination, importer, exporter nổi bật.
- Chỉ nêu những gì payload chứng minh được.

## 5. Outlier và chất lượng dữ liệu
- Nhận xét outlier unit value.
- Nêu tác động của outlier đến phân tích value.

## 6. Kết luận cho người chuyên môn
- 3-5 điểm nên theo dõi tiếp.

Payload aggregate:
{json.dumps(payload, ensure_ascii=False, indent=2)}
""".strip()


def analyze_trade_excel(df: pd.DataFrame) -> TradeAnalysis:
    clean = normalize_trade_data(df)
    comparable, comparable_note = comparable_period(clean)
    annual_raw = aggregate_by_year(comparable)

    filtered = comparable[
        comparable["unit_value_per_ton"].between(UNIT_VALUE_MIN, UNIT_VALUE_MAX)
    ].copy()
    if filtered.empty:
        filtered = comparable.copy()

    annual_filtered = aggregate_by_year(filtered)
    monthly = aggregate_by_month(comparable).tail(15)
    hs_summary = aggregate_by_hs(filtered)
    hs_year = aggregate_hs_year(filtered)
    outliers = clean[
        ~clean["unit_value_per_ton"].between(UNIT_VALUE_MIN, UNIT_VALUE_MAX)
    ].sort_values("value", ascending=False)

    warnings = [comparable_note]
    if len(outliers) > 0:
        warnings.append(
            f"Phát hiện {len(outliers):,} dòng có unit value ngoài khoảng "
            f"{UNIT_VALUE_MIN:,}-{UNIT_VALUE_MAX:,}/tấn; nên xem như outlier để kiểm tra."
        )

    return TradeAnalysis(
        clean_data=clean,
        annual_raw=annual_raw,
        annual_filtered=annual_filtered,
        monthly=monthly,
        hs_year=hs_year,
        hs_summary=hs_summary,
        top_destinations=top_by(filtered, "C/D"),
        top_importers=top_by(filtered, "Importer"),
        top_exporters=top_by(filtered, "Exporter"),
        top_origin_ports=top_by(filtered, "P/O"),
        top_destination_ports=top_by(filtered, "P/D"),
        outliers=outliers.head(20),
        narrative=build_narrative(clean, annual_raw, annual_filtered, hs_summary, warnings),
        warnings=warnings,
    )
