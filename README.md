# AI Phân tích thị trường cà phê

Ứng dụng Streamlit phân tích giá cà phê Robusta London và file Excel shipment cà phê.

Nguồn dữ liệu cố định:

```text
https://webgia.com/gia-hang-hoa/ca-phe-the-gioi/
```

## Tính năng

- Lấy dữ liệu Webgia và chỉ đọc bảng Robusta London.
- Chuẩn hóa dữ liệu giá, thay đổi %, khối lượng, mở cửa, hôm trước và HĐ mở.
- Tính các chỉ số định lượng cơ bản theo từng kỳ hạn.
- Hiển thị bảng dữ liệu, biểu đồ và báo cáo AI nếu có cấu hình `GEMINI_API_KEY`.
- Upload file `.xlsx` có cấu trúc shipment cố định để phân tích volume, value, unit value, HS code, destination, importer/exporter và outlier.

## Chạy local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

Nếu chưa có `GEMINI_API_KEY`, app vẫn hiển thị bảng, biểu đồ và chỉ số định lượng.

## Cấu hình

Tạo file `.env` từ `.env.example`:

```text
GEMINI_API_KEY=your_api_key_here
SOURCE_URL=https://webgia.com/gia-hang-hoa/ca-phe-the-gioi/
GEMINI_MODEL=gemini-3.1-flash-lite
```

## Deploy Streamlit

Trên Streamlit Community Cloud:

- Main file path: `app.py`
- Dependencies: `requirements.txt`
- Secrets: thêm `GEMINI_API_KEY` nếu muốn dùng báo cáo AI.

## Lưu ý

Phân tích chỉ mang tính tham khảo, không phải khuyến nghị đầu tư hoặc giao dịch.
