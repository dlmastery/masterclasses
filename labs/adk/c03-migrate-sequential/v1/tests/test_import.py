# Run with: python -W error::DeprecationWarning -m pytest tests/
# Fails on v1 (SequentialAgent is deprecated), passes on v2 (Workflow).
def test_agent_builds_without_deprecation():
    from support_desk import agent
    assert agent.root_agent is not None
