from github import Github
import os
import json
from dotenv import load_dotenv
from backend.llm_client import call_llama

load_dotenv()

g = Github(os.getenv("GITHUB_TOKEN"))


def get_pr_diff(repo_name: str, pr_number: int) -> str:
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    diff_text = ""
    for file in pr.get_files():
        if file.patch:
            diff_text += f"\nFile: {file.filename}\n{file.patch}\n"
    return diff_text


def get_changed_files(repo_name: str, pr_number: int) -> list:
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    return [f.filename for f in pr.get_files()]


def analyze_diff(diff_text: str, developer: str, dev_profile: str = "") -> list:
    prompt = f"""You are a senior code reviewer.
Developer: {developer}
{f"Developer history: {dev_profile}" if dev_profile else ""}

Code changes:
{diff_text[:3000]}

Find all issues. Return ONLY a JSON array, no extra text:
[{{"file":"path/file.py","line":1,"category":"security","severity":"high","comment":"Detailed explanation","llm_certainty":0.85}}]
Categories: security, logic_error, code_smell, bad_practice, architecture_concern
Severity: critical, high, medium, low"""

    response = call_llama(prompt)
    try:
        cleaned = response.strip()
        if "```" in cleaned:
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        start = cleaned.find("[")
        end = cleaned.rfind("]") + 1
        if start >= 0 and end > start:
            cleaned = cleaned[start:end]
        return json.loads(cleaned)
    except Exception as e:
        print(f"[Agent A] JSON parse error: {e}")
        return []


def run(repo_name: str, pr_number: int, developer: str, dev_profile: str = "") -> dict:
    diff = get_pr_diff(repo_name, pr_number)
    files = get_changed_files(repo_name, pr_number)
    issues = analyze_diff(diff, developer, dev_profile)
    return {"diff_issues": issues, "diff_text": diff, "changed_files": files}
