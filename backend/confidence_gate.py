import math

SEVERITY_PROBS = {"critical": 0.90, "high": 0.75, "medium": 0.55, "low": 0.35}
THRESHOLD = 0.70


def compute_score(severity: str, llm_certainty: float, recurrence_weight: float) -> float:
    log_prior = math.log(0.6 / 0.4)
    w1, w2, w3 = 0.5, 0.3, 0.2
    p_sev = SEVERITY_PROBS.get(severity.lower(), 0.55)

    def safe_log_odds(p):
        p = max(0.01, min(0.99, p))
        return math.log(p / (1 - p))

    log_sum = (
        log_prior
        + w1 * safe_log_odds(p_sev)
        + w2 * safe_log_odds(llm_certainty)
        + w3 * safe_log_odds(recurrence_weight)
    )
    return round(1 / (1 + math.exp(-log_sum)), 3)


def filter_comments(comments: list, recurrence_weight: float = 0.5):
    post_inline, send_to_human = [], []
    for item in comments:
        score = compute_score(
            item.get("severity", "medium"),
            item.get("llm_certainty", 0.65),
            recurrence_weight,
        )
        item["confidence_score"] = score
        (post_inline if score >= THRESHOLD else send_to_human).append(item)
    return post_inline, send_to_human


if __name__ == "__main__":
    test = [
        {"severity": "critical", "category": "security", "comment": "SQL injection risk", "llm_certainty": 0.9},
        {"severity": "low", "category": "code_smell", "comment": "Variable name is too short", "llm_certainty": 0.4},
    ]
    inline, human = filter_comments(test, 0.7)
    print("Inline:", inline)
    print("Human:", human)
