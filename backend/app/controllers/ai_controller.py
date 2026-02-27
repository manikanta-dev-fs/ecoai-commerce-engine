"""Controller layer for AI module orchestration."""

from app.models.ai import (
    AutoCategoryRequest,
    AutoCategoryResponse,
    B2BProposalRequest,
    B2BProposalResponse,
)
from app.services.ai_service import AIService

ai_service = AIService()


async def auto_category_controller(payload: AutoCategoryRequest) -> AutoCategoryResponse:
    """Orchestrate auto-category generation request."""
    result = await ai_service.generate_auto_category(
        title=payload.title,
        description=payload.description,
    )
    return AutoCategoryResponse.model_validate(result)


async def b2b_proposal_controller(payload: B2BProposalRequest) -> B2BProposalResponse:
    """Orchestrate B2B proposal generation request."""
    result = await ai_service.generate_b2b_proposal(
        budget=payload.budget,
        industry=payload.industry,
    )
    return B2BProposalResponse.model_validate(result)
