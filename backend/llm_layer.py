from backend.llm_client import call_llama
import json


def generate_final_review(merged: dict) -> list:
    prompt = f"""You are a senior software engineer doing a thorough code review.

DEVELOPER PROFILE:
{merged.get('dev_profile', 'No history available')}

PAST CODEBASE DECISIONS (watch for contradictions):
{merged.get('rag_context', 'None found')}

CONTRADICTION DETECTED:
{merged.get('contradiction', 'None')}

ISSUES ALREADY FOUND:
{json.dumps(merged.get('diff_issues', []), indent=2)[:2000]}

Generate your final review comment list. Return ONLY a JSON array, no extra text:
[{{"file":"path/file.py","line":1,"category":"security","severity":"high","comment":"Detailed explanation and suggested fix","llm_certainty":0.85}}]
Categories: security, logic_error, code_smell, bad_practice, architecture_concern
Severity: critical, high, medium, low"""

    response = call_llama(prompt)

    try:
        cleaned = response.strip()
        if "```" in cleaned:
            parts = cleaned.split("```")
            cleaned = parts[1] if len(parts) > 1 else cleaned
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        start = cleaned.find("[")
        end = cleaned.rfind("]") + 1
        if start >= 0 and end > start:
            cleaned = cleaned[start:end]
        return json.loads(cleaned)
    except Exception as e:
        print(f"[LLM Layer] JSON parse failed: {e}")
        return merged.get("diff_issues", [])
