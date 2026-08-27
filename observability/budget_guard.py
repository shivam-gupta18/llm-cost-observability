import os

from observability.storage import get_total_cost

BUDGET_CAP_USD = float(os.environ.get("BUDGET_CAP_USD", "1.00"))


class BudgetExceeded(Exception):
    pass


def check_budget():
    total = get_total_cost()
    if total >= BUDGET_CAP_USD:
        raise BudgetExceeded(
            f"Simulated spend (${total:.4f}) has reached the cap "
            f"(${BUDGET_CAP_USD:.2f}). Raise BUDGET_CAP_USD to continue."
        )
