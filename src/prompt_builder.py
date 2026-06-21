from __future__ import annotations

import json

import pandas as pd


def build_gemini_prompt(df: pd.DataFrame, analysis_metrics: dict) -> str:
    clean_df = df.copy()
    clean_df["scraped_at"] = clean_df["scraped_at"].astype(str)
    json_data = clean_df.to_dict(orient="records")

    return f"""
Bạn là chuyên gia phân tích giá hàng hóa, nhưng phải giải thích cho người không chuyên.

Dữ liệu dưới đây là giá cà phê Robusta London, đơn vị USD/tấn.
Hãy phân tích:
1. Tóm tắt thị trường hiện tại.
2. Kỳ hạn nào đáng chú ý nhất.
3. Giá đang tăng, giảm hay đi ngang.
4. Dự đoán ngắn hạn theo 3 kịch bản:
   - tích cực
   - trung tính
   - tiêu cực
5. Rủi ro và giới hạn của dự đoán.
6. Kết luận ngắn gọn cho người dùng phổ thông.

Không đưa lời khuyên đầu tư chắc chắn.
Không cam kết giá sẽ tăng hoặc giảm.
Luôn nói rõ đây chỉ là phân tích tham khảo.

Dữ liệu:
{json.dumps(json_data, ensure_ascii=False, indent=2)}

Chỉ số tính toán:
{json.dumps(analysis_metrics, ensure_ascii=False, indent=2)}
""".strip()
