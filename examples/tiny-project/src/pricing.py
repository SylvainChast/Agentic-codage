"""Small example domain: totals in cents, tax rate in basis points."""
from decimal import Decimal, ROUND_HALF_UP


def total_minor(subtotal_minor: int, tax_basis_points: int) -> int:
    """Return a non-negative total, rounding half a cent upwards."""
    if type(subtotal_minor) is not int or type(tax_basis_points) is not int:
        raise TypeError("Amounts and rates must be integers")
    if subtotal_minor < 0 or not 0 <= tax_basis_points <= 10000:
        raise ValueError("Invalid subtotal or tax rate")
    total = Decimal(subtotal_minor) * (10000 + tax_basis_points) / 10000
    return int(total.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
