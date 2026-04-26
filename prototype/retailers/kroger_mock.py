import random
import time

from prototype.retailers.base import BaseRetailerAdapter


class KrogerMockAdapter(BaseRetailerAdapter):
    retailer_id = "kroger"
    _failure_rate = 0.30

    def search(self, query: str, zip_code: str) -> list[dict]:
        time.sleep(random.uniform(0.12, 0.22))
        if random.random() < self._failure_rate:
            raise RuntimeError("Kroger mock transient failure")
        base_price = {"milk": 3.59, "eggs": 4.89, "bread": 3.29}.get(query, 6.49)
        return [
            {
                "retailer_id": self.retailer_id,
                "store_id": f"kg-{zip_code}",
                "name": query.title(),
                "price": round(base_price, 2),
                "currency": "USD",
            }
        ]

