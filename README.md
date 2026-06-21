## AI Phân tích giá cà phê Robusta London

MVP Streamlit để lấy bảng **Giá cà phê Robusta London (Luân Đôn)** từ Webgia, chuẩn hóa dữ liệu, tính các chỉ số định lượng cơ bản và gửi dữ liệu đã xử lý sang Gemini để tạo báo cáo tiếng Việt dễ hiểu.

### Tính năng

- Crawl dữ liệu từ `https://webgia.com/gia-hang-hoa/ca-phe-the-gioi/`
- Chỉ parse bảng Robusta London, bỏ qua Arabica New York và các bảng khác
- Chuẩn hóa số liệu: giá khớp, thay đổi, %, cao nhất, thấp nhất, khối lượng, mở cửa, hôm trước, HĐ mở
- Tính tín hiệu giá so với hôm trước, trong phiên, biên độ dao động, vị trí giá trong vùng cao-thấp, thanh khoản
- Tạo nhãn xu hướng định lượng trước khi gọi Gemini
- Hiển thị bảng, biểu đồ và cảnh báo rủi ro trong Streamlit

### Chạy local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

Thêm `GEMINI_API_KEY` trong `.env` nếu muốn Gemini tạo báo cáo AI. Nếu chưa có key, app vẫn chạy phần crawl, bảng, biểu đồ và phân tích định lượng.

### Deploy Streamlit

Có thể triển khai bằng Streamlit Community Cloud:

- Main file path: `app.py`
- Python dependencies: `requirements.txt`
- Secrets cần cấu hình nếu dùng Gemini:

```text
GEMINI_API_KEY=your_api_key_here
SOURCE_URL=https://webgia.com/gia-hang-hoa/ca-phe-the-gioi/
```

### Lưu ý

Phân tích chỉ mang tính tham khảo, không phải khuyến nghị đầu tư hoặc giao dịch. Dự đoán AI có sai số vì chỉ dựa trên bảng giá hiện tại, chưa bao gồm tin tức, thời tiết, tồn kho, tỷ giá, chính sách và dữ liệu lịch sử dài hạn.
