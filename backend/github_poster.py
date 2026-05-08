from github import Github
import os
from dotenv import load_dotenv

load_dotenv()

g = Github(os.getenv("GITHUB_TOKEN"))


def post_review_comments(repo_name: str, pr_number: int, comments: list):
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    if not comments:
        pr.create_issue_comment("✅ **Code Reviewer:** No major issues found. Good work!")
        return

    for item in comments:
        text = (
            f"**🤖 Code Reviewer**\n"
            f"**Severity:** {item.get('severity', 'medium').upper()} | "
            f"**Category:** {item.get('category', 'general')} | "
            f"**Confidence:** {item.get('confidence_score', 0.0):.2f}\n\n"
            f"{item.get('comment', '')}\n\n"
            f"*Reply to this comment if you disagree and I will respond.*"
        )
        try:
            commit = list(pr.get_commits())[-1]
            pr.create_review_comment(
                body=text,
                commit=commit,
                path=item.get("file", ""),
                line=item.get("line", 1),
            )
        except Exception:
            pr.create_issue_comment(
                f"**File:** `{item.get('file')}` | **Line:** {item.get('line')}\n\n{text}"
            )


def post_general_comment(repo_name: str, pr_number: int, message: str):
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment(message)
