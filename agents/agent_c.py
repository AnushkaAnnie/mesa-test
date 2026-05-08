from storage.database import get_patterns, save_comment, init_db
from backend.llm_client import call_llama
import math


def compute_recurrence_weight(patterns: list) -> float:
    if not patterns:
        return 0.5
    total_hits = sum(count for _, count in patterns)
    return round(1 / (1 + math.exp(-(total_hits - 3) * 0.4)), 3)


def get_developer_profile(username: str) -> dict:
    patterns = get_patterns(username)
    if not patterns:
        return {
            "profile_summary": f"No history for {username}. Applying standard review.",
            "recurrence_weight": 0.5,
            "patterns": [],
        }
    pattern_list = ", ".join([f"{cat} (flagged {cnt} times)" for cat, cnt in patterns])
    prompt = f"""Summarize this developer's code review history in 2 sentences.
Developer: {username}
Repeated issues: {pattern_list}
Start with: 'Developer {username} frequently...'"""
    summary = call_llama(prompt)
    return {
        "profile_summary": summary,
        "recurrence_weight": compute_recurrence_weight(patterns),
        "patterns": patterns,
    }


def record_comments(username: str, repo: str, pr_number: int, comments: list):
    for item in comments:
        save_comment(
            username,
            repo,
            pr_number,
            item.get("category", "general"),
            item.get("comment", ""),
        )


def run(username: str, repo: str, pr_number: int) -> dict:
    return get_developer_profile(username)


if __name__ == "__main__":
    init_db()
    save_comment("aarush", "test-repo", 1, "security", "Missing validation")
    save_comment("aarush", "test-repo", 2, "security", "Injection risk")
    result = run("aarush", "test-repo", 3)
    print(result)
