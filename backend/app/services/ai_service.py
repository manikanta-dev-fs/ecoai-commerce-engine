"""AI service layer for Groq (OpenAI-compatible) integrations."""

from datetime import datetime, timezone
import json
from typing import Any

from openai import AsyncOpenAI

from app.config.database import get_database
from app.config.settings import get_settings
from app.utils.exceptions import AIServiceError, DatabaseError


class AIService:
    """Encapsulates all AI-provider interactions for the application."""

    ALLOWED_CATEGORIES = [
        "Personal Care",
        "Home & Kitchen",
        "Office Supplies",
        "Packaging",
        "Apparel",
        "Corporate Gifting",
    ]
    ALLOWED_SUSTAINABILITY_FILTERS = [
        "plastic-free",
        "compostable",
        "biodegradable",
        "recycled",
        "vegan",
        "organic",
        "low-carbon",
    ]

    def __init__(self) -> None:
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
        )
        self.groq_model = "llama3-70b-8192"

    async def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Generate structured JSON output only from the provider."""
        try:
            completion = await self.client.chat.completions.create(
                model=model or self.groq_model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            system_prompt
                            + " Always return valid JSON only. Do not include markdown or prose."
                        ),
                    },
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:
            raise AIServiceError(f"Provider request failed: {exc}") from exc

        content = completion.choices[0].message.content if completion.choices else None
        if not content:
            raise AIServiceError("Provider returned empty response")

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIServiceError("Provider returned non-JSON response") from exc

    @staticmethod
    def _build_auto_category_prompt(title: str, description: str) -> tuple[str, str]:
        # Keep all task constraints centralized in the service layer.
        system_prompt = (
            "You are an AI for sustainable commerce metadata generation. "
            "Return strictly valid JSON only. No explanations. No markdown. No extra text."
        )
        user_payload = {
            "task": "Generate category and tags for the product.",
            "title": title,
            "description": description,
            "allowed_primary_categories": AIService.ALLOWED_CATEGORIES,
            "allowed_sustainability_filters": AIService.ALLOWED_SUSTAINABILITY_FILTERS,
            "required_output_schema": {
                "primary_category": "string",
                "sub_category": "string",
                "seo_tags": ["string"],
                "sustainability_filters": ["string"],
            },
            "constraints": [
                "primary_category must be one of allowed_primary_categories",
                "sustainability_filters must contain only allowed_sustainability_filters values",
                "seo_tags and sustainability_filters must be non-empty arrays",
            ],
        }
        return system_prompt, json.dumps(user_payload)

    def _validate_auto_category_result(self, result: dict[str, Any]) -> dict[str, Any]:
        required_keys = {
            "primary_category",
            "sub_category",
            "seo_tags",
            "sustainability_filters",
        }
        missing_keys = required_keys - set(result.keys())
        if missing_keys:
            raise AIServiceError(f"Missing response fields: {sorted(missing_keys)}")

        primary_category = str(result["primary_category"]).strip()
        sub_category = str(result["sub_category"]).strip()
        seo_tags = result["seo_tags"]
        sustainability_filters = result["sustainability_filters"]

        if primary_category not in self.ALLOWED_CATEGORIES:
            raise AIServiceError("AI returned unsupported primary_category")
        if not sub_category:
            raise AIServiceError("AI returned empty sub_category")
        if not isinstance(seo_tags, list) or not seo_tags:
            raise AIServiceError("AI returned empty seo_tags")
        if not isinstance(sustainability_filters, list) or not sustainability_filters:
            raise AIServiceError("AI returned empty sustainability_filters")

        cleaned_tags = [str(tag).strip() for tag in seo_tags if str(tag).strip()]
        cleaned_filters = [str(item).strip() for item in sustainability_filters if str(item).strip()]

        if not cleaned_tags:
            raise AIServiceError("AI returned invalid seo_tags")
        if not cleaned_filters:
            raise AIServiceError("AI returned invalid sustainability_filters")

        invalid_filters = [
            item for item in cleaned_filters if item not in self.ALLOWED_SUSTAINABILITY_FILTERS
        ]
        if invalid_filters:
            raise AIServiceError(f"AI returned unsupported sustainability_filters: {invalid_filters}")

        return {
            "primary_category": primary_category,
            "sub_category": sub_category,
            "seo_tags": cleaned_tags,
            "sustainability_filters": cleaned_filters,
        }

    async def _insert_prompt_log(
        self,
        *,
        module: str,
        input_payload: dict[str, Any],
        prompt: str,
        raw_response: str,
    ) -> None:
        # Auditability: store exact prompt/response pair for prompt engineering and debugging.
        try:
            database = get_database()
            await database["prompt_logs"].insert_one(
                {
                    "module": module,
                    "input_payload": input_payload,
                    "prompt": prompt,
                    "raw_response": raw_response,
                    "timestamp": datetime.now(timezone.utc),
                }
            )
        except Exception as exc:
            raise DatabaseError(f"Failed to store prompt log: {exc}") from exc

    async def _insert_auto_category_result(
        self,
        *,
        title: str,
        description: str,
        result: dict[str, Any],
    ) -> None:
        # Domain record: persist validated metadata used by downstream catalog workflows.
        try:
            database = get_database()
            await database["auto_categories"].insert_one(
                {
                    "title": title,
                    "description": description,
                    "primary_category": result["primary_category"],
                    "sub_category": result["sub_category"],
                    "seo_tags": result["seo_tags"],
                    "sustainability_filters": result["sustainability_filters"],
                    "timestamp": datetime.now(timezone.utc),
                }
            )
        except Exception as exc:
            raise DatabaseError(f"Failed to store auto-category result: {exc}") from exc

    async def generate_auto_category(
        self,
        *,
        title: str,
        description: str,
    ) -> dict[str, Any]:
        """Generate and persist auto-category metadata for catalog automation."""
        system_prompt, user_prompt = self._build_auto_category_prompt(title=title, description=description)

        try:
            completion = await self.client.chat.completions.create(
                model=self.groq_model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:
            raise AIServiceError(f"Provider request failed: {exc}") from exc

        raw_content = completion.choices[0].message.content if completion.choices else None
        if not raw_content:
            raise AIServiceError("Provider returned empty response")

        await self._insert_prompt_log(
            module="auto_category",
            input_payload={"title": title, "description": description},
            prompt=user_prompt,
            raw_response=raw_content,
        )

        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError as exc:
            raise AIServiceError("Provider returned non-JSON response") from exc

        if not isinstance(parsed, dict):
            raise AIServiceError("Provider returned invalid JSON object")

        validated = self._validate_auto_category_result(parsed)
        await self._insert_auto_category_result(
            title=title,
            description=description,
            result=validated,
        )
        return validated

    async def generate_b2b_proposal(
        self,
        *,
        budget: float,
        industry: str,
    ) -> dict[str, Any]:
        """Generate and persist a budget-constrained B2B proposal."""
        system_prompt = (
            "You are an AI assistant for sustainable B2B commerce planning. "
            "Return strictly valid JSON only. No explanations. No markdown. No extra text."
        )
        prompt_payload = {
            "task": "Generate a sustainable B2B product proposal within budget.",
            "budget": budget,
            "industry": industry,
            "required_output_schema": {
                "product_mix": [
                    {
                        "product_name": "string",
                        "quantity": "integer",
                        "unit_cost": "float",
                        "total_cost": "float",
                    }
                ],
                "budget_breakdown": {
                    "total_allocated": "float",
                    "remaining_budget": "float",
                },
                "impact_summary": "string",
            },
            "rules": [
                "total_cost must equal quantity * unit_cost",
                "budget_breakdown.total_allocated must equal sum(product_mix.total_cost)",
                "budget_breakdown.total_allocated must be <= budget",
                "budget_breakdown.remaining_budget must equal budget - total_allocated",
            ],
        }
        user_prompt = json.dumps(prompt_payload)

        try:
            completion = await self.client.chat.completions.create(
                model=self.groq_model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:
            raise AIServiceError(f"Provider request failed: {exc}") from exc

        raw_content = completion.choices[0].message.content if completion.choices else None
        if not raw_content:
            raise AIServiceError("Provider returned empty response")

        await self._insert_prompt_log(
            module="b2b_proposal",
            input_payload={"budget": budget, "industry": industry},
            prompt=user_prompt,
            raw_response=raw_content,
        )

        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError as exc:
            raise AIServiceError("Provider returned non-JSON response") from exc

        if not isinstance(parsed, dict):
            raise AIServiceError("Provider returned invalid JSON object")

        validated = self._validate_b2b_proposal_result(parsed, budget)
        await self._insert_b2b_proposal_result(
            budget=budget,
            industry=industry,
            result=validated,
        )
        return validated

    @staticmethod
    def _to_money(value: Any) -> float:
        return round(float(value), 2)

    def _validate_b2b_proposal_result(self, result: dict[str, Any], budget: float) -> dict[str, Any]:
        required_keys = {"product_mix", "budget_breakdown", "impact_summary"}
        missing_keys = required_keys - set(result.keys())
        if missing_keys:
            raise AIServiceError(f"Missing response fields: {sorted(missing_keys)}")

        product_mix = result["product_mix"]
        budget_breakdown = result["budget_breakdown"]
        impact_summary = str(result["impact_summary"]).strip()

        if not isinstance(product_mix, list) or not product_mix:
            raise AIServiceError("AI returned empty product_mix")
        if not isinstance(budget_breakdown, dict):
            raise AIServiceError("AI returned invalid budget_breakdown")
        if not impact_summary:
            raise AIServiceError("AI returned empty impact_summary")

        validated_mix: list[dict[str, Any]] = []
        calculated_total_allocated = 0.0

        for item in product_mix:
            if not isinstance(item, dict):
                raise AIServiceError("AI returned invalid product item")

            for key in ("product_name", "quantity", "unit_cost", "total_cost"):
                if key not in item:
                    raise AIServiceError(f"Missing product field: {key}")

            product_name = str(item["product_name"]).strip()
            quantity = int(item["quantity"])
            unit_cost = self._to_money(item["unit_cost"])
            total_cost = self._to_money(item["total_cost"])

            if not product_name:
                raise AIServiceError("AI returned empty product_name")
            if quantity <= 0:
                raise AIServiceError("AI returned non-positive quantity")

            expected_total_cost = self._to_money(quantity * unit_cost)
            if abs(total_cost - expected_total_cost) > 0.01:
                raise AIServiceError("AI returned invalid total_cost math")

            calculated_total_allocated = self._to_money(calculated_total_allocated + total_cost)
            validated_mix.append(
                {
                    "product_name": product_name,
                    "quantity": quantity,
                    "unit_cost": unit_cost,
                    "total_cost": total_cost,
                }
            )

        for key in ("total_allocated", "remaining_budget"):
            if key not in budget_breakdown:
                raise AIServiceError(f"Missing budget_breakdown field: {key}")

        total_allocated = self._to_money(budget_breakdown["total_allocated"])
        remaining_budget = self._to_money(budget_breakdown["remaining_budget"])
        normalized_budget = self._to_money(budget)

        if abs(total_allocated - calculated_total_allocated) > 0.01:
            raise AIServiceError("AI returned inconsistent total_allocated")
        if total_allocated - normalized_budget > 0.01:
            raise AIServiceError("AI exceeded budget")

        expected_remaining = self._to_money(normalized_budget - total_allocated)
        if abs(remaining_budget - expected_remaining) > 0.01:
            raise AIServiceError("AI returned inconsistent remaining_budget")

        return {
            "product_mix": validated_mix,
            "budget_breakdown": {
                "total_allocated": total_allocated,
                "remaining_budget": remaining_budget,
            },
            "impact_summary": impact_summary,
        }

    async def _insert_b2b_proposal_result(
        self,
        *,
        budget: float,
        industry: str,
        result: dict[str, Any],
    ) -> None:
        try:
            database = get_database()
            await database["b2b_proposals"].insert_one(
                {
                    "original_budget": self._to_money(budget),
                    "original_industry": industry,
                    "product_mix": result["product_mix"],
                    "budget_breakdown": result["budget_breakdown"],
                    "impact_summary": result["impact_summary"],
                    "timestamp": datetime.now(timezone.utc),
                }
            )
        except Exception as exc:
            raise DatabaseError(f"Failed to store b2b proposal result: {exc}") from exc
