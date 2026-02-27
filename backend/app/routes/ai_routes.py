"""Routes for AI-powered commerce modules."""

from fastapi import APIRouter

from app.controllers.ai_controller import auto_category_controller, b2b_proposal_controller
from app.models.ai import (
    AutoCategoryRequest,
    AutoCategoryResponse,
    B2BProposalRequest,
    B2BProposalResponse,
)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/auto-category", response_model=AutoCategoryResponse)
async def generate_auto_category(payload: AutoCategoryRequest) -> AutoCategoryResponse:
    """Module 1: AI Auto Category & Tag Generator."""
    return await auto_category_controller(payload)


@router.post("/b2b-proposal", response_model=B2BProposalResponse)
async def generate_b2b_proposal(payload: B2BProposalRequest) -> B2BProposalResponse:
    """Module 2: AI B2B Proposal Generator with budget constraints."""
    return await b2b_proposal_controller(payload)
