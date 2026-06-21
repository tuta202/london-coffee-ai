from __future__ import annotations

import os


def generate_report(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return (
            "Chưa cấu hình `GEMINI_API_KEY`, nên ứng dụng chỉ hiển thị phần phân tích định lượng. "
            "Khi deploy Streamlit, thêm secret này để Gemini tạo báo cáo tiếng Việt đầy đủ."
        )

    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise RuntimeError("Thiếu thư viện google-generativeai. Hãy cài requirements.txt.") from exc

    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(model_name)
    try:
        response = model.generate_content(prompt)
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini không trả về nội dung báo cáo.")
        return text
    except Exception as exc:
        return (
            "Không thể gọi Gemini ở thời điểm này, nên ứng dụng chỉ hiển thị phần phân tích "
            f"định lượng. Chi tiết lỗi: `{exc}`\n\n"
            "Bạn có thể kiểm tra lại `GEMINI_API_KEY`, quyền truy cập API của Google Cloud project, "
            "billing, khu vực/model được phép dùng, hoặc đổi `GEMINI_MODEL` trong `.env`."
        )
