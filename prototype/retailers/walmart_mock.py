import random
import time

from prototype.retailers.base import BaseRetailerAdapter


class WalmartMockAdapter(BaseRetailerAdapter):
    retailer_id = "walmart"
    _failure_rate = 0.08

    def search(self, query: str, zip_code: str) -> list[dict]:
        time.sleep(random.uniform(0.03, 0.08))
        if random.random() < self._failure_rate:
            raise RuntimeError("Walmart mock transient failure")
        base_price = {"milk": 3.29, "eggs": 4.49, "bread": 2.99}.get(query, 5.99)
        return [
            {
                "retailer_id": self.retailer_id,
                "store_id": f"wm-{zip_code}",
                "name": query.title(),
                "price": round(base_price, 2),
                "currency": "USD",
            }
        ]

