from typing import Any, Literal

from fastapi import APIRouter, Depends

from app.composer.chart_composer import (
    build_anomaly_bar_chart_data,
    build_compare_line_chart_data,
    build_ranking_bar_chart_data,
    build_series_line_chart_data,
)
from app.composer.followup_composer import compose_followup_analysis_answer
from app.composer.gemini_composer import compose_gemini_answer, should_use_gemini
from app.composer.template_composer import (
    compose_anomaly_answer,
    compose_compare_answer,
    compose_coverage_answer,
    compose_fallback_answer,
    compose_need_clarification_answer,
    compose_off_topic_answer,
    compose_ranking_answer,
    compose_trend_answer,
    compose_unsupported_answer,
)
from app.conversation.context_store import (
    build_router_context,
    get_conversation_context,
    summarize_rows,
    update_conversation_context,
)
from app.core.config import settings
from app.core.security import verify_internal_api_key
from app.executor.tool_executor import execute_query_plan
from app.parser.hybrid_parser import parse_with_hybrid_parser
from app.planner.plan_schema import QueryPlan
from app.resolver.slot_resolver import resolved_slots_to_metadata
from app.router.gemini_router import RouterDecision, route_message
from app.schemas.chat import (
    AiAgentChartConfig,
    AiAgentMetadata,
    AiChatRequest,
    AiChatResponse,
)


MetadataSource = Literal["template", "gemini", "mock"]


router = APIRouter(
    prefix="/agent",
    tags=["agent"],
    dependencies=[Depends(verify_internal_api_key)],
)


def make_metadata(
    metadata: dict,
    source: MetadataSource,
    tools_used: list[str],
) -> AiAgentMetadata:
    return AiAgentMetadata(
        source=source,
        toolsUsed=tools_used,
        indicators=metadata["indicators"],
        analytics_indicators=metadata["analytics_indicators"],
        raw_only_indicators=metadata["raw_only_indicators"],
        countries=metadata["countries"],
        years=metadata["years"],
        resolved=metadata["resolved"],
    )


def make_empty_metadata(source: MetadataSource, tools_used: list[str]) -> AiAgentMetadata:
    return AiAgentMetadata(
        source=source,
        toolsUsed=tools_used,
        indicators=[],
        analytics_indicators=[],
        raw_only_indicators=[],
        countries=[],
        years=[],
        resolved=None,
    )


def plan_to_dict(plan: QueryPlan) -> dict:
    return {
        "question_type": plan.question_type,
        "tool_name": plan.tool_name,
        "arguments": plan.arguments,
        "warnings": plan.warnings,
    }


def maybe_gemini_answer(
    user_message: str,
    question_type: str,
    indicator_code: str | None,
    result_payload: dict,
    template_answer: str,
    row_count: int,
) -> tuple[str, MetadataSource]:
    if not should_use_gemini(question_type, row_count):
        return template_answer, "template"

    answer = compose_gemini_answer(
        user_message=user_message,
        question_type=question_type,
        indicator_code=indicator_code,
        result_payload=result_payload,
        template_answer=template_answer,
    )

    if answer == template_answer:
        return answer, "template"

    return answer, "gemini"


@router.post("/chat", response_model=AiChatResponse)
def chat(payload: AiChatRequest) -> AiChatResponse:
    normalized_message = payload.message.strip()
    conversation_id = payload.conversationId or "__default__"
    previous_context = get_conversation_context(conversation_id)
    router_context = build_router_context(previous_context)
    router_decision = route_message(normalized_message, router_context)

    if router_decision.route in {"DIRECT_ANSWER", "GENERAL_EXPLANATION"}:
        return _handle_direct_answer(
            payload=payload,
            message=normalized_message,
            router_decision=router_decision,
        )

    if router_decision.route == "NEED_CLARIFICATION":
        return _handle_router_clarification(
            payload=payload,
            message=normalized_message,
            router_decision=router_decision,
        )

    if router_decision.route in {"UNSUPPORTED", "OFF_TOPIC"}:
        return _handle_router_stop(
            payload=payload,
            message=normalized_message,
            router_decision=router_decision,
        )

    if router_decision.route == "FOLLOW_UP_ANALYSIS":
        return _handle_followup_analysis(
            payload=payload,
            message=normalized_message,
            previous_context=previous_context,
            router_context=router_context,
            router_decision=router_decision,
        )

    if router_decision.route == "FOLLOW_UP_MODIFY_QUERY":
        query_text = router_decision.rewritten_query or normalized_message
        parser_context = {
            "conversation": router_context,
            "previous_parsed_query": previous_context.get("last_parsed_query"),
            "original_user_message": normalized_message,
            "router_rewritten_query": router_decision.rewritten_query,
        }
        return _run_parser_db_flow(
            payload=payload,
            query_text=query_text,
            original_message=normalized_message,
            parser_context=parser_context,
            router_decision=router_decision,
        )

    parser_context = {
        "frontend_context": payload.context,
        "conversation": router_context,
    }
    return _run_parser_db_flow(
        payload=payload,
        query_text=normalized_message,
        original_message=normalized_message,
        parser_context=parser_context,
        router_decision=router_decision,
    )


