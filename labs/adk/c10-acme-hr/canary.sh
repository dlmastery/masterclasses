#!/usr/bin/env bash
# Lab 10 build-up: canary a new Cloud Run revision behind an eval run.
# Guard metrics, written down before launch:
#   error rate · p99 latency · tokens per invocation · judge score
set -euo pipefail
# 1. new revision at 0% traffic; the tag gets its own URL
gcloud run deploy acme-hr --image "$IMAGE_URL" --no-traffic --tag cand
# 2. eval the live candidate before any user reaches it
agents-cli eval run --url "https://cand---acme-hr-xyz.a.run.app"
# 3. shift traffic; hold each step while the guard metrics stay steady
gcloud run services update-traffic acme-hr --to-revisions REV_NEW=5
gcloud run services update-traffic acme-hr --to-revisions REV_NEW=25
gcloud run services update-traffic acme-hr --to-revisions REV_NEW=100
# 4. rollback trigger: tokens per invocation > 1.5x baseline (a loop).
#    Run this by hand (or from an alert) when it fires:
# gcloud run services update-traffic acme-hr --to-revisions REV_PREV=100
