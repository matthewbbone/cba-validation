from __future__ import annotations

from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Duration(StrictBaseModel):
    hours: float | None = Field(default=None)
    days: float | None = Field(default=None)
    weeks: float | None = Field(default=None)
    months: float | None = Field(default=None)
    years: float | None = Field(default=None)

    @model_validator(mode="after")
    def validate_some_duration(self) -> Self:
        if all(
            value is None
            for value in (self.hours, self.days, self.weeks, self.months, self.years)
        ):
            raise ValueError("at least one duration field must be provided")
        return self


class MoneyAmount(StrictBaseModel):
    amount: float = Field(description="The monetary amount.")


class PercentAmount(StrictBaseModel):
    value: float = Field(
        description="The percentage as a decimal, for example 0.05 for 5%."
    )


class QuantitativeValue(StrictBaseModel):
    money: MoneyAmount | None = Field(default=None)
    percent: PercentAmount | None = Field(default=None)
    duration: Duration | None = Field(default=None)
    number: float | None = Field(default=None)
    multiplier: float | None = Field(
        default=None,
        description="Pay multiplier, for example 1.5 for time-and-a-half.",
    )
    included: bool | None = Field(
        default=None,
        description="Whether a benefit, coverage item, or right is included.",
    )
    employer_paid: bool | None = Field(default=None)
    employee_paid: bool | None = Field(default=None)

    @model_validator(mode="after")
    def validate_some_value(self) -> Self:
        if (
            self.money is None
            and self.percent is None
            and self.duration is None
            and self.number is None
            and self.multiplier is None
            and self.included is None
            and self.employer_paid is None
            and self.employee_paid is None
        ):
            raise ValueError("at least one quantitative value field must be provided")
        return self


class BaseProvisionExtraction(StrictBaseModel):
    detail_fields: ClassVar[tuple[str, ...]] = ()
    requires_detail_when_exists: ClassVar[bool] = True

    concept_id: ClassVar[str] = ""
    category: ClassVar[str] = ""

    summarize: str = Field(
        description=(
            "Natural-language summary of the provision. This is the only free-text "
            "field in the extraction."
        )
    )
    exists: bool = Field(
        description="Whether this provision exists in the CBA.",
    )

    def has_normalized_detail(self) -> bool:
        for field_name in self.detail_fields:
            value = getattr(self, field_name)
            if value is None:
                continue
            if isinstance(value, list | dict | tuple | set) and len(value) == 0:
                continue
            return True
        return False

    @model_validator(mode="after")
    def validate_presence_consistency(self) -> Self:
        has_detail = self.has_normalized_detail()

        if not self.exists:
            populated = [
                field_name
                for field_name in self.detail_fields
                if getattr(self, field_name) not in (None, [], {}, (), set())
            ]
            if populated:
                raise ValueError(
                    "absent provisions cannot include normalized details: "
                    + ", ".join(populated)
                )
            return self

        if self.requires_detail_when_exists and not has_detail:
            raise ValueError("existing provisions require at least one normalized detail")
        return self
