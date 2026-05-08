import jwt
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()


def get_jwt_token() -> str:
    with open("github_app.pem", "r") as f:
        private_key = f.read()
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + 600,
        "iss": os.getenv("GITHUB_APP_ID"),
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def get_installation_token(installation_id: int) -> str:
    token = get_jwt_token()
    response = requests.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
    )
    return response.json().get("token", "")