def _handle_direct_answer(
    payload: AiChatRequest,
    message: str,
    router_decision: RouterDecision,
) -> AiChatResponse:
    answer = router_decision.answer or "Câu hỏi này có thể trả lời trực tiếp mà không cần truy vấn dữ liệu."
    source: MetadataSource = "gemini" if router_decision.source == "gemini_router" else "template"
    response = AiChatResponse(
        answer=answer,
        questionType="VALID_SIMPLE_QUERY",
        status="success",
        data=[
            {
                "message": message,
                "conversationId": payload.conversationId,
                "route": router_decision.route,
            }
        ],
        chart=AiAgentChartConfig(type="none"),
        warnings=[],
        metadata=make_empty_metadata(source, ["gemini_router"]),
        parsedQuery=None,
        parserDebug=None,
        routerDebug=router_decision.to_dict(),
    )
    _update_context_basic(payload.conversationId, message, answer, router_decision.route, "success")
    return response


def _handle_router_clarification(
    payload: AiChatRequest,
    message: str,
    router_decision: RouterDecision,
) -> AiChatResponse:
    question = router_decision.clarification_question or "Bạn muốn phân tích chỉ số, quốc gia và giai đoạn nào?"
    questions = [question]
    answer = compose_need_clarification_answer(questions)
    response = AiChatResponse(
        answer=answer,
        questionType="NEED_CLARIFICATION",
        status="needs_clarification",
        clarificationQuestions=questions,
        data=[
            {
                "message": message,
                "conversationId": payload.conversationId,
                "route": router_decision.route,
            }
        ],
        chart=AiAgentChartConfig(type="none"),
        warnings=questions,
        metadata=make_empty_metadata("gemini" if router_decision.source == "gemini_router" else "template", ["gemini_router"]),
        parsedQuery=None,
        parserDebug=None,
        routerDebug=router_decision.to_dict(),
    )
    _update_context_basic(payload.conversationId, message, answer, router_decision.route, "needs_clarification")
    return response


def _handle_router_stop(
    payload: AiChatRequest,
    message: str,
    router_decision: RouterDecision,
) -> AiChatResponse:
    if router_decision.route == "OFF_TOPIC":
        answer = router_decision.answer or compose_off_topic_answer()
        question_type = "OFF_TOPIC"
        status = "off_topic"
    else:
        answer = router_decision.answer or compose_unsupported_answer([router_decision.reason] if router_decision.reason else None)
        question_type = "UNSUPPORTED"
        status = "unsupported"

    response = AiChatResponse(
        answer=answer,
        questionType=question_type,
        status=status,
        data=[
            {
                "message": message,
                "conversationId": payload.conversationId,
                "route": router_decision.route,
            }
        ],
        chart=AiAgentChartConfig(type="none"),
        warnings=[],
        metadata=make_empty_metadata("gemini" if router_decision.source == "gemini_router" else "template", ["gemini_router"]),
        parsedQuery=None,
        parserDebug=None,
        routerDebug=router_decision.to_dict(),
    )
    _update_context_basic(payload.conversationId, message, answer, router_decision.route, status)
    return response


