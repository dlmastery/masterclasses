#!/usr/bin/env bash
# Lab 10 build-up: agents-cli (google-agents-cli 1.11.0) from scaffold to a
# Gemini Enterprise tile. Run in the parent of hr_agent/.
# The sub-commands come from the agents-cli docs, not from its source.
set -euo pipefail
uvx google-agents-cli setup        # installs agents-cli + ADK skills in the coding agent
agents-cli scaffold enhance --deployment-target agent_runtime
#   + app/agent_engine_app.py  .cloudbuild/  deployment/  tests/  Makefile  pyproject.toml
agents-cli eval run                # inference + grading
agents-cli deploy                  # reads deployment_target from pyproject.toml
agents-cli infra cicd              # staging + prod, Cloud Build pipeline

RE=projects/$PROJECT/locations/$REGION/reasoningEngines/$AGENT_ENGINE_ID
agents-cli publish gemini \
  --agent-runtime-id "$RE" \
  --gemini-app-id "$GEMINI_APP_ID" \
  --display-name "Acme HR" \
  --registration-type adk          # or a2a + --agent-card-url
