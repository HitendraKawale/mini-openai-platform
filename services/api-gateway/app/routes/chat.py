import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import settings
from app.middleware.auth import verify_api_key
from app.models.chat import ChatCompletionRequest
from app.services.downstream_client import post_json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/chat", tags=["chat"])


@router.post("/completions", dependencies=[Depends(verify_api_key)])
async def chat_completions(payload: ChatCompletionRequest, request: Request):
    try:
        user_messages = [m.content for m in payload.messages if m.role == "user"]
        prompt = "\n".join(user_messages).strip()

        if not prompt:
            prompt = "\n".join([m.content for m in payload.messages]).strip()

        downstream_payload = {
            "prompt": prompt,
            "max_new_tokens": payload.max_tokens,
            "temperature": payload.temperature,
            "do_sample": True,
        }

        result = await post_json(
            url=f"{settings.LLM_SERVICE_URL}/generate",
            payload=downstream_payload,
            request_id=request.state.request_id,
        )

        return {
            "id": request.state.request_id,
            "object": "chat.completion",
            "model": result["model_name"],
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result["generated_text"],
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": result["usage"],
        }

    except httpx.HTTPStatusError as exc:
        logger.exception("llm_service_http_error")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM service returned an error: {exc.response.text}",
        ) from exc
    except httpx.HTTPError as exc:
        logger.exception("llm_service_unreachable")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM service unreachable: {str(exc)}",
        ) from exc
    except Exception as exc:
        logger.exception("chat_completion_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gateway chat completion failed: {str(exc)}",
        ) from exc