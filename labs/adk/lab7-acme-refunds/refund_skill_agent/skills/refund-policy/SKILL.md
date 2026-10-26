---
name: refund-policy
description: Decide refund eligibility and partial-refund
  amounts for Acme orders. Use for any refund, return
  or chargeback question.
metadata:
  adk_additional_tools:
    - lookup_order
---
Step 1: Call `lookup_order` with the order id.
Step 2: Read `references/policy.md` for the return windows.
Step 3: If the order is past the full-refund window but
inside 60 days, run `scripts/prorate.py` with args
{"amount": <amount>, "days": <days_since_purchase>}.
Step 4: Answer REFUNDABLE, PARTIAL_REFUND <amount>, or
NOT_REFUNDABLE with one reason.
