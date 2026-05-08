from github import Github
from storage.database import DB_PATH
from backend.llm_client import call_llama
import sqlite3
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

g = Github(os.getenv("GITHUB_TOKEN"))


def get_repo_structure(repo_name: str) -> str:
    repo = g.get_repo(repo_name)
    files = []
    try:
        contents = list(repo.get_contents(""))
        while contents:
            item = contents.pop(0)
            if item.type == "dir":
                contents.extend(repo.get_contents(item.path))
            else:
                files.append(item.path)
    except Exception as e:
        return f"Error fetching structure: {e}"
    return "\n".join(files[:100])


def get_baseline(repo: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT snapshot FROM architecture_snapshots WHERE repo=? ORDER BY created_at ASC LIMIT 1",
        (repo,),
    )
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def save_snapshot(repo: str, snapshot: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO architecture_snapshots VALUES (NULL,?,?,?)",
        (repo, snapshot, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def run(repo_name: str) -> dict:
    current = get_repo_structure(repo_name)
    baseline = get_baseline(repo_name)

    if not baseline:
        save_snapshot(repo_name, current)
        return {"drift_detected": False, "details": "Baseline saved. First run complete."}

    prompt = f"""Compare two repository structures and identify architectural drift.

BASELINE:
{baseline[:1500]}

CURRENT:
{current[:1500]}

Start with 'DRIFT DETECTED:' or 'No significant drift detected.' Then explain in 2 sentences."""

    analysis = call_llama(prompt)
    drift = "DRIFT DETECTED" in analysis.upper()
    save_snapshot(repo_name, current)
    return {"drift_detected": drift, "details": analysis}


if __name__ == "__main__":
    import sys
    repo = sys.argv[1] if len(sys.argv) > 1 else os.getenv("DEFAULT_REPO", "your-username/test-repo")
    result = run(repo)
    print(result)
