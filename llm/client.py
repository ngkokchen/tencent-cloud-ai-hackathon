"""LLM client wrapper — OpenAI-compatible, works with Tencent Hunyuan or any provider."""

import json
import os
from typing import Optional

from openai import OpenAI


class LLMClient:
    """
    Thin wrapper around the OpenAI Python SDK.
    Works with any OpenAI-compatible endpoint (Tencent Hunyuan, OpenAI, DeepSeek, etc.)
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.base_url = base_url or os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o")

        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
            )
        return self._client

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        json_mode: bool = False,
        max_tokens: int = 4096,
    ) -> str:
        """
        Send a chat completion request and return the text response.

        Args:
            messages: list of {"role": "system"|"user"|"assistant", "content": "..."}
            temperature: 0.0 = deterministic, 1.0 = creative
            json_mode: if True, forces response to be valid JSON
            max_tokens: max response length

        Returns:
            The response text (string).
        """
        kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    def chat_json(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
    ) -> dict:
        """
        Convenience method: send system + user message, get parsed JSON back.

        Returns:
            Parsed JSON dict. Raises json.JSONDecodeError if the response
            is not valid JSON.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        raw = self.chat(messages, temperature=temperature, json_mode=True)
        return json.loads(raw)
