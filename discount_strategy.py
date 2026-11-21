"""Interchangeable order discounts (Strategy pattern)."""

import math
from abc import ABC, abstractmethod


class DiscountStrategy(ABC):
    """Shared interface used by Order without knowing any concrete discount."""

    @abstractmethod
    def apply(self, total: float) -> float:
        """Return the order total after applying this discount."""
        raise NotImplementedError


class NoDiscount(DiscountStrategy):
    def apply(self, total: float) -> float:
        return total


class PercentageDiscount(DiscountStrategy):
    def __init__(self, percentage: float) -> None:
        if (
            not isinstance(percentage, (int, float))
            or isinstance(percentage, bool)
            or not math.isfinite(percentage)
            or not 0 <= percentage <= 100
        ):
            raise ValueError("Discount percentage must be between 0 and 100.")
        self.percentage: float = float(percentage)

    def apply(self, total: float) -> float:
        return total * (1 - self.percentage / 100)


class BulkDiscount(DiscountStrategy):
    def __init__(self, threshold: float, amount: float) -> None:
        for label, value in (("Threshold", threshold), ("Discount amount", amount)):
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError(f"{label} must be a non-negative finite number.")
        self.threshold: float = float(threshold)
        self.amount: float = float(amount)

    def apply(self, total: float) -> float:
        if total >= self.threshold:
            return max(0.0, total - self.amount)
        return total


class StudentDiscount(DiscountStrategy):
    """A new five-percent strategy; Order does not need to be modified."""

    def apply(self, total: float) -> float:
        return total * 0.95
