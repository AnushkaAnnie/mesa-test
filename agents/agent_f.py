from github import Github
from backend.llm_client import call_llama
from backend.github_poster import post_general_comment
import os
from dotenv import load_dotenv

load_dotenv()

g = Github(os.getenv("GITHUB_TOKEN"))


def get_last_bot_comment(repo_name: str, pr_number: int) -> str:
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    for comment in reversed(list(pr.get_issue_comments())):
        if "Code Reviewer" in comment.body:
            return comment.body
    return "Original AI comment not found."


def run(repo_name: str, pr_number: int, dev_reply: str, commenter: str) -> dict:
    bot_name = os.getenv("BOT_NAME", "")
    if commenter == bot_name:
        return {"decision": "ignored"}

    original = get_last_bot_comment(repo_name, pr_number)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    diff = "".join(f.patch[:200] for f in pr.get_files() if f.patch)

    prompt = f"""You are a code reviewer in a debate.
Your original comment: {original[:500]}
Developer's reply: {dev_reply}
Relevant code: {diff[:400]}

Start your response with EXACTLY one word: CONCEDE, MAINTAIN, or ESCALATE.
Then explain your reasoning in 2 sentences.
- CONCEDE if the developer makes a valid point and you were wrong
- MAINTAIN if your original concern stands
- ESCALATE if this is a critical issue that must be fixed before merge"""

    response = call_llama(prompt)
    decision = "MAINTAIN"
    if response.upper().startswith("CONCEDE"):
        decision = "CONCEDE"
    elif response.upper().startswith("ESCALATE"):
        decision = "ESCALATE"

    reply = f"**🤖 Code Reviewer — {decision}**\n\n{response}"
    post_general_comment(repo_name, pr_number, reply)
    return {"decision": decision, "response": response}
