from prototype.retailers.kroger_mock import KrogerMockAdapter
from prototype.retailers.target_mock import TargetMockAdapter
from prototype.retailers.walmart_mock import WalmartMockAdapter

ALL_RETAILERS = ["walmart", "target", "kroger"]


def build_adapters():
    return {
        "walmart": WalmartMockAdapter(),
        "target": TargetMockAdapter(),
        "kroger": KrogerMockAdapter(),
    }

