# Paper slide: a simplified sketch of ROPE (arXiv 2608.27496): an origin check
# on the few tool parameters that move money or data out of Acme.
# Agent-level before_tool_callback form: (tool, args, tool_context).
SENSITIVE = {"send_email": ["to"], "transfer_funds": ["iban", "amount"]}


async def origin_guard(tool, args, tool_context):
    fields = SENSITIVE.get(tool.name, [])
    # filled by YOUR code from the user turn / CRM
    trusted = set(tool_context.state.get("user:trusted_values", []))
    for f in fields:
        if str(args.get(f)) not in trusted:
            return {"status": "blocked",  # dict = skip the tool
                    "error": f"'{f}' is not from the user or a "
                             "trusted record; ask the user to confirm"}
    return None

# agent = Agent(..., before_tool_callback=origin_guard)
