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
from src.trade_excel_analyzer import REQUIRED_COLUMNS, analyze_trade_excel, build_trade_ai_prompt


load_dotenv()

DEFAULT_SOURCE_URL = "https://webgia.com/gia-hang-hoa/ca-phe-the-gioi/"
SOURCE_URL = os.getenv("SOURCE_URL", DEFAULT_SOURCE_URL)

st.set_page_config(
    page_title="AI Phân tích thị trường cà phê",
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


def format_numeric_table(df: pd.DataFrame) -> pd.DataFrame:
    display = df.copy()
    numeric_columns = display.select_dtypes(include="number").columns
    for column in numeric_columns:
        display[column] = display[column].round(2)
    return display


def render_trade_analysis_table(title: str, df: pd.DataFrame) -> None:
    st.subheader(title)
    st.dataframe(format_numeric_table(df), use_container_width=True, hide_index=True)


def render_trade_charts(annual_filtered: pd.DataFrame, monthly: pd.DataFrame) -> None:
    chart_cols = st.columns(2)
    chart_cols[0].plotly_chart(
        px.bar(
            annual_filtered,
            x="year",
            y="volume_ton",
            title="Volume theo năm sau lọc outlier",
            labels={"year": "Năm", "volume_ton": "Tấn"},
        ),
        use_container_width=True,
    )
    chart_cols[1].plotly_chart(
        px.line(
            monthly,
            x="month",
            y="volume_ton",
            title="Volume theo tháng gần nhất",
            markers=True,
            labels={"month": "Tháng", "volume_ton": "Tấn"},
        ),
        use_container_width=True,
    )


st.title("AI Phân tích thị trường cà phê")

market_tab, excel_tab = st.tabs(["Giá Robusta London", "Phân tích Excel"])

with market_tab:
    st.caption("Nguồn dữ liệu: Webgia.")

    analyze_button = st.empty()
    analyze_clicked = analyze_button.button("Phân tích ngay", type="primary", key="analyze_now")

    if analyze_clicked:
        try:
            analyze_button.button("Đang phân tích...", type="primary", disabled=True, key="analyzing")
            with st.status("Đang lấy dữ liệu từ Webgia...", expanded=True) as status:
                df, scraped_at = load_market_data(SOURCE_URL)
                status.write("Đang xử lý dữ liệu...")
                market_analysis = analyze_market(df)
                status.write("Đang gọi AI để phân tích...")
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
        finally:
            analyze_button.button("Phân tích ngay", type="primary", disabled=False, key="analyze_again")
    else:
        st.write("Bấm **Phân tích ngay** để lấy dữ liệu mới nhất và tạo báo cáo.")

with excel_tab:
    st.caption("Upload file Excel shipment")
    st.info("Mỗi lần chỉ upload 1 file. File chỉ được dùng trong phiên phân tích hiện tại và không được lưu vào hệ thống.")
    uploaded_file = st.file_uploader(
        "Chọn 1 file .xlsx",
        type=["xlsx"],
        accept_multiple_files=False,
        key="trade_excel_upload",
    )

    with st.expander("Cấu trúc file bắt buộc"):
        st.write(", ".join(REQUIRED_COLUMNS))

    if uploaded_file is not None:
        analyze_excel_button = st.empty()
        excel_clicked = analyze_excel_button.button(
            "Phân tích file Excel",
            type="primary",
            key="analyze_trade_excel",
        )

        if excel_clicked:
            try:
                analyze_excel_button.button(
                    "Đang phân tích file...",
                    type="primary",
                    disabled=True,
                    key="analyzing_trade_excel",
                )
                with st.status("Đang đọc và kiểm tra file Excel...", expanded=True) as status:
                    trade_df = pd.read_excel(uploaded_file)
                    status.write("Đang chuẩn hóa ngày, khối lượng và giá trị...")
                    analysis = analyze_trade_excel(trade_df)
                    status.write("Đang gọi AI để viết báo cáo phân tích...")
                    trade_ai_report = generate_report(build_trade_ai_prompt(analysis))
                    status.update(label="Hoàn tất phân tích file", state="complete")

                st.markdown(analysis.narrative)

                st.subheader("Báo cáo AI")
                st.markdown(trade_ai_report)

                for warning in analysis.warnings:
                    st.warning(warning)

                render_trade_charts(analysis.annual_filtered, analysis.monthly)
                render_trade_analysis_table("Tăng trưởng năm - dữ liệu raw", analysis.annual_raw)
                render_trade_analysis_table(
                    "Tăng trưởng năm - sau lọc outlier unit value",
                    analysis.annual_filtered,
                )
                render_trade_analysis_table("15 tháng gần nhất", analysis.monthly)
                render_trade_analysis_table("Theo HS code", analysis.hs_summary)
                render_trade_analysis_table("HS code theo năm", analysis.hs_year)

                top_cols = st.columns(2)
                with top_cols[0]:
                    render_trade_analysis_table("Top destination", analysis.top_destinations)
                    render_trade_analysis_table("Top exporter", analysis.top_exporters)
                    render_trade_analysis_table("Top cảng đi", analysis.top_origin_ports)
                with top_cols[1]:
                    render_trade_analysis_table("Top importer", analysis.top_importers)
                    render_trade_analysis_table("Top cảng đến", analysis.top_destination_ports)

                if not analysis.outliers.empty:
                    st.subheader("Outlier cần kiểm tra")
                    outlier_columns = [
                        "date",
                        "Importer",
                        "Exporter",
                        "HS",
                        "Product Description",
                        "volume_ton",
                        "value",
                        "unit_value_per_ton",
                        "C/D",
                        "P/O",
                        "P/D",
                    ]
                    st.dataframe(
                        format_numeric_table(analysis.outliers[outlier_columns]),
                        use_container_width=True,
                        hide_index=True,
                    )
            except Exception as exc:
                st.error(f"Không thể phân tích file Excel: {exc}")
            finally:
                analyze_excel_button.button(
                    "Phân tích file Excel",
                    type="primary",
                    disabled=False,
                    key="analyze_trade_excel_again",
                )
        else:
            st.write("Bấm **Phân tích file Excel** để bắt đầu.")
