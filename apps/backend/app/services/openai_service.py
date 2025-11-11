import os
from textwrap import dedent
from typing import Optional

from dotenv import load_dotenv
from fastapi import HTTPException
from openai import AsyncOpenAI, OpenAIError


_client: Optional[AsyncOpenAI] = None


load_dotenv()


def _get_client() -> AsyncOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key is not configured")

    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=api_key)
    return _client


async def generate_data(prompt: str) -> str:
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt must not be empty")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = _get_client()

    system_prompt = dedent(
        """
        You are a meticulous data analyst. When given a user request, you must select an appropriate
        visualization for the existing dataset that the application already holds. Never fabricate or emit
        actual dataset rows. Respond strictly with valid JSON using this schema:
        {"plot_name": string, "chart": {"type": string, "aggregation": "raw_records" | "non_zero_count" |
        "zero_count" | "non_zero_count_by_group", "columns": array[string], "group_by"?: string,
        "value_field"?: string, "summary"?: string}}. Choose the aggregation carefully: use
        "non_zero_count" when the user requests counts of exceptions or non-zero values per column, use
        "zero_count" when the user requests counts of zero values or non-exceptions per column, and use
        "non_zero_count_by_group" when the user asks for counts per date or category. Keep the response concise.
        """
    ).strip()

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        "Recommend a visualization based strictly on the existing dataset available to the "
                        "application. Decide whether the visualization should return raw records or aggregated "
                        "values using the supported aggregation options, and include any necessary group_by "
                        "field when summarising by a dimension. Prompt: "
        f"{prompt}"
                    ),
                },
            ],
            response_format={"type": "json_object"},
        )
    except OpenAIError as exc:  # pragma: no cover - network error path
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {exc}") from exc

    choices = response.choices
    if not choices:
        raise HTTPException(status_code=502, detail="OpenAI API returned no choices")

    content = choices[0].message.content
    if content is None:
        raise HTTPException(status_code=502, detail="OpenAI API returned empty content")

    return content