def _handle_followup_analysis(
    payload: AiChatRequest,
    message: str,
    previous_context: dict[str, Any],
    router_context: dict[str, Any],
    router_decision: RouterDecision,
) -> AiChatResponse:
    if not previous_context.get("last_answer") and not previous_context.get("last_rows"):
        clarification = "Bạn muốn mình phân tích kết quả nào trước? Hiện chưa có kết quả dữ liệu trong cuộc hội thoại này."
        fallback_decision = RouterDecision(
            route="NEED_CLARIFICATION",
            confidence=router_decision.confidence,
            needs_parser=False,
            needs_db=False,
            uses_previous_result=False,
            clarification_question=clarification,
            reason="missing_previous_result",
            source=router_decision.source,
        )
        return _handle_router_clarification(payload, message, fallback_decision)

    tools_used = ["gemini_router", "conversation_context"]
    if router_decision.answer:
        answer = router_decision.answer
        source: MetadataSource = "gemini" if router_decision.source == "gemini_router" else "template"
    else:
        answer, used_gemini = compose_followup_analysis_answer(
            user_message=message,
            router_context=router_context,
            fallback_answer=router_decision.answer,
        )
        if used_gemini:
            tools_used.append("gemini_composer")
        source = "gemini" if used_gemini else "template"

    response = AiChatResponse(
        answer=answer,
        questionType="VALID_SIMPLE_QUERY",
        status="success",
        data=[
            {
                "message": message,
                "conversationId": payload.conversationId,
                "route": router_decision.route,
                "previousDataSummary": router_context.get("last_data_summary"),
            }
        ],
        chart=AiAgentChartConfig(type="none"),
        warnings=[],
        metadata=make_empty_metadata(source, tools_used),
        parsedQuery=previous_context.get("last_parsed_query") or None,
        parserDebug=None,
        routerDebug=router_decision.to_dict(),
    )
    _update_context_basic(payload.conversationId, message, answer, router_decision.route, "success")
    return response


