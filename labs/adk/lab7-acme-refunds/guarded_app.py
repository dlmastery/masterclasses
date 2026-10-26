"""Step 6: register RefundGuardPlugin once on the App.

Run:  python guarded_app.py
Or:   adk web --extra_plugins=refund_guard.RefundGuardPlugin .
"""
import asyncio

from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from refund_guard import RefundGuardPlugin


def issue_refund(order_id: str, amount: float) -> dict:
    """Refund amount (USD) to the card on file for order_id."""
    return {"status": "ok", "refunded": amount}


M, T = "gemini-3.5-flash", [issue_refund]
partner = LlmAgent(name="partner_refunds", model=M, tools=T,
                   description="Partner orders.")
chargebacks = LlmAgent(name="chargebacks", model=M, tools=T,
                       description="Chargebacks.")
refunds = LlmAgent(name="refunds", model=M, tools=T,
    sub_agents=[partner, chargebacks],
    instruction="Partner-store orders: transfer to partner_refunds.")
app = App(name="refund_app", root_agent=refunds,
          plugins=[RefundGuardPlugin()])

ASKS = ["Refund $79 on A-100", "Partner-store order: refund $640 on A-200"]


async def main():
    async with InMemoryRunner(app=app) as runner:
        await runner.run_debug(ASKS, verbose=True)


if __name__ == "__main__":
    asyncio.run(main())
