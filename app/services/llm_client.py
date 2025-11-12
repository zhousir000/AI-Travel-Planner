import json
from datetime import date, timedelta
from typing import Any

import httpx

from ..core.config import settings
from ..schemas.plan import PlanIntent


class LLMClientError(RuntimeError):
    """Raised when the LLM provider fails."""


class LLMClient:
    def __init__(
        self,
        provider: str | None = None,
        api_key: str | None = None,
        endpoint: str | None = None,
        model: str | None = None,
    ) -> None:
        default_provider = settings.llm_provider or "mock"
        raw_provider = provider or default_provider
        self.provider = raw_provider.lower() if raw_provider else "mock"
        self.api_key = api_key or settings.llm_api_key
        self.endpoint = endpoint or settings.llm_endpoint
        if model is not None:
            self.model = model
        elif provider is None and settings.llm_model:
            self.model = settings.llm_model
        else:
            self.model = None

    async def generate_plan(self, intent: PlanIntent) -> dict[str, Any]:
        if self.provider == "mock":
            return self._mock_plan(intent)
        if self.provider == "dashscope":
            return await self._dashscope_plan(intent)
        if self.provider == "openai":
            return await self._openai_plan(intent)
        raise LLMClientError(f"Unsupported LLM provider: {self.provider}")

    def _build_prompt(self, intent: PlanIntent) -> str:
        duration = intent.duration_days or 5
        travel_style = ", ".join(intent.travel_style or intent.interests) or "balanced mix of sightseeing and food"
        audience = "with children" if intent.traveling_with_children else ""
        custom_request = f"Additional notes: {intent.custom_request}." if intent.custom_request else ""
        date_instructions = ""
        if intent.start_date:
            date_instructions += f" Trip must start on {intent.start_date.isoformat()}."
        if intent.end_date:
            date_instructions += f" Trip must end on {intent.end_date.isoformat()}."
        return (
            "You are an expert travel planner. Craft a detailed itinerary in JSON format. "
            "Ensure the JSON is valid and follows the schema: "
            "{'title': str, 'summary': str, 'days': [{'day': int, 'date': 'YYYY-MM-DD', 'headline': str, "
            "'activities': [{'time': str, 'title': str, 'description': str, 'location': str, "
            "'latitude': float | null, 'longitude': float | null, 'estimated_cost': float}]}], "
            "'budget': {'currency': str, 'total': float, 'items': [{'category': str, 'amount': float, 'notes': str}]}, "
            "'tips': [str]}. "
            f"Destination: {intent.destination}. Duration: {duration} days. "
            f"Budget: {intent.budget_amount or 'estimate based on standard costs'} {intent.currency}. "
            f"Travelers: {intent.travelers or 2} {audience}. Preferences: {travel_style}. "
            f"Every activity must include an estimated_cost number expressed in {intent.currency}. "
            f"{date_instructions} {custom_request} Reply ONLY with JSON."
        )

    async def _dashscope_plan(self, intent: PlanIntent) -> dict[str, Any]:
        if not self.api_key:
            raise LLMClientError("DashScope API key missing (LLM_API_KEY).")
        prompt = self._build_prompt(intent)
        endpoint = (
            self.endpoint
            or "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        )
        model_name = self.model or "qwen-turbo"
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                endpoint,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": model_name,
                    "input": {"prompt": prompt},
                    "parameters": {"result_format": "json"},
                },
            )
        if response.status_code >= 400:
            raise LLMClientError(f"DashScope error: {response.status_code} {response.text}")
        payload = response.json()
        output = payload.get("output", {})
        output_text = self._extract_dashscope_text(output)
        if not output_text:
            keys = ", ".join(output.keys()) if isinstance(output, dict) else "n/a"
            raise LLMClientError(f"DashScope response missing text field (output keys: {keys}).")
        return self._parse_plan_json(output_text)

    async def _openai_plan(self, intent: PlanIntent) -> dict[str, Any]:
        if not self.api_key:
            raise LLMClientError("OpenAI API key missing (LLM_API_KEY).")
        prompt = self._build_prompt(intent)
        api_url = self.endpoint or "https://api.openai.com/v1/chat/completions"
        model_name = self.model or "gpt-4o-mini"
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                api_url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": "You are a travel planning assistant that outputs ONLY JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    "response_format": {"type": "json_object"},
                },
            )
        if response.status_code >= 400:
            raise LLMClientError(f"OpenAI error: {response.status_code} {response.text}")
        payload = response.json()
        choice = payload.get("choices", [{}])[0]
        output_text = choice.get("message", {}).get("content")
        if not output_text:
            raise LLMClientError("OpenAI response missing content.")
        return self._parse_plan_json(output_text)

    def _parse_plan_json(self, text: str) -> dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMClientError(f"Failed to parse LLM JSON: {exc}") from exc

    def _extract_dashscope_text(self, output: Any) -> str | None:
        if not isinstance(output, dict):
            return None

        text = output.get("text")
        if isinstance(text, str) and text.strip():
            return text
        if isinstance(text, list):
            for item in text:
                if isinstance(item, str) and item.strip():
                    return item

        choices = output.get("choices")
        if isinstance(choices, list):
            for choice in choices:
                if not isinstance(choice, dict):
                    continue
                message = choice.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str) and content.strip():
                        return content
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, str) and item.strip():
                                return item
                            if isinstance(item, dict):
                                text_part = item.get("text") or item.get("content")
                                if isinstance(text_part, str) and text_part.strip():
                                    return text_part
                for key in ("content", "text"):
                    candidate = choice.get(key)
                    if isinstance(candidate, str) and candidate.strip():
                        return candidate
                    if isinstance(candidate, list):
                        for item in candidate:
                            if isinstance(item, str) and item.strip():
                                return item
                            if isinstance(item, dict):
                                text_part = item.get("text") or item.get("content")
                                if isinstance(text_part, str) and text_part.strip():
                                    return text_part

        results = output.get("results")
        if isinstance(results, list):
            for result in results:
                if not isinstance(result, dict):
                    continue
                for key in ("text", "content", "completion", "result"):
                    candidate = result.get(key)
                    if isinstance(candidate, str) and candidate.strip():
                        return candidate
                    if isinstance(candidate, list):
                        for item in candidate:
                            if isinstance(item, str) and item.strip():
                                return item
                            if isinstance(item, dict):
                                text_part = item.get("text") or item.get("content")
                                if isinstance(text_part, str) and text_part.strip():
                                    return text_part

        return None

    def _mock_plan(self, intent: PlanIntent) -> dict[str, Any]:
        duration = intent.duration_days or 5
        start = intent.start_date or date.today()
        activities_bank = [
            ("Morning", "Explore local market", "Try regional breakfast delicacies.", 120.0),
            ("Midday", "Visit cultural landmark", "Guided tour with interactive exhibits.", 260.0),
            ("Afternoon", "Hands-on workshop", "Family-friendly activity to learn local crafts.", 320.0),
            ("Evening", "Dinner at recommended restaurant", "Taste signature dishes and desserts.", 200.0),
        ]
        days: list[dict[str, Any]] = []
        for day_offset in range(duration):
            day_date = start + timedelta(days=day_offset)
            activities = []
            for slot, title, description, cost in activities_bank:
                activities.append(
                    {
                        "time": slot,
                        "title": title,
                        "description": description,
                        "location": f"{intent.destination} city center",
                        "latitude": None,
                        "longitude": None,
                        "estimated_cost": cost,
                    }
                )
            days.append(
                {
                    "day": day_offset + 1,
                    "date": day_date.isoformat(),
                    "headline": f"Day {day_offset + 1} highlights in {intent.destination}",
                    "activities": activities,
                }
            )
        estimated_budget = intent.budget_amount or float(duration * 1000)
        return {
            "title": f"{intent.destination} {duration}-Day Adventure",
            "summary": f"A balanced itinerary in {intent.destination} optimized for {intent.travelers or 2} travelers.",
            "days": days,
            "budget": {
                "currency": intent.currency,
                "total": estimated_budget,
                "items": [
                    {"category": "Accommodation", "amount": estimated_budget * 0.4, "notes": "Mid-range hotels"},
                    {"category": "Food", "amount": estimated_budget * 0.2, "notes": "Local restaurants"},
                    {"category": "Activities", "amount": estimated_budget * 0.2, "notes": "Tickets & workshops"},
                    {"category": "Transport", "amount": estimated_budget * 0.15, "notes": "Rail passes & taxis"},
                    {"category": "Misc", "amount": estimated_budget * 0.05, "notes": "Souvenirs & contingency"},
                ],
            },
            "tips": [
                "Reserve popular restaurants two weeks in advance.",
                "Purchase a local transit day-pass to save on transportation.",
                "Carry cash for smaller vendors and night markets.",
            ],
        }
