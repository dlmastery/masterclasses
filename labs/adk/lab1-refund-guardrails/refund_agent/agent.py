# labs/adk/lab1-refund-guardrails/refund_agent/agent.py
# Acme refund desk, Lab 1 build-up: policy in code.
#   before_model_callback  block_card_numbers  card numbers never reach the model
#   before_tool_callback   refund_cap          hard ceiling, app:refund_cap_usd (default $1,500)
#   after_tool_callback    redact_pii          emails leave lookup_order as [email redacted]
#   after_model_callback   meter_tokens        running token count in state
#   FunctionTool(require_confirmation=...)     a human approves refunds over $200
# Tested against google-adk 2.13.0 source.
import re
from typing import Annotated, Any, Literal, Optional

from pydantic import Field
from google.adk import Agent, Context
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools import BaseTool, FunctionTool, ToolContext
from google.genai import types

ORDERS = {
    "A-1001": {"email": "dana@example.com", "total_usd": 89.0, "days_since_delivery": 12, "category": "apparel"},
    "A-1002": {"email": "li@example.com", "total_usd": 1299.0, "days_since_delivery": 41, "category": "electronics"},
    "A-1003": {"email": "sam@example.com", "total_usd": 24.5, "days_since_delivery": 3, "category": "grocery"},
}
RETURN_WINDOW_DAYS = {"apparel": 30, "electronics": 30, "grocery": 0}
APPROVAL_THRESHOLD_USD = 200.0          # refund_cap still blocks anything over $1,500

CARD = re.compile(r"\b(?:\d[ -]?){13,16}\b")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


# ---------- tools (lookup_order, check_refund_eligibility: unchanged from lab1-refund-tools) ----------

def lookup_order(
    order_id: Annotated[str, Field(description="Order ID, e.g. A-1001")],
) -> dict:
    """Look up an order.

    Always call this before answering a refund question."""
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        return {"status": "error",
                "error_message": f"No order with ID {order_id}."}
    return {"status": "success", "order": order}


Reason = Literal["changed_mind", "damaged", "wrong_item"]   # becomes an enum


def check_refund_eligibility(
    order_id: str, reason: Reason = "changed_mind"
) -> dict:
    """Apply the refund policy: 30-day window.

    Grocery is final sale unless damaged. Damaged or wrong items are
    always refundable, inside or outside the window.
    """
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        return {"status": "error",
                "error_message": f"No order with ID {order_id}."}
    if reason in ("damaged", "wrong_item"):
        return {"status": "success", "eligible": True, "rule": "defect_override"}
    window = RETURN_WINDOW_DAYS[order["category"]]
    eligible = order["days_since_delivery"] <= window
    return {"status": "success", "eligible": eligible, "window_days": window,
            "days_since_delivery": order["days_since_delivery"]}


def issue_refund(order_id: str, amount_usd: float, tool_context: ToolContext) -> dict:
    """Issue a refund to the original payment method. Irreversible."""
    issued = tool_context.state.get("refunds_issued", [])
    tool_context.state["refunds_issued"] = issued + [{"order_id": order_id, "amount_usd": amount_usd}]
    return {"status": "success", "refund_id": f"RF-{order_id}", "amount_usd": amount_usd}


def needs_approval(order_id: str, amount_usd: float,
                   tool_context: ToolContext) -> bool:
    """Same parameters as issue_refund.

    ADK calls this with the tool's own arguments."""
    return amount_usd > APPROVAL_THRESHOLD_USD   # a real bool, never None


# ---------- callbacks ----------

def block_card_numbers(callback_context: Context, llm_request: LlmRequest) -> Optional[LlmResponse]:
    last = llm_request.contents[-1] if llm_request.contents else None
    text = " ".join(p.text or "" for p in (last.parts or [])) if last else ""
    if CARD.search(text):
        return LlmResponse(content=types.Content(role="model", parts=[types.Part.from_text(
            text="For your security, please don't share card numbers here. I've flagged the ticket.")]))
    return None                                            # None = call the model


def refund_cap(tool: BaseTool, args: dict[str, Any],
               tool_context: ToolContext) -> Optional[dict]:
    cap = tool_context.state.get("app:refund_cap_usd", 1500)
    amount = args.get("amount_usd", 0)
    if tool.name == "issue_refund" and amount > cap:
        msg = f"Refunds over ${cap} are blocked by policy."
        return {"status": "error", "error_message": msg}
    return None                        # None = run the tool


def redact_pii(tool: BaseTool, args: dict, tool_context: ToolContext,
               tool_response: dict) -> Optional[dict]:
    if tool.name == "lookup_order" and "order" in tool_response:
        order = {k: EMAIL.sub("[email redacted]", v)
                 if isinstance(v, str) else v
                 for k, v in tool_response["order"].items()}
        return {**tool_response, "order": order}
    return None                     # None = keep the tool result


def meter_tokens(callback_context: Context,
                 llm_response: LlmResponse) -> Optional[LlmResponse]:
    if llm_response.usage_metadata:
        used = callback_context.state.get("tokens_used", 0)
        callback_context.state["tokens_used"] = used + (
            llm_response.usage_metadata.total_token_count or 0)
    return None                     # None = keep the response


root_agent = Agent(
    name="refund_agent",
    model="gemini-3.5-flash",
    description="Answers refund questions and issues refunds for Acme retail orders.",
    instruction=(
        "You are a refund desk assistant. Use lookup_order, then check_refund_eligibility. "
        "Quote the rule you applied. Never promise a refund the tool did not approve. "
        "Call issue_refund only for an eligible order. If the tool says the call "
        "was rejected, tell the customer a supervisor declined it."
    ),
    tools=[lookup_order, check_refund_eligibility,
           FunctionTool(issue_refund,
                        require_confirmation=needs_approval)],
    before_model_callback=block_card_numbers, before_tool_callback=refund_cap,
    after_tool_callback=redact_pii, after_model_callback=meter_tokens,
)
