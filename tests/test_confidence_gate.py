from backend.confidence_gate import compute_score, filter_comments


def test_compute_score():
    score_high = compute_score("critical", 0.9, 0.8)
    score_low = compute_score("low", 0.3, 0.2)
    assert score_high > 0.7, f"Expected high score > 0.7, got {score_high}"
    assert score_low < 0.7, f"Expected low score < 0.7, got {score_low}"
    print(f"✅ Test 1 passed: high={score_high}, low={score_low}")


def test_filter_comments():
    comments = [
        {"severity": "critical", "category": "security", "comment": "SQL injection", "llm_certainty": 0.9},
        {"severity": "low", "category": "code_smell", "comment": "Short var name", "llm_certainty": 0.3},
        {"severity": "high", "category": "logic_error", "comment": "Off-by-one error", "llm_certainty": 0.8},
    ]
    inline, human = filter_comments(comments, 0.7)
    assert len(inline) >= 1, "Expected at least 1 inline comment"
    assert len(human) >= 1, "Expected at least 1 human comment"
    print(f"✅ Test 2 passed: {len(inline)} inline, {len(human)} to human")


if __name__ == "__main__":
    test_compute_score()
    test_filter_comments()
