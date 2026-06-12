from __future__ import annotations

from typing import ClassVar, Self

from pydantic import Field, model_validator

from .common import BaseProvisionExtraction, QuantitativeValue, StrictBaseModel


class BooleanFlagModel(StrictBaseModel):
    @model_validator(mode="after")
    def validate_some_indicator(self) -> Self:
        if all(value is None for value in self.model_dump().values()):
            raise ValueError("at least one boolean indicator must be provided")
        return self


class ComplexProvisionExtraction(BaseProvisionExtraction):
    detail_fields: ClassVar[tuple[str, ...]] = ("values",)

    values: list[QuantitativeValue] = Field(
        default_factory=list,
        description="Quantitative extracted values such as wages, rates, durations, counts, or percentages.",
    )


class BinaryProvisionExtraction(BaseProvisionExtraction):
    requires_detail_when_exists: ClassVar[bool] = False


class QuantitativeProvisionExtraction(BaseProvisionExtraction):
    detail_fields: ClassVar[tuple[str, ...]] = ("value",)

    value: QuantitativeValue | None = Field(
        default=None,
        description=(
            "The single normalized value for this provision. Use None when "
            "the provision does not exist."
        ),
    )

    @model_validator(mode="after")
    def validate_quantitative_value(self) -> Self:
        if self.exists and self.value is None:
            raise ValueError("existing quantitative provisions require value")
        if not self.exists and self.value is not None:
            raise ValueError("nonexistent quantitative provisions must have value=None")
        return self


class MonetaryBenefitExtraction(ComplexProvisionExtraction):
    pass


class ContributionExtraction(ComplexProvisionExtraction):
    pass


class WageScaleExtraction(ComplexProvisionExtraction):
    pass


class WageAdjustmentExtraction(ComplexProvisionExtraction):
    pass


class PremiumPayExtraction(ComplexProvisionExtraction):
    pass


class LeaveEntitlementExtraction(ComplexProvisionExtraction):
    pass


class HealthBenefitExtraction(ComplexProvisionExtraction):
    pass


class ProcedureOrStandardExtraction(ComplexProvisionExtraction):
    pass


class RecognitionExtraction(ComplexProvisionExtraction):
    pass


class JobSecurityExtraction(ComplexProvisionExtraction):
    pass


class SchedulingExtraction(ComplexProvisionExtraction):
    pass


class SafetyExtraction(ComplexProvisionExtraction):
    pass


class AncillaryBenefitExtraction(ComplexProvisionExtraction):
    pass
