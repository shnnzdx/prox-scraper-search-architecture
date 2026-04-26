import random
import time

from prototype.retailers.base import BaseRetailerAdapter


class TargetMockAdapter(BaseRetailerAdapter):
    retailer_id = "target"
    _failure_rate = 0.18

    def search(self, query: str, zip_code: str) -> list[dict]:
        time.sleep(random.uniform(0.08, 0.16))
        if random.random() < self._failure_rate:
            raise RuntimeError("Target mock transient failure")
        base_price = {"milk": 3.49, "eggs": 4.79, "bread": 3.09}.get(query, 6.29)
        return [
            {
                "retailer_id": self.retailer_id,
                "store_id": f"tg-{zip_code}",
                "name": query.title(),
                "price": round(base_price, 2),
                "currency": "USD",
            }
        ]

