from agents.agent_b import store_pr_in_memory, get_related_context, detect_contradiction


def test_store_and_retrieve():
    store_pr_in_memory(
        "test_pr_1",
        "Add auth check",
        "Added JWT validation",
        "Added auth middleware to all routes",
        "test-repo",
    )
    result = get_related_context("authentication middleware changes", "test-repo")
    assert len(result["related_prs"]) > 0
    print("✅ Test 1 passed: store and retrieve works")


def test_contradiction_detection():
    store_pr_in_memory(
        "test_pr_2",
        "Always async DB",
        "Policy: async queries only",
        "Changed all db.query() to await db.query()",
        "test-repo",
    )
    result = get_related_context("adding synchronous database call", "test-repo")
    contradiction = detect_contradiction("Using db.query() synchronously", result["context_text"])
    assert "YES" in contradiction.upper()
    print("✅ Test 2 passed: contradiction detection works")


def test_empty_store():
    result = get_related_context("completely unrelated xyz123abc", "empty-repo")
    print(f"✅ Test 3 passed: {result['context_text']}")


if __name__ == "__main__":
    test_store_and_retrieve()
    test_contradiction_detection()
    test_empty_store()
