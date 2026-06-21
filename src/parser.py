from __future__ import annotations

import re
import unicodedata
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup, Tag


TARGET_TITLE = "Giá cà phê Robusta London (Luân Đôn)"
EXPECTED_COLUMNS = [
    "contract_month",
    "matched_price",
    "change_value",
    "change_percent",
    "high",
    "low",
    "volume",
    "open_price",
    "previous_price",
    "open_interest",
    "scraped_at",
]


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFC", value or "")
    return re.sub(r"\s+", " ", text).strip()


def normalize_for_match(value: str) -> str:
    text = normalize_text(value).lower()
    text = "".join(
        char for char in unicodedata.normalize("NFD", text) if unicodedata.category(char) != "Mn"
    )
    return text.replace("đ", "d")


def parse_number(value: str) -> float | None:
    text = normalize_text(value)
    if not text or text in {"-", "—", "N/A"}:
        return None
    match = re.search(r"[-+]?\d[\d,.]*", text)
    if not match:
        return None
    return float(match.group(0).replace(",", ""))


def parse_change(value: str) -> tuple[float | None, float | None]:
    text = normalize_text(value)
    numbers = re.findall(r"[-+]?\d[\d,.]*", text)
    if not numbers:
        return None, None
    change_value = float(numbers[0].replace(",", ""))
    change_percent = None
    if len(numbers) > 1:
        change_percent = float(numbers[1].replace(",", ""))
    return change_value, change_percent


def decode_webgia_nb(value: str | None) -> str | None:
    if not value:
        return None

    hex_text = re.sub(r"[A-Z]", "", value)
    if len(hex_text) < 2:
        return None

    chars = []
    for index in range(0, len(hex_text) - 1, 2):
        pair = hex_text[index : index + 2]
        try:
            chars.append(chr(int(pair, 16)))
        except ValueError:
            return None
    return "".join(chars)


def find_target_table(soup: BeautifulSoup) -> Tag:
    target_key = normalize_for_match(TARGET_TITLE)
    for heading in soup.find_all(string=lambda text: text and target_key in normalize_for_match(text)):
        parent = heading.parent
        table = None
        cursor = parent
        for _ in range(6):
            if cursor is None:
                break
            table = cursor.find_next("table")
            if table:
                return table
            cursor = cursor.parent

    for table in soup.find_all("table"):
        context = normalize_for_match(table.get_text(" ", strip=True))
        if "robusta london" in context or "luan don" in context:
            return table

    raise ValueError(f"Không tìm thấy bảng '{TARGET_TITLE}'.")


def row_cells(row: Tag) -> list[str]:
    cells = []
    for cell in row.find_all(["td", "th"]):
        decoded = decode_webgia_nb(cell.get("nb"))
        cells.append(normalize_text(decoded or cell.get_text(" ", strip=True)))
    return cells


def parse_robusta_london_table(html: str, scraped_at: datetime) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")
    table = find_target_table(soup)
    rows = [row_cells(row) for row in table.find_all("tr")]
    data_rows = [cells for cells in rows if len(cells) >= 9 and parse_number(cells[1]) is not None]

    records = []
    for cells in data_rows:
        change_value, change_percent = parse_change(cells[2])
        records.append(
            {
                "contract_month": cells[0],
                "matched_price": parse_number(cells[1]),
                "change_value": change_value,
                "change_percent": change_percent,
                "high": parse_number(cells[3]),
                "low": parse_number(cells[4]),
                "volume": parse_number(cells[5]),
                "open_price": parse_number(cells[6]),
                "previous_price": parse_number(cells[7]),
                "open_interest": parse_number(cells[8]),
                "scraped_at": scraped_at,
            }
        )

    if not records:
        raise ValueError("Bảng Robusta London không có dòng dữ liệu hợp lệ.")

    df = pd.DataFrame(records, columns=EXPECTED_COLUMNS)
    int_columns = ["volume", "open_interest"]
    for column in int_columns:
        df[column] = df[column].fillna(0).astype(int)
    return df
