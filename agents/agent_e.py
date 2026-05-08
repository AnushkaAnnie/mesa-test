from github import Github
from backend.llm_client import call_llama
from backend.github_poster import post_general_comment
import os
from dotenv import load_dotenv

load_dotenv()

g = Github(os.getenv("GITHUB_TOKEN"))


def get_open_prs(repo_name: str, exclude_pr: int) -> list:
    repo = g.get_repo(repo_name)
    open_prs = []
    for pr in repo.get_pulls(state="open"):
        if pr.number != exclude_pr:
            files = [f.filename for f in pr.get_files()]
            open_prs.append({
                "number": pr.number,
                "author": pr.user.login,
                "files": files,
                "title": pr.title,
            })
    return open_prs


def run(repo_name: str, new_pr_number: int, new_pr_files: list, new_diff: str) -> dict:
    open_prs = get_open_prs(repo_name, new_pr_number)
    confirmed_conflicts = []

    for pr in open_prs:
        overlap = set(new_pr_files) & set(pr["files"])
        if not overlap:
            continue

        prompt = f"""Two PRs both modify these files: {list(overlap)}
New PR changes: {new_diff[:400]}
Other PR title: {pr['title']}
Are these logically incompatible? Answer YES or NO in one sentence."""

        answer = call_llama(prompt)
        if answer.upper().strip().startswith("YES"):
            confirmed_conflicts.append(pr)
            msg_new = (
                f"⚠️ **Inter-PR Conflict Detected**\n"
                f"This PR conflicts with **PR #{pr['number']}** by @{pr['author']}\n"
                f"**Overlapping files:** {', '.join(overlap)}\n"
                f"Please coordinate with @{pr['author']} before merging."
            )
            msg_other = (
                f"⚠️ **PR #{new_pr_number}** also modifies your files: "
                f"`{', '.join(overlap)}`. Please coordinate before merging."
            )
            post_general_comment(repo_name, new_pr_number, msg_new)
            post_general_comment(repo_name, pr["number"], msg_other)

    return {"conflicts_found": [p["number"] for p in confirmed_conflicts]}
