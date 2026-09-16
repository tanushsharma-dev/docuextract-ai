from __future__ import annotations


def generate_invoice_records(count: int = 10) -> list[dict]:
    return [{
        "invoice_id": f"INV-{index:04d}",
        "vendor": "Vendor A",
        "total": 125.0 + index,
    } for index in range(1, count + 1)]


if __name__ == "__main__":
    records = generate_invoice_records()
    print(records)
