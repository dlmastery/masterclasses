#!/usr/bin/env bash
# Lab 10 step 3: ship hr_agent/ to Agent Runtime, Cloud Run or GKE.
# Run in the parent of hr_agent/. Run block A first: B uses its AGENT_ENGINE_ID.
set -euo pipefail
gcloud auth application-default login
export PROJECT=my-proj REGION=us-central1
gcloud config set project "$PROJECT"

# A) Agent Runtime: managed sessions + Memory Bank, traces without content
adk deploy agent_engine --project=$PROJECT --region=$REGION \
  --display_name="acme-hr" --otel_to_cloud \
  --service_account=acme-hr@$PROJECT.iam.gserviceaccount.com hr_agent
export AGENT_ENGINE_ID=1234567890              # printed by the first deploy
adk deploy agent_engine --project=$PROJECT --region=$REGION \
  --agent_engine_id=$AGENT_ENGINE_ID hr_agent  # later: update in place

# B) Cloud Run: private, one warm instance; flags after "--" go to gcloud
adk deploy cloud_run --project=$PROJECT --region=$REGION \
  --service_name=acme-hr --session_service_uri="agentengine://$AGENT_ENGINE_ID" \
  hr_agent -- --no-allow-unauthenticated --min-instances=1 \
  --set-env-vars=ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false

# C) GKE: ClusterIP by default, no public IP
adk deploy gke --project=$PROJECT --region=$REGION \
  --cluster_name=agents-prod --service_type=ClusterIP hr_agent
# also: --extra_packages (2.13), --validate-agent-import; --trace_to_cloud is deprecated
