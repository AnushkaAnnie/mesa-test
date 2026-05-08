from storage.vector_store import save_pr, search_similar
from backend.llm_client import call_llama


def store_pr_in_memory(pr_id: str, pr_title: str, pr_body: str, diff_summary: str, repo: str):
    text = f"Title: {pr_title}\nDescription: {pr_body}\nChanges: {diff_summary[:1000]}"
    save_pr(pr_id, text, metadata={"repo": repo, "pr_id": pr_id})
    print(f"[Agent B] PR {pr_id} stored in memory")


def get_related_context(diff_text: str, repo: str) -> dict:
    results = search_similar(diff_text[:500], n=3)
    if results["documents"] and results["documents"][0]:
        related = results["documents"][0]
        return {"related_prs": related, "context_text": "\n\n".join(related)}
    return {"related_prs": [], "context_text": "No related past PRs found."}


def detect_contradiction(diff_text: str, past_context: str) -> str:
    if not past_context or past_context == "No related past PRs found.":
        return ""
    prompt = f"""Past team decisions:
{past_context[:1000]}

New code change:
{diff_text[:1000]}

Does the new change contradict any past decision? Answer in one sentence starting with YES or NO."""
    return call_llama(prompt)


def run(pr_id: str, pr_title: str, pr_body: str, diff_text: str, repo: str) -> dict:
    store_pr_in_memory(pr_id, pr_title, pr_body, diff_text, repo)
    context = get_related_context(diff_text, repo)
    contradiction = detect_contradiction(diff_text, context["context_text"])
    context["contradiction"] = contradiction
    return context


if __name__ == "__main__":
    store_pr_in_memory("pr_1", "Add async DB calls", "Replaced all sync calls", "Changed db.query() to await db.query()", "test-repo")
    result = run("pr_2", "Add sync DB call", "Added sync query", "Used db.query() synchronously", "test-repo")
    print(result)
