import requests


def call_llama(prompt: str) -> str:
    """Call the local Ollama LLaMA3 model."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": prompt, "stream": False},
            timeout=120
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return ""


if __name__ == "__main__":
    result = call_llama("Say hello in one sentence.")
    print(result)
