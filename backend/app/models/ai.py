"""Pydantic schemas for AI-powered modules."""

from pydantic import BaseModel, Field


class AutoCategoryRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=4000)


class AutoCategoryResponse(BaseModel):
    primary_category: str
    sub_category: str
    seo_tags: list[str] = Field(..., min_length=1)
    sustainability_filters: list[str] = Field(..., min_length=1)


class B2BProposalRequest(BaseModel):
    budget: float = Field(..., gt=0)
    industry: str = Field(..., min_length=2, max_length=150)


class B2BProductItem(BaseModel):
    product_name: str = Field(..., min_length=2, max_length=200)
    quantity: int = Field(..., gt=0)
    unit_cost: float = Field(..., ge=0)
    total_cost: float = Field(..., ge=0)


class B2BBudgetBreakdown(BaseModel):
    total_allocated: float = Field(..., ge=0)
    remaining_budget: float = Field(..., ge=0)


class B2BProposalResponse(BaseModel):
    product_mix: list[B2BProductItem] = Field(..., min_length=1)
    budget_breakdown: B2BBudgetBreakdown
    impact_summary: str = Field(..., min_length=5)
