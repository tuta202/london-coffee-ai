from datetime import datetime, timezone

from src.analyzer import analyze_market
from src.parser import decode_webgia_nb, parse_robusta_london_table


def test_decode_webgia_nb_attribute():
    assert decode_webgia_nb("YZD33L2RcD363KD43R0H") == "3,640"


def test_parse_and_analyze_sample_robusta_london_table():
    html = """
    <html>
      <body>
        <h2>Giá cà phê Robusta London (Luân Đôn)</h2>
        <table>
          <tr>
            <th>Kỳ hạn</th><th>Giá khớp</th><th>Thay đổi</th><th>Cao nhất</th>
            <th>Thấp nhất</th><th>Khối lượng</th><th>Mở cửa</th>
            <th>Hôm trước</th><th>HĐ mở</th>
          </tr>
          <tr>
            <td>09/2026</td><td>3,640</td><td>-45 -1.22%</td><td>3,720</td>
            <td>3,600</td><td>10,157</td><td>3,690</td><td>3,685</td><td>23,400</td>
          </tr>
          <tr>
            <td>11/2026</td><td>3,710</td><td>20 0.54%</td><td>3,730</td>
            <td>3,650</td><td>8,500</td><td>3,680</td><td>3,690</td><td>21,100</td>
          </tr>
        </table>
      </body>
    </html>
    """

    scraped_at = datetime(2026, 6, 21, tzinfo=timezone.utc)
    df = parse_robusta_london_table(html, scraped_at)
    analysis = analyze_market(df)

    assert list(df["contract_month"]) == ["09/2026", "11/2026"]
    assert df.loc[0, "matched_price"] == 3640
    assert df.loc[0, "change_value"] == -45
    assert df.loc[0, "change_percent"] == -1.22
    assert df.loc[0, "volume"] == 10157
    assert analysis["summary"]["focus_contract"] == "09/2026"
    assert analysis["contracts"][0]["daily_change"] == -45


def test_parse_webgia_encoded_cells():
    html = """
    <html>
      <body>
        <h2>Giá cà phê Robusta London (Luân Đôn)</h2>
        <table>
          <tr>
            <th>Kỳ hạn</th><th>Giá khớp</th><th>Thay đổi</th><th>Cao nhất</th>
            <th>Thấp nhất</th><th>Khối lượng</th><th>Mở cửa</th>
            <th>Hôm trước</th><th>HĐ mở</th>
          </tr>
          <tr>
            <td>07/2026</td>
            <td nb="YZD33L2RcD363KD43R0H"><small>webgiá.com</small></td>
            <td><strong>-45</strong><small>-1.22%</small></td>
            <td>3,699<small>+14</small></td>
            <td>3,634<small>-51</small></td>
            <td nb="KDXVEX32Z2cG3031Q3Q3"><small>webgia.com</small></td>
            <td nb="S33T2c3S6X3NWM6UE3X4"><small>webgia.com</small></td>
            <td nb="3L3U2c36383TH5EL"><small>webgia.com</small></td>
            <td nb="38UQ2c3434TR3V4"><small>webgia.com</small></td>
          </tr>
        </table>
      </body>
    </html>
    """

    scraped_at = datetime(2026, 6, 21, tzinfo=timezone.utc)
    df = parse_robusta_london_table(html, scraped_at)

    assert df.loc[0, "matched_price"] == 3640
    assert df.loc[0, "volume"] == 2013
    assert df.loc[0, "open_price"] == 3664
    assert df.loc[0, "previous_price"] == 3685
    assert df.loc[0, "open_interest"] == 8444
