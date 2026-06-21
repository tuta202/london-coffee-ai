import os

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from src.analyzer import analyze_market
from src.gemini_client import generate_report
from src.parser import parse_robusta_london_table
from src.prompt_builder import build_gemini_prompt
from src.scraper import fetch_html


load_dotenv()

DEFAULT_SOURCE_URL = "https://webgia.com/gia-hang-hoa/ca-phe-the-gioi/"
SOURCE_URL = os.getenv("SOURCE_URL", DEFAULT_SOURCE_URL)

st.set_page_config(
    page_title="AI Phân tích giá cà phê Robusta London",
    page_icon="☕",
    layout="wide",
)


@st.cache_data(ttl=60, show_spinner=False)
def load_market_data(url: str):
    html, scraped_at = fetch_html(url)
    return parse_robusta_london_table(html, scraped_at), scraped_at


def render_charts(df: pd.DataFrame) -> None:
    chart_cols = st.columns(3)
    chart_cols[0].plotly_chart(
        px.bar(
            df,
            x="contract_month",
            y="matched_price",
            title="Giá khớp theo kỳ hạn",
            labels={"contract_month": "Kỳ hạn", "matched_price": "USD/tấn"},
        ),
        use_container_width=True,
    )
    chart_cols[1].plotly_chart(
        px.bar(
            df,
            x="contract_month",
            y="change_percent",
            title="Thay đổi % theo kỳ hạn",
            labels={"contract_month": "Kỳ hạn", "change_percent": "%"},
            color="change_percent",
            color_continuous_scale="RdYlGn",
        ),
        use_container_width=True,
    )
    chart_cols[2].plotly_chart(
        px.bar(
            df,
            x="contract_month",
            y="volume",
            title="Khối lượng theo kỳ hạn",
            labels={"contract_month": "Kỳ hạn", "volume": "Hợp đồng"},
        ),
        use_container_width=True,
    )


st.title("AI Phân tích giá cà phê Robusta London")
st.caption("Nguồn dữ liệu: Webgia.")

if st.button("Phân tích ngay", type="primary"):
    try:
        with st.status("Đang lấy dữ liệu từ Webgia...", expanded=True) as status:
            df, scraped_at = load_market_data(SOURCE_URL)
            status.write("Đang xử lý dữ liệu...")
            market_analysis = analyze_market(df)
            status.write("Đang gọi Gemini để phân tích...")
            prompt = build_gemini_prompt(df, market_analysis)
            ai_report = generate_report(prompt)
            status.update(label="Hoàn tất phân tích", state="complete")

        st.subheader("Kết quả")
        st.write(f"Cập nhật lúc: **{scraped_at.strftime('%Y-%m-%d %H:%M:%S %Z')}**")
        st.write(f"Nguồn: [{SOURCE_URL}]({SOURCE_URL})")

        st.subheader("Bảng dữ liệu chuẩn hóa")
        display_df = df.copy()
        display_df["scraped_at"] = display_df["scraped_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.subheader("Biểu đồ")
        render_charts(df)

        st.subheader("Chỉ số phân tích")
        metrics_df = pd.DataFrame(market_analysis["contracts"])
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)

        st.subheader("Báo cáo AI")
        st.markdown(ai_report)

        st.warning(
            "Phân tích này chỉ mang tính tham khảo, không phải khuyến nghị đầu tư/giao dịch. "
            "Dữ liệu công khai có thể bị trễ hoặc thay đổi. Dự đoán AI có sai số vì chưa bao gồm "
            "tin tức, thời tiết, tồn kho, tỷ giá, chính sách và dữ liệu lịch sử dài hạn."
        )
    except Exception as exc:
        st.error(f"Không thể phân tích dữ liệu: {exc}")
else:
    st.write("Bấm **Phân tích ngay** để lấy dữ liệu mới nhất và tạo báo cáo.")
