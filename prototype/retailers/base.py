from abc import ABC, abstractmethod


class BaseRetailerAdapter(ABC):
    retailer_id: str

    @abstractmethod
    def search(self, query: str, zip_code: str) -> list[dict]:
        raise NotImplementedError

