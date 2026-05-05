import json
from typing import Any

from app.llm.gemini_client import GeminiClientError, generate_gemini_text


def compose_followup_analysis_answer(
    user_message: str,
    router_context: dict[str, Any],
    fallback_answer: str | None = None,
) -> tuple[str, bool]:
    prompt_payload = {
        "user_message": user_message,
        "previous_context": router_context,
    }
    prompt = f"""
Bạn là AI analyst cho Government AI Agent Platform.

Nhiệm vụ:
- Viết tiếng Việt.
- Chỉ dựa trên previous_context được cung cấp.
- Không bịa số liệu, không thêm số ngoài JSON.
- Nếu user hỏi "vì sao"/"lý do", hãy nói rõ đây là phân tích định tính dựa trên kết quả trước, không phải bằng chứng nhân quả trực tiếp.
- Không query DB, không nói bạn đã query DB.
- Trả lời ngắn gọn, có insight chính.

Input:
{json.dumps(prompt_payload, ensure_ascii=False, indent=2, default=str)}
""".strip()

    try:
        return generate_gemini_text(prompt), True
    except GeminiClientError:
        if fallback_answer:
            return fallback_answer, False
        return (
            "Dựa trên kết quả trước, mình có thể nhận xét ở mức định tính nhưng không có đủ dữ liệu bổ sung để kết luận nguyên nhân nhân quả trực tiếp.",
            False,
        )
