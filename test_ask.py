"""
Quick manual test for /ask. Pure stdlib so it runs the same way on
Windows, Mac, or Linux -- no shell-quoting issues.
"""
import json
import urllib.request

BASE_URL = "http://localhost:5000"


def ask(prompt: str):
    data = json.dumps({"prompt": prompt}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/ask",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    print(f"prompt: {prompt!r}")
    print(f"  model_used: {result.get('model_used')}")
    print(f"  response:   {result.get('response')[:200]}")
    print()


if __name__ == "__main__":
    ask("What is the capital of Pune?")
    ask("Compare the tradeoffs between SQL and NoSQL databases in detail, step by step.")
    print("Check http://localhost:5000/dashboard to see both calls logged.")
