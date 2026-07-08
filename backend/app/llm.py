"""Grounded investigation summary generation via the Claude API.

The prompt includes the flagged transaction's features and the retrieved
similar cases, with an explicit instruction to cite case IDs and to say
when the evidence is inconclusive rather than guessing.
"""

import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8")

SYSTEM_PROMPT = (
    "You are a fraud investigation assistant. You are given a flagged transaction "
    "and a set of similar historical cases retrieved from the case database. "
    "Write a concise investigation summary explaining why this transaction may be "
    "fraudulent, grounded only in the provided transaction features and cases. "
    "Cite the case IDs you relied on using the form [case: <id>]. "
    "If the evidence is inconclusive, say so explicitly rather than guessing."
)


def build_prompt(transaction: dict, cases: list[dict], question: str | None) -> str:
    lines = [
        "Flagged transaction:",
        f"- id: {transaction['id']}",
        f"- account_id: {transaction['account_id']}",
        f"- amount: {transaction['amount']}",
        f"- timestamp: {transaction['timestamp']}",
        f"- fraud_score: {transaction['fraud_score']}",
        f"- top contributing features: {transaction['top_shap_features']}",
        "",
        "Similar historical cases (most relevant first):",
    ]
    for case in cases:
        lines.append(
            f"- [case: {case['case_id']}] outcome={case['outcome']}, "
            f"relevance={case['relevance_score']}: {case['content']}"
        )
    if question:
        lines.append("")
        lines.append(f"Analyst question: {question}")
    return "\n".join(lines)


def generate_investigation_summary(
    transaction: dict, cases: list[dict], question: str | None
) -> str:
    prompt = build_prompt(transaction, cases, question)
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")
