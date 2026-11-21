"""Small, testable command-line validation helpers."""

import math


def get_positive_float(prompt: str) -> float:
    """Repeatedly ask for a finite price above zero (Lab 9 section 5.1)."""
    while True:
        try:
            value = float(input(prompt))
            if not math.isfinite(value) or value <= 0:
                print("Please enter a number greater than zero.")
                continue
            return value
        except ValueError:
            print("Please enter a valid number, e.g. 12.50")
