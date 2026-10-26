#!/usr/bin/env bash
# Lab 10 step 3: smoke-test the deployed Acme HR agent.
set -euo pipefail
: "${PROJECT:?}" "${REGION:?}" "${AGENT_ENGINE_ID:?}"

# Cloud Run: identity token, not access token (an access token gets 403)
URL=$(gcloud run services describe acme-hr --region=$REGION \
  --format='value(status.url)')
TOKEN=$(gcloud auth print-identity-token)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "$URL/apps/hr_agent/users/E-1001/sessions/s1"
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  "$URL/run_sse" -d '{"app_name":"hr_agent","user_id":"E-1001","session_id":"s1",
    "new_message":{"role":"user","parts":[{"text":"What is my salary band?"}]},
    "state_delta":{"employee_id":"E-1001"},"streaming":false}'

# Agent Runtime: REST :query
RE=projects/$PROJECT/locations/$REGION/reasoningEngines/$AGENT_ENGINE_ID
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://$REGION-aiplatform.googleapis.com/v1/$RE:query" \
  -d '{"class_method":"async_create_session","input":{"user_id":"E-1001"}}'
