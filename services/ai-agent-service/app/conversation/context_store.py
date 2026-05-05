from copy import deepcopy
from typing import Any

from app.core.config import settings


DEFAULT_CONVERSATION_ID = "__default__"
_CONVERSATIONS: dict[str, dict[str, Any]] = {}


def _key(conversation_id: str | None) -> str:
    return conversation_id or DEFAULT_CONVERSATION_ID


def _empty_context(conversation_id: str | None) -> dict[str, Any]:
    return {
        "conversation_id": _key(conversation_id),
        "last_user_message": None,
        "last_answer": None,
        "last_route": None,
        "last_status": None,
        "last_parsed_query": {},
        "last_rows": [],
        "last_chart": {},
        "last_data_summary": {},
        "last_parser_debug": {},
        "turn_count": 0,
    }


def get_conversation_context(conversation_id: str | None) -> dict[str, Any]:
    key = _key(conversation_id)
    if key not in _CONVERSATIONS:
        _CONVERSATIONS[key] = _empty_context(key)
    return deepcopy(_CONVERSATIONS[key])


def update_conversation_context(
    conversation_id: str | None,
    patch: dict[str, Any],
) -> dict[str, Any]:
    key = _key(conversation_id)
    current = _CONVERSATIONS.get(key) or _empty_context(key)
    next_context = {**current, **patch}
    next_context["conversation_id"] = key
    next_context["turn_count"] = int(current.get("turn_count") or 0) + 1
    _CONVERSATIONS[key] = next_context
    return deepcopy(next_context)


def summarize_rows(rows: list[dict], max_rows: int) -> dict[str, Any]:
    safe_rows = rows if isinstance(rows, list) else []
    safe_limit = max(0, max_rows)
    return {
        "row_count": len(safe_rows),
        "top_rows": deepcopy(safe_rows[:safe_limit]),
    }


def build_router_context(context: dict[str, Any]) -> dict[str, Any]:
    last_chart = context.get("last_chart") or {}
    chart_metadata = {
        key: value
        for key, value in last_chart.items()
        if key != "data"
    }

    max_rows = settings.conversation_context_max_rows
    last_rows = context.get("last_rows") or []

    return {
        "conversation_id": context.get("conversation_id"),
        "turn_count": context.get("turn_count", 0),
        "last_user_message": context.get("last_user_message"),
        "last_answer": context.get("last_answer"),
        "last_route": context.get("last_route"),
        "last_status": context.get("last_status"),
        "last_parsed_query": context.get("last_parsed_query") or {},
        "last_data_summary": context.get("last_data_summary") or {},
        "last_chart": chart_metadata,
        "last_rows": deepcopy(last_rows[:max_rows]),
    }