def _run_parser_db_flow(
    payload: AiChatRequest,
    query_text: str,
    original_message: str,
    parser_context: dict[str, Any],
    router_decision: RouterDecision,
) -> AiChatResponse:
    parse_result = parse_with_hybrid_parser(query_text, parser_context)
    slots = parse_result.slots
    metadata = resolved_slots_to_metadata(slots)

    question_type = parse_result.question_type
    plan = parse_result.plan

    if parse_result.parser_debug.get("source") == "model_parser":
        base_tools = [
            "gemini_router",
            "parser_model_service",
            "model_parser_adapter",
            "query_planner",
        ]
    else:
        base_tools = [
            "gemini_router",
            "indicator_resolver",
            "country_resolver",
            "year_resolver",
            "rule_router",
            "query_planner",
        ]

    response_debug = {
        "parsedQuery": parse_result.parsed_query,
        "parserDebug": parse_result.parser_debug,
        "routerDebug": router_decision.to_dict(),
    }

    indicator_code = metadata["indicators"][0] if metadata["indicators"] else None
    country_codes = metadata["countries"]
    start_year = metadata["resolved"].get("start_year")
    end_year = metadata["resolved"].get("end_year")

    if question_type == "OFF_TOPIC":
        response = AiChatResponse(
            answer=compose_off_topic_answer(),
            questionType="OFF_TOPIC",
            status=parse_result.status or "off_topic",
            data=[
                _base_data_item(payload, original_message, query_text, metadata, plan, router_decision)
            ],
            chart=AiAgentChartConfig(type="none"),
            warnings=[],
            metadata=make_metadata(metadata, "template", base_tools),
            **response_debug,
        )
        _update_context_basic(payload.conversationId, original_message, response.answer, router_decision.route, response.status)
        return response

    if plan.question_type == "NEED_CLARIFICATION":
        clarification_questions = plan.warnings or slots.clarification_questions
        response = AiChatResponse(
            answer=compose_need_clarification_answer(clarification_questions),
            questionType="NEED_CLARIFICATION",
            status="needs_clarification",
            clarificationQuestions=clarification_questions,
            data=[
                _base_data_item(payload, original_message, query_text, metadata, plan, router_decision)
            ],
            chart=AiAgentChartConfig(type="none"),
            warnings=clarification_questions,
            metadata=make_metadata(metadata, "template", base_tools),
            **response_debug,
        )
        _update_context_basic(
            payload.conversationId,
            original_message,
            response.answer,
            router_decision.route,
            response.status,
            parsed_query=parse_result.parsed_query,
            parser_debug=parse_result.parser_debug,
        )
        return response

    if plan.question_type in {"UNSUPPORTED_DATA_QUERY", "UNSUPPORTED"}:
        response = AiChatResponse(
            answer=compose_unsupported_answer(plan.warnings),
            questionType=plan.question_type,
            status="unsupported",
            data=[
                _base_data_item(payload, original_message, query_text, metadata, plan, router_decision)
            ],
            chart=AiAgentChartConfig(type="none"),
            warnings=plan.warnings,
            metadata=make_metadata(metadata, "template", base_tools),
            **response_debug,
        )
        _update_context_basic(
            payload.conversationId,
            original_message,
            response.answer,
            router_decision.route,
            response.status,
            parsed_query=parse_result.parsed_query,
            parser_debug=parse_result.parser_debug,
        )
        return response

    try:
        executed = execute_query_plan(plan)
    except Exception as error:
        response = AiChatResponse(
            answer=compose_unsupported_answer(
                [
                    "Có lỗi khi chạy DB tool.",
                    str(error),
                ]
            ),
            questionType="UNSUPPORTED_DATA_QUERY",
            status="unsupported",
            data=[
                {
                    **_base_data_item(payload, original_message, query_text, metadata, plan, router_decision),
                    "error": str(error),
                }
            ],
            chart=AiAgentChartConfig(type="none"),
            warnings=[
                "Tool execution failed.",
                str(error),
            ],
            metadata=make_metadata(metadata, "template", base_tools),
            **response_debug,
        )
        _update_context_basic(
            payload.conversationId,
            original_message,
            response.answer,
            router_decision.route,
            response.status,
            parsed_query=parse_result.parsed_query,
            parser_debug=parse_result.parser_debug,
        )
        return response

    result = executed["result"]
    tool_name = executed["tool"]
    tools_used = [*base_tools, tool_name]

    if plan.question_type == "VALID_COMPARE_QUERY":
        rows = result["rows"]
        coverage = result["coverage"]
        chart_data = build_compare_line_chart_data(rows)

        template_answer = compose_compare_answer(
            indicator_code=indicator_code,
            country_codes=country_codes,
            start_year=start_year,
            end_year=end_year,
            rows=rows,
        )

        result_payload = {
            "indicator": indicator_code,
            "countries": country_codes,
            "coverage": coverage,
            "rows": rows,
        }

        answer, source = maybe_gemini_answer(
            user_message=original_message,
            question_type=plan.question_type,
            indicator_code=indicator_code,
            result_payload=result_payload,
            template_answer=template_answer,
            row_count=len(rows),
        )

        chart = AiAgentChartConfig(
            type="line" if rows else "none",
            title=f"{indicator_code} comparison",
            xKey="year",
            yKeys=country_codes,
            data=chart_data,
        )
        response = AiChatResponse(
            answer=answer,
            questionType="VALID_COMPARE_QUERY",
            status="success",
            data=[
                {
                    **_base_data_item(payload, original_message, query_text, metadata, plan, router_decision),
                    "indicator": indicator_code,
                    "countries": country_codes,
                    "coverage": coverage,
                    "rows": rows,
                }
            ],
            chart=chart,
            warnings=[] if rows else ["Không tìm thấy dữ liệu phù hợp."],
            metadata=make_metadata(metadata, source, tools_used),
            **response_debug,
        )
        _update_context_query_success(payload.conversationId, original_message, response, router_decision, parse_result, rows, chart, metadata, indicator_code, country_codes)
        return response

    if plan.question_type == "VALID_RANKING_QUERY":
        rows = result
        year = plan.arguments.get("year")

        template_answer = compose_ranking_answer(
            indicator_code=indicator_code,
            year=year,
            rows=rows,
        )

        result_payload = {
            "indicator": indicator_code,
            "year": year,
            "rows": rows,
        }

        answer, source = maybe_gemini_answer(
            user_message=original_message,
            question_type=plan.question_type,
            indicator_code=indicator_code,
            result_payload=result_payload,
            template_answer=template_answer,
            row_count=len(rows),
        )

        chart = AiAgentChartConfig(
            type="bar" if rows else "none",
            title=f"Top countries by {indicator_code} in {year}",
            xKey="country_code",
            yKeys=["value"],
            data=build_ranking_bar_chart_data(rows),
        )
        response = AiChatResponse(
            answer=answer,
            questionType="VALID_RANKING_QUERY",
            status="success",
            data=[
                {
                    **_base_data_item(payload, original_message, query_text, metadata, plan, router_decision),
                    "indicator": indicator_code,
                    "year": year,
                    "rows": rows,
                }
            ],
            chart=chart,
            warnings=[] if rows else ["Không tìm thấy dữ liệu ranking phù hợp."],
            metadata=make_metadata(metadata, source, tools_used),
            **response_debug,
        )
        _update_context_query_success(payload.conversationId, original_message, response, router_decision, parse_result, rows, chart, metadata, indicator_code, country_codes)
        return response

    if plan.question_type == "VALID_COVERAGE_QUERY":
        rows = result

        template_answer = compose_coverage_answer(
            indicator_code=indicator_code,
            rows=rows,
        )

        result_payload = {
            "indicator": indicator_code,
            "rows": rows,
        }

        answer, source = maybe_gemini_answer(
            user_message=original_message,
            question_type=plan.question_type,
            indicator_code=indicator_code,
            result_payload=result_payload,
            template_answer=template_answer,
            row_count=len(rows),
        )

        chart = AiAgentChartConfig(
            type="table" if rows else "none",
            title=f"Coverage for {indicator_code}",
            xKey=None,
            yKeys=None,
            data=rows,
        )
        response = AiChatResponse(
            answer=answer,
            questionType="VALID_COVERAGE_QUERY",
            status="success",
            data=[
                {
                    **_base_data_item(payload, original_message, query_text, metadata, plan, router_decision),
                    "indicator": indicator_code,
                    "rows": rows,
                }
            ],
            chart=chart,
            warnings=[] if rows else ["Không tìm thấy coverage phù hợp."],
            metadata=make_metadata(metadata, source, tools_used),
            **response_debug,
        )
        _update_context_query_success(payload.conversationId, original_message, response, router_decision, parse_result, rows, chart, metadata, indicator_code, country_codes)
        return response

    if plan.question_type == "VALID_ANOMALY_QUERY":
        rows = result
        threshold = plan.arguments.get("threshold", 0.75)

        template_answer = compose_anomaly_answer(
            indicator_code=indicator_code,
            country_codes=country_codes,
            start_year=start_year,
            end_year=end_year,
            rows=rows,
            threshold=threshold,
        )

        result_payload = {
            "indicator": indicator_code,
            "countries": country_codes,
            "threshold": threshold,
            "rows": rows,
        }

        answer, source = maybe_gemini_answer(
            user_message=original_message,
            question_type=plan.question_type,
            indicator_code=indicator_code,
            result_payload=result_payload,
            template_answer=template_answer,
            row_count=len(rows),
        )

        chart = AiAgentChartConfig(
            type="bar" if rows else "none",
            title=f"Anomalies for {indicator_code}",
            xKey="year",
            yKeys=["anomaly_score"],
            data=build_anomaly_bar_chart_data(rows),
        )
        response = AiChatResponse(
            answer=answer,
            questionType="VALID_ANOMALY_QUERY",
            status="success",
            data=[
                {
                    **_base_data_item(payload, original_message, query_text, metadata, plan, router_decision),
                    "indicator": indicator_code,
                    "countries": country_codes,
                    "threshold": threshold,
                    "rows": rows,
                }
            ],
            chart=chart,
            warnings=[] if rows else ["Không tìm thấy điểm bất thường phù hợp."],
            metadata=make_metadata(metadata, source, tools_used),
            **response_debug,
        )
        _update_context_query_success(payload.conversationId, original_message, response, router_decision, parse_result, rows, chart, metadata, indicator_code, country_codes)
        return response

    if plan.question_type == "VALID_TREND_QUERY":
        rows = result

        is_analytics_series = plan.tool_name == "get_indicator_analytics_series"

        if is_analytics_series:
            chart_data = rows
            y_keys = ["actual_value", "trend_value"]
            chart_title = f"{indicator_code} actual vs trend"
        else:
            chart_data = build_series_line_chart_data(rows)
            y_keys = ["value"]
            chart_title = f"{indicator_code} trend"

        template_answer = compose_trend_answer(
            indicator_code=indicator_code,
            country_codes=country_codes,
            start_year=start_year,
            end_year=end_year,
            rows=rows,
            is_analytics_series=is_analytics_series,
        )

        result_payload = {
            "indicator": indicator_code,
            "countries": country_codes,
            "is_analytics_series": is_analytics_series,
            "rows": rows,
        }

        answer, source = maybe_gemini_answer(
            user_message=original_message,
            question_type=plan.question_type,
            indicator_code=indicator_code,
            result_payload=result_payload,
            template_answer=template_answer,
            row_count=len(rows),
        )

        chart = AiAgentChartConfig(
            type="line" if rows else "none",
            title=chart_title,
            xKey="year",
            yKeys=y_keys,
            data=chart_data,
        )
        response = AiChatResponse(
            answer=answer,
            questionType="VALID_TREND_QUERY",
            status="success",
            data=[
                {
                    **_base_data_item(payload, original_message, query_text, metadata, plan, router_decision),
                    "indicator": indicator_code,
                    "countries": country_codes,
                    "is_analytics_series": is_analytics_series,
                    "rows": rows,
                }
            ],
            chart=chart,
            warnings=[] if rows else ["Không tìm thấy dữ liệu chuỗi thời gian phù hợp."],
            metadata=make_metadata(metadata, source, tools_used),
            **response_debug,
        )
        _update_context_query_success(payload.conversationId, original_message, response, router_decision, parse_result, rows, chart, metadata, indicator_code, country_codes)
        return response

    response = AiChatResponse(
        answer=compose_fallback_answer(
            {
                "question_type": plan.question_type,
                "tool_name": plan.tool_name,
            }
        ),
        questionType="UNSUPPORTED_DATA_QUERY",
        status="unsupported",
        data=[
            _base_data_item(payload, original_message, query_text, metadata, plan, router_decision)
        ],
        chart=AiAgentChartConfig(type="none"),
        warnings=["Missing response composer for this plan type."],
        metadata=make_metadata(metadata, "template", tools_used),
        **response_debug,
    )
    _update_context_basic(
        payload.conversationId,
        original_message,
        response.answer,
        router_decision.route,
        response.status,
        parsed_query=parse_result.parsed_query,
        parser_debug=parse_result.parser_debug,
    )
    return response


