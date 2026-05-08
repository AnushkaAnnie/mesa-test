from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

celery_app = Celery(
    "code_reviewer",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)

celery_app.conf.beat_schedule = {
    "weekly-drift-check": {
        "task": "backend.celery_app.run_drift_check",
        "schedule": crontab(hour=10, minute=0, day_of_week=1),
    }
}


@celery_app.task
def process_pr(payload: dict):
    repo_name = payload["repository"]["full_name"]
    pr_number = payload["pull_request"]["number"]
    pr_author = payload["pull_request"]["user"]["login"]
    pr_title = payload["pull_request"].get("title", "")
    pr_body = payload["pull_request"].get("body", "") or ""

    from agents.agent_a import run as run_a
    from agents.agent_b import run as run_b
    from agents.agent_c import run as run_c

    # Run C and B in parallel, then A (needs profile from C)
    with ThreadPoolExecutor() as ex:
        future_c = ex.submit(run_c, pr_author, repo_name, pr_number)
        future_b = ex.submit(run_b, f"pr_{pr_number}", pr_title, pr_body, "", repo_name)
        profile = future_c.result()
        future_a = ex.submit(run_a, repo_name, pr_number, pr_author, profile["profile_summary"])

    result_a = future_a.result()
    result_b = future_b.result()

    merged = {
        "diff_issues": result_a["diff_issues"],
        "diff_text": result_a["diff_text"],
        "changed_files": result_a["changed_files"],
        "rag_context": result_b["context_text"],
        "contradiction": result_b.get("contradiction", ""),
        "dev_profile": profile["profile_summary"],
        "recurrence_weight": profile["recurrence_weight"],
    }

    print(f"[Celery] Agents A/B/C complete for PR #{pr_number}")

    # LLM Layer: final enriched review
    from backend.llm_layer import generate_final_review
    final_comments = generate_final_review(merged)

    # Confidence Gate
    from backend.confidence_gate import filter_comments
    inline_comments, human_comments = filter_comments(final_comments, merged["recurrence_weight"])

    # Post to GitHub
    from backend.github_poster import post_review_comments, post_general_comment
    post_review_comments(repo_name, pr_number, inline_comments)

    if human_comments:
        alert = f"⚠️ **Human Review Needed** — {len(human_comments)} low-confidence finding(s):\n"
        for h in human_comments:
            alert += f"\n- `{h.get('file', '?')}:{h.get('line', '?')}` — {h.get('comment', '')[:100]}"
        post_general_comment(repo_name, pr_number, alert)

    # Record comments in DB for developer profile
    from agents.agent_c import record_comments
    record_comments(pr_author, repo_name, pr_number, final_comments)

    # Store this PR in vector memory
    from agents.agent_b import store_pr_in_memory
    store_pr_in_memory(
        f"{repo_name}_pr_{pr_number}",
        pr_title,
        pr_body,
        merged["diff_text"],
        repo_name,
    )

    # Inter-PR Conflict Detection
    from agents.agent_e import run as run_e
    run_e(repo_name, pr_number, merged["changed_files"], merged["diff_text"])

    print(f"[Celery] PR #{pr_number} review complete. {len(inline_comments)} inline, {len(human_comments)} to human.")
    return {"status": "complete", "pr": pr_number}


@celery_app.task
def run_drift_check():
    from agents.agent_d import run
    # Replace with your actual repo name or make dynamic
    repo = os.getenv("DEFAULT_REPO", "your-username/your-repo")
    result = run(repo)
    print("[Drift Check]", result)
    return result
