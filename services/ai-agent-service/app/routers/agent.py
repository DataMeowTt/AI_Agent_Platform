from fastapi import APIRouter, Depends

from app.core.security import verify_internal_api_key
from app.resolver.slot_resolver import resolve_slots, resolved_slots_to_metadata
from app.schemas.chat import (
    AiAgentChartConfig,
    AiAgentMetadata,
    AiChatRequest,
    AiChatResponse,
)
from app.tools.compare_tool import compare_countries
from app.tools.common import ToolError


router = APIRouter(
    prefix="/agent",
    tags=["agent"],
    dependencies=[Depends(verify_internal_api_key)],
)


def build_compare_line_chart_data(rows: list[dict]) -> list[dict]:
    """
    Convert long format:
      country_code, year, value

    Thành chart format:
      year, VNM, THA
    """
    by_year: dict[int, dict] = {}

    for row in rows:
        year = row.get("year")
        country_code = row.get("country_code")
        value = row.get("value")

        if year is None or country_code is None:
            continue

        if year not in by_year:
            by_year[year] = {"year": year}

        by_year[year][country_code] = value

    return [by_year[year] for year in sorted(by_year.keys())]


@router.post("/chat", response_model=AiChatResponse)
def chat(payload: AiChatRequest) -> AiChatResponse:
    normalized_message = payload.message.strip()

    slots = resolve_slots(normalized_message)
    metadata = resolved_slots_to_metadata(slots)

    if slots.needs_clarification:
        return AiChatResponse(
            answer="Mình cần bạn làm rõ thêm: "
            + " ".join(slots.clarification_questions),
            questionType="NEED_CLARIFICATION",
            data=[
                {
                    "message": normalized_message,
                    "conversationId": payload.conversationId,
                    "context": payload.context,
                    "resolved": metadata["resolved"],
                }
            ],
            chart=AiAgentChartConfig(type="none"),
            warnings=[],
            metadata=AiAgentMetadata(
                source="template",
                toolsUsed=[
                    "indicator_resolver",
                    "country_resolver",
                    "year_resolver",
                ],
                indicators=metadata["indicators"],
                analytics_indicators=metadata["analytics_indicators"],
                raw_only_indicators=metadata["raw_only_indicators"],
                countries=metadata["countries"],
                years=metadata["years"],
                resolved=metadata["resolved"],
            ),
        )

    indicator_codes = metadata["indicators"]
    country_codes = metadata["countries"]
    years = metadata["years"]

    if not indicator_codes:
        return AiChatResponse(
            answer="Mình chưa xác định được chỉ số bạn muốn phân tích.",
            questionType="NEED_CLARIFICATION",
            data=[],
            chart=AiAgentChartConfig(type="none"),
            warnings=[],
            metadata=AiAgentMetadata(
                source="template",
                toolsUsed=[
                    "indicator_resolver",
                    "country_resolver",
                    "year_resolver",
                ],
                indicators=[],
                countries=country_codes,
                years=years,
                resolved=metadata["resolved"],
            ),
        )

    if len(country_codes) < 2:
        return AiChatResponse(
            answer=(
                "Phase 4 hiện mới hỗ trợ so sánh từ 2 quốc gia trở lên. "
                "Bạn hãy nhập câu kiểu: So sánh nợ công Việt Nam và Thái Lan từ 2010 đến 2023."
            ),
            questionType="NEED_CLARIFICATION",
            data=[
                {
                    "message": normalized_message,
                    "resolved": metadata["resolved"],
                }
            ],
            chart=AiAgentChartConfig(type="none"),
            warnings=[],
            metadata=AiAgentMetadata(
                source="template",
                toolsUsed=[
                    "indicator_resolver",
                    "country_resolver",
                    "year_resolver",
                ],
                indicators=indicator_codes,
                analytics_indicators=metadata["analytics_indicators"],
                raw_only_indicators=metadata["raw_only_indicators"],
                countries=country_codes,
                years=years,
                resolved=metadata["resolved"],
            ),
        )

    indicator_code = indicator_codes[0]

    start_year = slots.start_year
    end_year = slots.end_year

    try:
        compare_result = compare_countries(
            indicator_code=indicator_code,
            country_codes=country_codes,
            start_year=start_year,
            end_year=end_year,
        )
    except ToolError as error:
        return AiChatResponse(
            answer=f"Chỉ số này chưa được hỗ trợ bởi DB tool: {str(error)}",
            questionType="UNSUPPORTED_DATA_QUERY",
            data=[],
            chart=AiAgentChartConfig(type="none"),
            warnings=[str(error)],
            metadata=AiAgentMetadata(
                source="template",
                toolsUsed=[
                    "indicator_resolver",
                    "country_resolver",
                    "year_resolver",
                    "compare_tool",
                ],
                indicators=indicator_codes,
                countries=country_codes,
                years=years,
                resolved=metadata["resolved"],
            ),
        )

    rows = compare_result["rows"]
    coverage = compare_result["coverage"]
    chart_data = build_compare_line_chart_data(rows)

    answer = (
        f"Đã query dữ liệu thật cho chỉ số {indicator_code} "
        f"của {', '.join(country_codes)}"
    )

    if start_year is not None and end_year is not None:
        answer += f" trong giai đoạn {start_year}-{end_year}"

    answer += f". Tìm thấy {len(rows)} dòng dữ liệu."

    warnings: list[str] = []

    if not rows:
        warnings.append(
            "Không tìm thấy dữ liệu phù hợp trong database cho bộ lọc hiện tại."
        )

    return AiChatResponse(
        answer=answer,
        questionType="VALID_COMPARE_QUERY",
        data=[
            {
                "message": normalized_message,
                "conversationId": payload.conversationId,
                "context": payload.context,
                "resolved": metadata["resolved"],
                "indicator": indicator_code,
                "countries": country_codes,
                "start_year": start_year,
                "end_year": end_year,
                "coverage": coverage,
                "rows": rows,
            }
        ],
        chart=AiAgentChartConfig(
            type="line" if rows else "none",
            title=f"{indicator_code} comparison",
            xKey="year",
            yKeys=country_codes,
            data=chart_data,
        ),
        warnings=warnings,
        metadata=AiAgentMetadata(
            source="template",
            toolsUsed=[
                "indicator_resolver",
                "country_resolver",
                "year_resolver",
                "compare_tool",
                "indicator_series_tool",
                "coverage_tool",
            ],
            indicators=indicator_codes,
            analytics_indicators=metadata["analytics_indicators"],
            raw_only_indicators=metadata["raw_only_indicators"],
            countries=country_codes,
            years=years,
            resolved=metadata["resolved"],
        ),
    )