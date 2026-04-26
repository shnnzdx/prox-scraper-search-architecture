import json
from urllib.error import URLError
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:8000"


def call(method: str, path: str, payload: dict | None = None) -> dict:
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    with urlopen(req) as resp:  # nosec B310
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    try:
        print("1) Search milk/90210")
        print(json.dumps(call("POST", "/search", {"query": "milk", "zip_code": "90210"}), indent=2))

        print("\n2) Repeat same search (cache hit or dedupe suppression)")
        print(json.dumps(call("POST", "/search", {"query": "milk", "zip_code": "90210"}), indent=2))

        print("\n3) Run worker once")
        print(json.dumps(call("POST", "/worker/run-once"), indent=2))

<<<<<<< HEAD
        print("\n4) List jobs")
        print(json.dumps(call("GET", "/jobs"), indent=2))

        print("\n5) Show failed jobs")
=======
        print("\n4) Search milk/90210 again after worker refresh")
        print(json.dumps(call("POST", "/search", {"query": "milk", "zip_code": "90210"}), indent=2))

        print("\n5) List jobs")
        print(json.dumps(call("GET", "/jobs"), indent=2))

        print("\n6) Show failed jobs")
>>>>>>> 475eb6b (Initial Track A prototype submission)
        print(json.dumps(call("GET", "/failed-jobs"), indent=2))
    except URLError:
        print("API is not reachable. Start server first:")
        print("uvicorn prototype.app:app --reload")


if __name__ == "__main__":
    main()
<<<<<<< HEAD

=======
>>>>>>> 475eb6b (Initial Track A prototype submission)
