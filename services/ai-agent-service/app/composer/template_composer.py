from typing import Any


def _format_year_range(start_year: int | None, end_year: int | None) -> str:
    if start_year is not None and end_year is not None:
        if start_year == end_year:
            return f" năm {start_year}"
        return f" trong giai đoạn {start_year}-{end_year}"

    if start_year is not None:
        return f" từ năm {start_year}"

    if end_year is not None:
        return f" đến năm {end_year}"

    return ""


def compose_off_topic_answer() -> str:
    return (
        "Câu hỏi này nằm ngoài phạm vi dữ liệu government/economic/social indicators. "
        "Bạn có thể hỏi về GDP, nợ công, lạm phát, thất nghiệp, nghèo đói, khủng hoảng, "
        "dân số, đô thị hóa, đầu tư hoặc thương mại."
    )


def compose_need_clarification_answer(questions: list[str]) -> str:
    if not questions:
        return "Mình cần bạn làm rõ thêm câu hỏi."

    return "Mình cần bạn làm rõ thêm: " + " ".join(questions)


def compose_unsupported_answer(warnings: list[str] | None = None) -> str:
    if warnings:
        return "Loại câu hỏi này chưa được hỗ trợ ở phase hiện tại. " + " ".join(warnings)

    return "Loại câu hỏi này chưa được hỗ trợ ở phase hiện tại."


def compose_compare_answer(
    indicator_code: str | None,
    country_codes: list[str],
    start_year: int | None,
    end_year: int | None,
    rows: list[dict],
) -> str:
    year_text = _format_year_range(start_year, end_year)

    return (
        f"Đã so sánh dữ liệu thật cho chỉ số {indicator_code} "
        f"của {', '.join(country_codes)}{year_text}. "
        f"Tìm thấy {len(rows)} dòng dữ liệu."
    )


def compose_ranking_answer(
    indicator_code: str | None,
    year: int | None,
    rows: list[dict],
) -> str:
    if not rows:
        return f"Không tìm thấy dữ liệu ranking cho chỉ số {indicator_code} năm {year}."

    top = rows[0]
    country_name = top.get("country") or top.get("country_code")
    value = top.get("value")

    return (
        f"Đã xếp hạng top {len(rows)} quốc gia theo chỉ số {indicator_code} năm {year}. "
        f"Quốc gia đứng đầu là {country_name} với giá trị {value}."
    )


def compose_coverage_answer(
    indicator_code: str | None,
    rows: list[dict],
) -> str:
    if not rows:
        return f"Không tìm thấy coverage dữ liệu cho chỉ số {indicator_code}."

    if len(rows) == 1:
        row = rows[0]
        country = row.get("country") or row.get("country_code")
        return (
            f"Dữ liệu {indicator_code} của {country} có từ năm {row.get('min_year')} "
            f"đến năm {row.get('max_year')}, với {row.get('observations')} quan sát."
        )

    return f"Đã kiểm tra coverage dữ liệu cho chỉ số {indicator_code} trên {len(rows)} quốc gia."


def compose_trend_answer(
    indicator_code: str | None,
    country_codes: list[str],
    start_year: int | None,
    end_year: int | None,
    rows: list[dict],
    is_analytics_series: bool,
) -> str:
    year_text = _format_year_range(start_year, end_year)

    country_text = ""
    if country_codes:
        country_text = f" của {', '.join(country_codes)}"

    if is_analytics_series:
        return (
            f"Đã lấy chuỗi thời gian analytics cho chỉ số {indicator_code}"
            f"{country_text}{year_text}. "
            f"Tìm thấy {len(rows)} dòng gồm actual, trend, residual và anomaly_score."
        )

    return (
        f"Đã lấy chuỗi thời gian raw cho chỉ số {indicator_code}"
        f"{country_text}{year_text}. "
        f"Tìm thấy {len(rows)} dòng dữ liệu."
    )


def compose_anomaly_answer(
    indicator_code: str | None,
    country_codes: list[str],
    start_year: int | None,
    end_year: int | None,
    rows: list[dict],
    threshold: float = 0.75,
) -> str:
    year_text = _format_year_range(start_year, end_year)

    country_text = ""
    if country_codes:
        country_text = f" của {', '.join(country_codes)}"

    if not rows:
        return (
            f"Không tìm thấy điểm bất thường cho chỉ số {indicator_code}"
            f"{country_text}{year_text} với ngưỡng anomaly_score >= {threshold}."
        )

    top = rows[0]
    top_year = top.get("year")
    top_score = top.get("anomaly_score")
    top_actual = top.get("actual_value")

    return (
        f"Đã kiểm tra bất thường cho chỉ số {indicator_code}{country_text}{year_text}. "
        f"Tìm thấy {len(rows)} điểm bất thường với ngưỡng anomaly_score >= {threshold}. "
        f"Điểm đáng chú ý nhất là năm {top_year}, actual={top_actual}, anomaly_score={top_score}."
    )


def compose_fallback_answer(payload: dict[str, Any]) -> str:
    question_type = payload.get("question_type")
    tool_name = payload.get("tool_name")

    return (
        "Planner đã tạo plan nhưng agent chưa có composer phù hợp. "
        f"question_type={question_type}, tool={tool_name}."
    )