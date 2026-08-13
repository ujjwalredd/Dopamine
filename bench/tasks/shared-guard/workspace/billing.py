def compute_total(cents: int, discount_pct: int) -> int:
    return cents * (100 - discount_pct) // 100


def checkout_api(cents: int, discount_pct: int) -> int:
    if discount_pct < 0:
        raise ValueError("discount must not be negative")
    return compute_total(cents, discount_pct)


def invoice_job(cents: int, discount_pct: int) -> int:
    return compute_total(cents, discount_pct)
