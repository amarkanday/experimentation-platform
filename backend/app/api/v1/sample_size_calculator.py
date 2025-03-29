"""
Sample size calculator endpoint.

This module provides an endpoint for calculating the required sample size
for experiments based on expected effect size, baseline conversion rate,
and desired statistical power.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional
import math

from backend.app.api import deps
from backend.app.models.user import User

# Create router
router = APIRouter(prefix="/utils")


class SampleSizeRequest(BaseModel):
    """Schema for sample size calculation request."""

    baseline_rate: float = Field(
        ..., ge=0, le=1, description="Baseline conversion rate (0-1)"
    )
    minimum_detectable_effect: float = Field(
        ...,
        gt=0,
        description="Minimum detectable effect (relative change, e.g. 0.1 for 10%)",
    )
    statistical_power: float = Field(
        0.8, ge=0.5, le=0.99, description="Statistical power (0.5-0.99)"
    )
    significance_level: float = Field(
        0.05, ge=0.01, le=0.1, description="Significance level (0.01-0.1)"
    )
    is_one_sided: bool = Field(
        False, description="Whether the test is one-sided (default: two-sided)"
    )

    @validator("baseline_rate")
    def validate_baseline_rate(cls, v):
        """Validate baseline conversion rate."""
        if v <= 0 or v >= 1:
            raise ValueError("Baseline rate must be between 0 and 1")
        return v

    @validator("minimum_detectable_effect")
    def validate_minimum_detectable_effect(cls, v):
        """Validate minimum detectable effect."""
        if v <= 0:
            raise ValueError("Minimum detectable effect must be greater than 0")
        return v

    class Config:
        """Pydantic model configuration."""

        schema_extra = {
            "example": {
                "baseline_rate": 0.1,
                "minimum_detectable_effect": 0.15,
                "statistical_power": 0.8,
                "significance_level": 0.05,
                "is_one_sided": False,
            }
        }


class SampleSizeResponse(BaseModel):
    """Schema for sample size calculation response."""

    baseline_rate: float
    minimum_detectable_effect: float
    statistical_power: float
    significance_level: float
    is_one_sided: bool
    samples_per_variant: int
    total_samples: int
    estimated_duration_days: Optional[Dict[str, int]] = None
    notes: Optional[str] = None


@router.post(
    "/sample-size",
    response_model=SampleSizeResponse,
    summary="Calculate required sample size",
    response_description="Returns the required sample size for an experiment",
)
async def calculate_sample_size(
    request: SampleSizeRequest = Body(
        ..., description="Sample size calculation parameters"
    ),
    daily_traffic: Optional[int] = Query(
        None, gt=0, description="Daily traffic to the experiment (optional)"
    ),
    traffic_allocation: Optional[float] = Query(
        None,
        gt=0,
        le=1,
        description="Fraction of traffic allocated to the experiment (0-1)",
    ),
    variant_count: int = Query(
        2, ge=2, description="Number of variants (including control)"
    ),
    current_user: User = Depends(deps.get_current_active_user),
) -> SampleSizeResponse:
    """
    Calculate the required sample size for an experiment.

    This endpoint calculates the number of samples needed per variant and in total
    to achieve the desired statistical power for detecting the minimum effect size.

    Optionally, if daily traffic and traffic allocation are provided, it also
    estimates how long the experiment will need to run to collect the required sample.

    Returns:
        SampleSizeResponse: Sample size calculation results
    """
    # Extract parameters from request
    baseline_rate = request.baseline_rate
    mde = request.minimum_detectable_effect
    power = request.statistical_power
    alpha = request.significance_level
    is_one_sided = request.is_one_sided

    # Calculate sample size using power analysis
    # Get z-scores for alpha and beta
    if is_one_sided:
        z_alpha = abs(stats_z_score(alpha))
    else:
        z_alpha = abs(stats_z_score(alpha / 2))  # Two-sided test

    z_beta = abs(stats_z_score(1 - power))

    # Calculate expected rate for treatment
    treatment_rate = baseline_rate * (1 + mde)

    # Calculate pooled standard error
    pooled_variance = baseline_rate * (1 - baseline_rate) + treatment_rate * (
        1 - treatment_rate
    )

    # Calculate required sample size per variant
    numerator = (z_alpha + z_beta) ** 2 * pooled_variance
    denominator = (treatment_rate - baseline_rate) ** 2

    samples_per_variant = math.ceil(numerator / denominator)

    # Calculate total sample size
    total_samples = samples_per_variant * variant_count

    # Calculate estimated duration if daily traffic and allocation are provided
    estimated_duration_days = None
    notes = None

    if daily_traffic is not None and traffic_allocation is not None:
        if traffic_allocation <= 0 or traffic_allocation > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Traffic allocation must be between 0 and 1",
            )

        # Calculate daily experiment traffic
        daily_experiment_traffic = daily_traffic * traffic_allocation

        # Calculate daily traffic per variant
        daily_variant_traffic = daily_experiment_traffic / variant_count

        # Calculate days needed
        days_needed = math.ceil(samples_per_variant / daily_variant_traffic)

        # Add estimates for different time periods
        estimated_duration_days = {
            "days": days_needed,
            "weeks": math.ceil(days_needed / 7),
            "months": math.ceil(days_needed / 30),
        }

        # Add notes for very long or very short experiments
        if days_needed < 7:
            notes = "This experiment is very short. Consider implementing proper guardrails to avoid data quality issues."
        elif days_needed > 90:
            notes = "This experiment will take a long time to complete. Consider increasing traffic allocation, reducing the number of variants, or adjusting the minimum detectable effect."

    # Return response
    return SampleSizeResponse(
        baseline_rate=baseline_rate,
        minimum_detectable_effect=mde,
        statistical_power=power,
        significance_level=alpha,
        is_one_sided=is_one_sided,
        samples_per_variant=samples_per_variant,
        total_samples=total_samples,
        estimated_duration_days=estimated_duration_days,
        notes=notes,
    )


def stats_z_score(p: float) -> float:
    """
    Calculate the z-score for a given probability.

    This is an approximation of the inverse of the standard normal CDF.

    Args:
        p: Probability (0-1)

    Returns:
        float: Corresponding z-score
    """
    # Constants for the approximation
    a1 = -39.6968302866538
    a2 = 220.946098424521
    a3 = -275.928510446969
    a4 = 138.357751867269
    a5 = -30.6647980661472
    a6 = 2.50662827745924

    b1 = -54.4760987982241
    b2 = 161.585836858041
    b3 = -155.698979859887
    b4 = 66.8013118877197
    b5 = -13.2806815528857

    c1 = -0.00778489400243029
    c2 = -0.322396458041136
    c3 = -2.40075827716184
    c4 = -2.54973253934373
    c5 = 4.37466414146497
    c6 = 2.93816398269878

    d1 = 0.00778469570904146
    d2 = 0.32246712907004
    d3 = 2.445134137143
    d4 = 3.75440866190742

    # Determine which approximation to use based on p
    if p <= 0 or p >= 1:
        raise ValueError("Probability must be between 0 and 1")

    if p < 0.02425:
        # Lower region
        q = math.sqrt(-2 * math.log(p))
        z = (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) / (
            (((d1 * q + d2) * q + d3) * q + d4) * q + 1
        )
    elif p < 0.97575:
        # Central region
        q = p - 0.5
        r = q * q
        z = (
            (((((a1 * r + a2) * r + a3) * r + a4) * r + a5) * r + a6)
            * q
            / (((((b1 * r + b2) * r + b3) * r + b4) * r + b5) * r + 1)
        )
    else:
        # Upper region
        q = math.sqrt(-2 * math.log(1 - p))
        z = -(((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) / (
            (((d1 * q + d2) * q + d3) * q + d4) * q + 1
        )

    return z
