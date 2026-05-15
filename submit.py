import json
import hmac
import hashlib
import os
from datetime import datetime, timezone

import requests


SIGNING_SECRET = os.environ.get(
    "B12_SIGNING_SECRET",
    "hello-there-from-b12"
)

SUBMISSION_URL = "https://b12.io/apply/submission"


def generate_payload():
    github_repo = os.environ["GITHUB_REPOSITORY"]
    run_id = os.environ["GITHUB_RUN_ID"]

    return {
        "action_run_link": (
            f"https://github.com/{github_repo}"
            f"/actions/runs/{run_id}"
        ),
        "email": os.environ["APPLICANT_EMAIL"],
        "name": os.environ["APPLICANT_NAME"],
        "repository_link": (
            f"https://github.com/{github_repo}"
        ),
        "resume_link": os.environ["RESUME_LINK"],
        "timestamp": (
            datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )
    }


def canonical_json(payload):
    return json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=False
    )


def create_signature(body):
    digest = hmac.new(
        SIGNING_SECRET.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return f"sha256={digest}"


def main():
    payload = generate_payload()

    compact_body = canonical_json(payload)

    signature = create_signature(compact_body)

    headers = {
        "Content-Type": "application/json",
        "X-Signature-256": signature,
    }

    response = requests.post(
        SUBMISSION_URL,
        data=compact_body.encode("utf-8"),
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    result = response.json()

    receipt = result.get("receipt")

    print(f"Submission successful.")
    print(f"Receipt: {receipt}")


if __name__ == "__main__":
    main()