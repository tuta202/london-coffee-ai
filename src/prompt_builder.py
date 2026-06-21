from __future__ import annotations

import json

import pandas as pd


def build_gemini_prompt(df: pd.DataFrame, analysis_metrics: dict) -> str:
    clean_df = df.copy()
    clean_df["scraped_at"] = clean_df["scraped_at"].astype(str)
    json_data = clean_df.to_dict(orient="records")

    return f"""
Bạn là chuyên gia phân tích thị trường hàng hóa, tập trung vào hợp đồng tương lai cà phê Robusta London.
Người đọc là người có chuyên môn trong ngành cà phê, xuất nhập khẩu, giao dịch hàng hóa hoặc quản trị rủi ro giá.

Yêu cầu quan trọng:
- Chỉ sử dụng dữ liệu trong phần "Dữ liệu chuẩn hóa" và "Chỉ số định lượng đã tính".
- Không tự bổ sung số liệu, tin tức, tồn kho, thời tiết, tỷ giá, vị thế quỹ hoặc dữ liệu thị trường bên ngoài.
- Không bịa nguyên nhân thị trường. Chỉ được nêu yếu tố bên ngoài như rủi ro cần theo dõi, không trình bày như sự thật đã xảy ra.
- Nếu một nhận định không thể suy ra trực tiếp từ dữ liệu đã cung cấp, ghi rõ "chưa đủ dữ liệu để kết luận".
- Không đưa khuyến nghị mua/bán chắc chắn. Không cam kết giá sẽ tăng hoặc giảm.

Dữ liệu là bảng giá Robusta London, đơn vị USD/tấn, tại một thời điểm crawl. Viết báo cáo tiếng Việt,
giọng chuyên nghiệp, súc tích, tối đa 900 từ. Không lặp lại toàn bộ dữ liệu thô.

Trả lời đúng cấu trúc sau:

## 1. Tóm tắt thị trường
- Nhận định xu hướng chung của các kỳ hạn.
- Nêu mức độ đồng thuận hoặc phân hóa giữa các kỳ hạn.

## 2. Kỳ hạn trọng tâm
- Chọn kỳ hạn đáng chú ý nhất dựa trên volume, open_interest và độ gần hạn.
- Phân tích giá khớp, thay đổi %, so với mở cửa, so với hôm trước và biên độ trong phiên.

## 3. Cấu trúc kỳ hạn
- So sánh giá giữa kỳ hạn gần và xa.
- Chỉ nêu backwardation/contango nếu suy ra được từ dữ liệu; nếu không, ghi rõ chưa đủ dữ liệu để kết luận chắc chắn.

## 4. Thanh khoản và độ tin cậy
- Đánh giá volume và open_interest.
- Chỉ ra kỳ hạn nào có tín hiệu đáng tin hơn do thanh khoản tốt hơn.

## 5. Kịch bản ngắn hạn
- Tích cực: điều kiện kích hoạt hoặc tín hiệu cần theo dõi.
- Trung tính: điều kiện kích hoạt hoặc tín hiệu cần theo dõi.
- Tiêu cực: điều kiện kích hoạt hoặc tín hiệu cần theo dõi.

## 6. Rủi ro và giới hạn
- Nêu giới hạn do chỉ có dữ liệu một thời điểm.
- Nêu các yếu tố bên ngoài cần theo dõi như rủi ro, không xem là nguyên nhân đã được xác nhận.

## 7. Điểm cần theo dõi tiếp
- Tóm tắt 3-5 ý chính cho người có chuyên môn.

Dữ liệu chuẩn hóa:
{json.dumps(json_data, ensure_ascii=False, indent=2)}

Chỉ số định lượng đã tính:
{json.dumps(analysis_metrics, ensure_ascii=False, indent=2)}
""".strip()
