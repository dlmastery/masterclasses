#!/usr/bin/env bash
# Lab 2, step 3: call the claims App over REST and SSE.
# Terminal 1 (lab folder):  adk api_server agents --port 8000
# Terminal 2:               bash rest_calls.sh
# Windows: run this in Git Bash or WSL (PowerShell breaks the quoted JSON).
set -e
B=localhost:8000

curl -s $B/list-apps; echo

curl -s -X POST $B/apps/claims_api/users/u-tom/sessions \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"claim-77","state":{"channel":"email"}}'; echo

curl -s -X POST $B/run -H "Content-Type: application/json" -d '{
  "appName":"claims_api","userId":"u-tom","sessionId":"claim-77",
  "newMessage":{"role":"user","parts":[
    {"text":"What is my collision deductible on POL-448120?"}]}}'; echo

# add "streaming":true to also get partial text chunks
curl -N -X POST $B/run_sse -H "Content-Type: application/json" -d '{
  "appName":"claims_api","userId":"u-tom","sessionId":"claim-77",
  "newMessage":{"role":"user","parts":[{"text":"Is glass covered?"}]}}'; echo

curl -s $B/apps/claims_api/users/u-tom/sessions/claim-77; echo
