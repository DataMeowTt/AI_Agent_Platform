import json
from typing import Any

from app.llm.gemini_client import GeminiClientError, generate_gemini_text, is_gemini_enabled


MAX_ROWS_FOR_GEMINI = 80


def _safe_json(data: Any) -> str:
    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
        default=str,
    )


def _truncate_rows(rows: list[dict], max_rows: int = MAX_ROWS_FOR_GEMINI) -> list[dict]:
    if len(rows) <= max_rows:
        return rows

    return rows[:max_rows]


def should_use_gemini(question_type: str, row_count: int) -> bool:
    if not is_gemini_enabled():
        return False

    if question_type in {
        "OFF_TOPIC",
        "NEED_CLARIFICATION",
        "UNSUPPORTED_DATA_QUERY",
    }:
        return False

    return row_count > 0


def compose_gemini_answer(
    user_message: str,
    question_type: str,
    indicator_code: str | None,
    result_payload: dict[str, Any],
    template_answer: str,
) -> str:
    rows = result_payload.get("rows", [])

    if isinstance(rows, list):
        rows_for_prompt = _truncate_rows(rows)
    else:
        rows_for_prompt = rows

    prompt_payload = {
        "user_message": user_message,
        "question_type": question_type,
        "indicator_code": indicator_code,
        "template_answer": template_answer,
        "result": {
            **result_payload,
            "rows": rows_for_prompt,
        },
    }

    prompt = f"""
Bạn là AI analyst cho Government AI Agent Platform.

Nhiệm vụ:
- Viết câu trả lời bằng tiếng Việt.
- Dựa CHỈ trên dữ liệu JSON được cung cấp.
- Không bịa số liệu.
- Không tự suy đoán ngoài dữ liệu.
- Không viết SQL.
- Không nói rằng bạn đã query database.
- Nếu dữ liệu rỗng, nói rõ là không tìm thấy dữ liệu phù hợp.
- Trả lời ngắn gọn, có insight chính, không quá dài.

Dữ liệu đầu vào:
{_safe_json(prompt_payload)}

Hãy viết câu trả lời cuối cho user.
""".strip()

    try:
        return generate_gemini_text(prompt)
    except GeminiClientError:
        # Fallback an toàn: nếu Gemini lỗi thì vẫn trả template.
        return template_answer