def _base_data_item(
    payload: AiChatRequest,
    original_message: str,
    query_text: str,
    metadata: dict[str, Any],
    plan: QueryPlan,
    router_decision: RouterDecision,
) -> dict[str, Any]:
    item = {
        "message": original_message,
        "conversationId": payload.conversationId,
        "context": payload.context,
        "resolved": metadata["resolved"],
        "plan": plan_to_dict(plan),
        "route": router_decision.route,
    }
    if query_text != original_message:
        item["rewritten_query"] = query_text
    return item


def _update_context_basic(
    conversation_id: str | None,
    message: str,
    answer: str,
    route: str,
    status: str,
    parsed_query: dict[str, Any] | None = None,
    parser_debug: dict[str, Any] | None = None,
) -> None:
    patch: dict[str, Any] = {
        "last_user_message": message,
        "last_answer": answer,
        "last_route": route,
        "last_status": status,
    }
    if parsed_query is not None:
        patch["last_parsed_query"] = parsed_query
    if parser_debug is not None:
        patch["last_parser_debug"] = parser_debug
    update_conversation_context(conversation_id, patch)


def _update_context_query_success(
    conversation_id: str | None,
    original_message: str,
    response: AiChatResponse,
    router_decision: RouterDecision,
    parse_result: Any,
    rows: list[dict],
    chart: AiAgentChartConfig,
    metadata: dict[str, Any],
    indicator_code: str | None,
    country_codes: list[str],
) -> None:
    row_summary = summarize_rows(rows, settings.conversation_context_max_rows)
    chart_dict = chart.model_dump()
    chart_without_data = {key: value for key, value in chart_dict.items() if key != "data"}
    update_conversation_context(
        conversation_id,
        {
            "last_user_message": original_message,
            "last_answer": response.answer,
            "last_route": router_decision.route,
            "last_status": response.status,
            "last_parsed_query": parse_result.parsed_query or {},
            "last_rows": row_summary["top_rows"],
            "last_chart": chart_without_data,
            "last_data_summary": {
                "indicator": indicator_code,
                "countries": country_codes,
                "years": metadata.get("years", []),
                "row_count": row_summary["row_count"],
                "top_rows": row_summary["top_rows"],
            },
            "last_parser_debug": parse_result.parser_debug,
        },
    )
