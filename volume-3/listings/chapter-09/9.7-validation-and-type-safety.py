# Applied AI Engineering, Volume III, Chapter 9
# Section 9.7, Validation and Type Safety
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from pydantic import BaseModel, Field, ValidationError, field_validator
import json

class SearchProductsArgs(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    sort_by: str = Field(default="popularity")

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        allowed = {"popularity", "price_asc", "price_desc"}
        if v not in allowed:
            raise ValueError(f"sort_by must be one of {allowed}, got '{v}'")
        return v

class GetInventoryArgs(BaseModel):
    product_id: str = Field(..., pattern=r"^[A-Z]{2,8}-\d{3,6}$")

class CalculateRevenueArgs(BaseModel):
    unit_price: float = Field(..., gt=0, description="Must be positive")
    quantity: int = Field(..., ge=1, le=100_000)
    discount_pct: float = Field(default=0.0, ge=0.0, le=100.0)

ARGUMENT_MODELS = {
    "search_products":   SearchProductsArgs,
    "get_inventory":     GetInventoryArgs,
    "calculate_revenue": CalculateRevenueArgs,
}

def validate_and_dispatch(tool_name: str, raw_args: str) -> dict:
    """Parse, validate, and dispatch a tool call."""
    try:
        args_dict = json.loads(raw_args)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON arguments: {e}"}

    model_cls = ARGUMENT_MODELS.get(tool_name)
    if model_cls is None:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        validated = model_cls(**args_dict)
    except ValidationError as e:
        return {"error": f"Argument validation failed: {e}"}

    func = TOOL_REGISTRY.get(tool_name)
    if func is None:
        return {"error": f"No implementation for tool: {tool_name}"}

    try:
        return func(**validated.model_dump())
    except Exception as e:
        return {"error": f"Execution error: {type(e).__name__}: {e}"}
