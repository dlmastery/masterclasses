# 01 — From Google Agentspace to Gemini Enterprise (status as of 2026-10-23)

> Research brief for a university deck on Google ADK 2.0 and the Google agent platform.
> Sources are primary Google pages fetched on 2026-10-23 (most doc pages show "Last updated 2026-10-20/22 UTC").
> Anything I could not confirm on a primary page is marked **[UNVERIFIED]**.
> Research limit: the web-search budget for this session ran out, so this brief comes only from fetching known primary URLs directly. I could not search for codelab titles or pricing pages (see Section 11).

---

## 0. TL;DR for the speaker

- **Google Agentspace** was announced on **Dec 13, 2024**. On **Oct 9, 2025** it was folded into **Gemini Enterprise**, which Google calls "the new front door for AI in the workplace".
- On **Apr 22, 2026** (Cloud Next '26), **Vertex AI** became the **Gemini Enterprise Agent Platform**, and **Vertex AI Agent Engine** became **Agent Runtime**. Other renames:
  - Vertex AI Studio became **Agent Studio**.
  - Agent Builder Memory Bank became **Agent Platform Memory Bank**.
- Within the Gemini Enterprise app:
  - **Agent Designer** is now **Workflow Builder** (GA on Sep 3, 2026).
  - **NotebookLM Enterprise** is now **Gemini Notebook Enterprise** (Jul 16, 2026).
  - **Idea Generation** was **removed** on Jul 14, 2026.
- There are two ways to bring developer-built agents into Gemini Enterprise:
  1. **ADK agent on Agent Runtime**, using `adkAgentDefinition.provisionedReasoningEngine`.
  2. **A2A agent hosted anywhere**, using `a2aAgentDefinition.jsonAgentCard`.
  - Both go through the Discovery Engine `v1alpha` `.../assistants/default_assistant/agents` API, or through `agents-cli publish gemini`.
- Governance is handled by four pieces: **Agent Registry**, **Agent Gateway** (egress allow/deny), **Agent Identity**, and **Model Armor**.
- **Google Cloud Marketplace** sells partner A2A agents. At Next '26, Google said the Agent Marketplace launched with "70+ partner-built agents".

---

## 1. Naming and rename timeline (verify before every slide)

| Date | Event | Source |
|---|---|---|
| 2024-12-13 | **Google Agentspace** announced. It offered enterprise search, expert agents, NotebookLM Plus, connectors (Confluence, Drive, Jira, SharePoint, ServiceNow), RBAC, VPC-SC and IAM. A low-code visual agent builder was "planned". | https://cloud.google.com/blog/products/ai-machine-learning/bringing-ai-agents-to-enterprises-with-google-agentspace |
| 2025-01-31 / 2025-02-07 | NotebookLM Enterprise licensing; NotebookLM Enterprise integrated into Agentspace Enterprise; multi-region support | GE release notes |
| 2025-04-09 | **Agent Gallery GA**; **Agent Designer** and **Idea Generation** enter Private Preview | GE release notes |
| 2025-05-08 | App tier set by license type: *Agentspace Enterprise* vs *Agentspace Enterprise Plus* | GE release notes |
| 2025-07-31 | GA entry (the release notes now show it under the "Gemini Enterprise" name, so the page was retro-renamed) and **Deep Research** agent announced | GE release notes |
| 2025-08-01 | **Idea Generation** (Preview) and **Data agent** (Private Preview; natural language over BigQuery) | GE release notes |
| 2025-09-15 | Model Armor screens prompts and responses in Agentspace / NotebookLM Enterprise apps | GE release notes |
| **2025-10-09** | **"Google Agentspace is part of Gemini Enterprise."** The console and default app are renamed. Google launches Gemini Enterprise at its "Gemini at Work" event. | GE release notes; https://cloud.google.com/blog/products/ai-machine-learning/introducing-gemini-enterprise ; https://blog.google/products/google-cloud/gemini-enterprise-sundar-pichai/ |
| 2025-11-17 | ADK and A2A agent registration announced | GE release notes |
| 2025-11-19 | Agent Designer **visual flow builder** (Preview); Gemini 3 Pro previews | GE release notes |
| 2025-12-05 | Admins can add **A2A agents from Google Cloud Marketplace** (Preview) | GE release notes |
| 2025-12-12 | Unified data-source flow with 12 connectors: 6 GA (SharePoint, Outlook, OneDrive, Drive, Calendar, Gmail) and 6 Preview (Jira Cloud, Confluence Cloud, Box, Teams, Dropbox, ServiceNow) | GE release notes |
| 2025-12-19 | Scheduled agent executions (Preview) | GE release notes |
| 2026-01-12 | **Agent Designer GA** | GE release notes |
| 2026-02-23 | Agent sharing in Agent Designer GA; sharing Marketplace agents GA | GE release notes |
| 2026-03-24 | **Data Insights agent** (BigQuery), GA with allowlist | GE release notes |
| 2026-04-20 | Registering ADK agents on Agent Engine is **GA**; end users can request Marketplace agents from Agent Gallery (Preview) | GE release notes |
| 2026-04-21 | Registering A2UI and A2A agents (Preview) | GE release notes |
| **2026-04-22** | **Gemini Enterprise Agent Platform** launches. Release notes say "Vertex AI is now part of Gemini Enterprise Agent Platform" and "**Agent Engine is now Agent Runtime**". Agent Registry (Public Preview), Agent Gateway (Private Preview), Agent Identity (GA). | https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes |
| 2026-04-24 | Next '26 recap blog | https://cloud.google.com/blog/topics/google-cloud-next/google-cloud-next-2026-wrap-up |
| 2026-04-28 | Custom MCP server data stores (Preview, off by default, needs an org-policy change) | GE release notes |
| 2026-06-18 | Agent Registry **GA** (API v1, A2A v1, Terraform); Agent Gateway **GA**; workflow agents GA (allowlist) | Agent Platform and GE release notes |
| 2026-06-25 | **Governance for agents and MCP servers GA**: Agent Gateway egress policies allow or deny traffic to agents and MCP servers | GE release notes |
| 2026-07-14 | **Idea Generation agent removed**. Users are pointed to the assistant, Deep Research or **Co-Scientist**. | GE release notes |
| 2026-07-16 | **NotebookLM Enterprise is renamed Gemini Notebook Enterprise** (APIs unchanged) | GE release notes |
| 2026-08-01 | **Pay-as-you-go edition GA** | GE release notes |
| 2026-08-17 | A2A and A2UI agent registration **GA** (A2UI v0.9) | GE release notes |
| 2026-08-18/20 | **Antigravity for IDEs** added to "AI developer tools" | GE release notes |
| **2026-09-03** | **Workflow Builder (formerly Agent Designer) GA**. Adds agent import for A2A and ADK agents and an "Enhanced Agent Gallery" (keyword search, filter chips, pins). | GE release notes |
| 2026-09-08 | Semantic search for agents in Google Cloud Marketplace (Preview) | GE release notes |
| 2026-09-17 | New Standard and Plus subscriptions no longer include Gemini Code Assist | GE release notes |
| 2026-10-07 | Pay-as-you-go overage enabled for Frontline, EDU and Emerging Market editions | GE release notes |
| 2026-10-13/14 | Workflow Builder connectors for Teams, Notion and Salesforce; **Gemini 4 Argon** available in Workflow Builder | GE release notes |
| 2026-10-20 | **Antigravity Enterprise Gateway** support GA | GE release notes |

Release notes URL: https://docs.cloud.google.com/gemini/enterprise/docs/release-notes. The docs moved from `cloud.google.com/gemini/enterprise/docs/...` to `docs.cloud.google.com/...`; the old links return a 301 redirect.

Teaching note: the ADK docs also moved. `google.github.io/adk-docs` redirects (301) to **https://adk.dev**, and `adk.dev/deploy/agent-engine/` redirects to `adk.dev/deploy/agent-runtime/`.

Observed oddity: on 2026-10-23, the `<title>` of https://cloud.google.com/gemini-enterprise read "Gemini for Business: The Universal Work Agent". It is unclear whether this signals another brand change. **[UNVERIFIED]**

---

## 2. What Gemini Enterprise is (architecture in words)

The Oct 9, 2025 launch blog lists **six components**:

1. **Gemini models**, described as "the brains".
2. A **no-code workbench**, first called Agent Designer and now Workflow Builder.
3. **Pre-built Google agents**, a "taskforce" for deep research and data insights.
4. **Data connectors** for Workspace, Microsoft 365, Salesforce, SAP and others.
5. **Central governance** to "visualize, secure, and audit all of your agents from one place".
6. An **open ecosystem** of more than 100,000 partners.

Other launch numbers:
- The GEAR (Gemini Enterprise Agent Ready) program targets 1 million developers.
- AP2 (Agent Payments Protocol) has more than 100 partners.
- Commerzbank: more than 2 million chats, 70% of inquiries resolved.

The docs define Gemini Enterprise as "an intranet search, AI assistant, and agentic platform".

**Diagram flow** (left to right):

1. **User surfaces.** The Gemini Enterprise web app, mobile app (Standard/Plus GA with allowlist, Feb 12, 2026), and GE Desktop with skills.
2. **Assistant.** Users work through `default_assistant`, using Projects, Skills ("@"), Canvas, and the Inbox ("Needs your input / Errors / Completed").
3. **Agent layer.** It has four sources:
   - (a) Made-by-Google agents: Deep Research, Gemini Notebook Enterprise, Co-Scientist, Data Insights.
   - (b) Workflow Builder chat agents and workflows (no-code).
   - (c) Custom agents: ADK on Agent Runtime, or A2A/A2UI hosted anywhere.
   - (d) Marketplace partner agents.
4. **Grounding layer.** Connectors (ingested index or federated), Google Search/web, and custom MCP servers.
5. **Governance plane.** IAM/SSO, Agent Registry, Agent Gateway egress policy, Model Armor, audit logs in Cloud Logging, VPC-SC, CMEK.
6. **Build plane.** The **Gemini Enterprise Agent Platform** (ex-Vertex AI): ADK, Agent Studio, Agent Runtime, Memory Bank, Sessions, Sandbox, Evaluation/Simulation/Optimizer.

### Agent Gallery (four sections)

Source: https://docs.cloud.google.com/gemini/enterprise/docs/agent-gallery

- **Made by Google:** Deep Research, Gemini Notebook Enterprise, Co-Scientist.
- **Marketplace:** "Third-party partner agents available to request from your administrator." The user requests access and the admin approves.
- **From your organization:** agents colleagues have shared.
- **Your agents:** the user's own Workflow Builder agents, shown as Draft or Live.

Next '26 named partner agents in the Gallery from Accenture, Adobe, Atlassian, Deloitte, Salesforce, ServiceNow and Workday.

---

## 3. Editions (and what is public about price)

Source: https://docs.cloud.google.com/gemini/enterprise/docs/editions (last updated 2026-10-22)

| Edition | Seats | Pooled storage/index |
|---|---|---|
| Business | 1–500 users (documented in a separate Help Center) | 25 GiB |
| Standard | 1+ | 30 GiB |
| Plus | 1+ | 75 GiB |
| Pay-as-you-go (GA 2026-08-01) | 1 minimum seat; requires an invoiced Cloud Billing account | PAYG |
| Frontline | 150+ users of Standard or Plus | 2 GiB |

**Shared features across editions:**
- Permission-aware enterprise search
- Grounding on enterprise data, Google Search and the web
- Deep Research
- Agent Marketplace access
- Basic agent governance
- Custom no-code agents

**Frontline restrictions:**
- **No Made-by-Google agents.**
- Users can install skills but cannot create them.
- Users can only use agents that an admin has provisioned for them.

**Partner models:** Anthropic Claude Opus 5.5 and Sonnet 5.5 can be used through AI developer tools. They are billed on consumption right away, and seat credits cover only first-party Gemini models.

**Prices:** the editions page links to pricing pages but **states no prices**. The pricing URLs I tried (`/gemini-enterprise/pricing`, `/products/gemini-enterprise/pricing`, `/gemini-enterprise/editions`) returned 404.
- Launch-week press coverage in Oct 2025 reported about **$30/user/month** for Gemini Enterprise (Standard/Plus) and about **$21/user/month** for **Gemini Business**. **[UNVERIFIED: not on a primary page I could fetch; ask Sales or check the console]**

**Agent-creation quota** (this matters for CI/CD):
- Each `agents.create` uses one unit of the pooled daily quota `discoveryengine.googleapis.com/agents_tier_enterprise_regional`.
- Allowance per user per day: Standard = 1, Plus = 10, Frontline = 0.
- Going over returns `HTTP 429 RESOURCE_EXHAUSTED: Agent creation quota exceeded`.

---

## 4. Workflow Builder (formerly Agent Designer): no-code and low-code

Source: https://docs.cloud.google.com/gemini/enterprise/docs/agent-designer (the page keeps the old slug; last updated 2026-10-20)

- The docs define it as "an interactive no-code, low-code platform for creating, managing, and turning on chat agents and workflows in your Gemini Enterprise web app."
- **Two agent types:**
  - **Chat agents** are conversational and "primarily non-deterministic".
  - **Workflows** are sequences of "triggers, steps, and actions", deterministic or not, that can include **human-in-the-loop** steps.
- **Docs navigation lists:** flow-control steps, human-in-the-loop steps, MCP server connections, and "add existing agent" steps (import of ADK/A2A agents, GA Sep 3, 2026).
- **Other features:**
  - Build from a natural-language prompt or in the visual editor.
  - Test in an integrated preview or simulator.
  - Publish and share with users or groups.
  - Schedule runs.
- **Guardrail:** actions and tools are limited to the connectors, tools and permissions the admin has provisioned.
- **Model:** Gemini 4 Argon has been available in Workflow Builder since 2026-10-14.
- **Next '26 positioning:** **Agent Studio** on the Agent Platform builds an agent from a prompt and then **exports the logic to ADK** for full-code work. This is the no-code to pro-code bridge.

**Failure modes to teach:**
- Users expect a Workflow Builder agent to reach data the admin has not connected. It cannot.
- Non-deterministic chat agents get used where a deterministic workflow was needed.
- An agent stays in Draft state and is never shared.
- Scheduled runs fail silently. Check the Inbox "Errors" view.

---

## 5. Registering an ADK agent (Agent Runtime) in Gemini Enterprise

Source: https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-adk-agent (last updated 2026-10-20). GA since 2026-04-20.

### 5.1 Prerequisites
- Role **Gemini Enterprise Admin** (`discoveryengine.agentspaceAdmin`). The role ID still carries the Agentspace name, which is useful trivia for the deck.
- **Discovery Engine API** enabled, and an existing Gemini Enterprise app (an `engine`).
- The ADK agent is **hosted on Agent Runtime**. If it is in another project, cross-project IAM must be granted.

### 5.2 Step 1: Deploy the ADK agent to Agent Runtime
Source: https://adk.dev/deploy/agent-runtime/deploy/

```bash
PROJECT_ID=my-project-id
LOCATION_ID=us-central1

adk deploy agent_engine \
        --project=$PROJECT_ID \
        --region=$LOCATION_ID \
        --display_name="My First Agent" \
        multi_tool_agent
```

On success the CLI prints:
`AgentEngine created. Resource name: projects/123456789/locations/us-central1/reasoningEngines/751619551677906944`

- The CLI subcommand is still `agent_engine`, and the resource type is still **`reasoningEngines`** after the Agent Runtime rename.
- Go version: `adkgo deploy agentengine -e ./main.go -s "multi_tool_agent" -p $PROJECT_ID -r $LOCATION_ID -d .`
- Required APIs: `aiplatform.googleapis.com` (now "Agent Platform API") and Cloud Resource Manager. Authenticate with `gcloud auth login` and `gcloud auth application-default login`.

Accelerated path with **agents-cli**, the successor tooling to Agent Starter Pack. Sources: https://adk.dev/deploy/agent-runtime/agents-cli/ and https://google.github.io/agents-cli/cli/

```bash
uvx google-agents-cli setup
agents-cli scaffold enhance --deployment-target agent_runtime
agents-cli deploy                      # reads deployment_target from pyproject.toml
agents-cli infra single-project        # optional telemetry infra
agents-cli publish gemini \
  --agent-runtime-id projects/P/locations/us-central1/reasoningEngines/ID \
  --gemini-app-id <GEMINI_APP_RESOURCE> \
  --display-name "Expense Helper" --description "Files expenses" \
  --registration-type adk               # or a2a + --agent-card-url
```

- `publish gemini` reads `deployment_metadata.json` when `--agent-runtime-id` is omitted.
- `--list` lists the Gemini apps in the project.
- `-i` prompts for any missing values.
- `GEMINI_APP_ID` can be set as an environment variable.

### 5.3 Step 2 (optional): OAuth so the agent can act on the user's behalf
1. In Credentials, create an **OAuth client ID** of type **Web application**.
2. Add these redirect URIs:
   - `https://vertexaisearch.cloud.google.com/oauth-redirect`
   - `https://vertexaisearch.cloud.google.com/static/oauth/oauth.html`
3. Download the JSON.
4. Build the Authorization URI on `https://accounts.google.com/o/oauth2/v2/auth` with `client_id`, `redirect_uri=.../static/oauth/oauth.html`, `scope` (space-separated as `%20`), `include_granted_scopes=true`, `response_type=code`, `access_type=offline` and `prompt=consent`.
5. Create the authorization resource:

```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: PROJECT_ID" \
  "https://ENDPOINT_LOCATION-discoveryengine.googleapis.com/v1alpha/projects/PROJECT_NUMBER/locations/LOCATION/authorizations?authorizationId=AUTH_ID" \
  -d '{
    "name": "projects/PROJECT_NUMBER/locations/LOCATION/authorizations/AUTH_ID",
    "serverSideOauth2": {
      "clientId": "OAUTH_CLIENT_ID",
      "clientSecret": "OAUTH_CLIENT_SECRET",
      "authorizationUri": "OAUTH_AUTH_URI",
      "tokenUri": "OAUTH_TOKEN_URI"
    }
  }'
```

### 5.4 Step 3: Register the agent
`ENDPOINT_LOCATION` is one of `us`, `eu` or `global`.

```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: PROJECT_ID" \
  "https://ENDPOINT_LOCATION-discoveryengine.googleapis.com/v1alpha/projects/PROJECT_ID/locations/global/collections/default_collection/engines/APP_ID/assistants/default_assistant/agents" \
  -d '{
    "displayName": "Expense Helper",
    "description": "Files and checks expense reports",
    "icon": {"uri": "https://example.com/icon.png"},
    "adkAgentDefinition": {
      "provisionedReasoningEngine": {
        "reasoningEngine": "projects/PROJECT_ID/locations/RESOURCE_LOCATION/reasoningEngines/RESOURCE_ID"
      }
    },
    "authorizationConfig": {
      "toolAuthorizations": ["projects/PROJECT_NUMBER/locations/global/authorizations/AUTH_ID"]
    }
  }'
```

- The field names are taken from the doc. The example values (display name, description, icon URL) are illustrative.
- **Console path:** Gemini Enterprise, then *app*, then **Agents**, then **Add agent**, then **Custom agent via Agent Runtime**. Optionally add an authorization. Then enter the name, the description and the resource path `projects/PROJECT_ID/locations/LOCATION/reasoningEngines/RESOURCE_ID`.
- **Manage the agent** with `GET .../agents` (list), `GET .../agents/AGENT_ID`, `PATCH .../AGENT_RESOURCE_NAME` (only `displayName`, `description` and `reasoningEngine` can be updated) and `DELETE` (returns an LRO with `"done": true`).

### 5.5 Location compatibility (common failure)

| GE app location | Allowed Agent Runtime region |
|---|---|
| `global` | any supported region |
| `us` | `us-*` only |
| `eu` | `europe-*` only |

A mismatch returns an error.

### 5.6 Gotchas from the doc
- **Model Armor:** the console's Model Armor settings **do not protect ADK agents**. Configure Model Armor through the REST API inside the agent code.
- **Identity:** ADK agents **receive the user's email** from Gemini Enterprise.
- **Network:** the link between Agent Runtime and GE is **VPC-SC compliant**.
- **Performance best practices:**
  - Minimize sequential sub-agent hops.
  - Tune `min_instances`, `resource_limits` and `container_concurrency`.
  - Pin package versions.
  - Use the **global** endpoint for model calls.
- **Observability (Agent Platform release notes):**
  - OpenTelemetry tracing has been on by default for new ADK deployments since 2026-06-18.
  - Prompt and response logs include `user.id` from ADK 2.1+. Agents that opted in before 2026-05-22 must redeploy and opt in again.
  - ADK **2.6.0+** on Agent Runtime emits `gen_ai` metrics (2026-08-13).

---

## 6. Registering an A2A agent (hosted anywhere, e.g. Cloud Run)

Source: https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-a2a-agent (GA since 2026-08-17, with A2UI v0.9)

- **Protocol support:** Gemini Enterprise supports **A2A v0.3 streaming**. For A2A **v1.0.0+**, use the compatibility packages: `a2a.compat.v0_3` (Python) or `a2acompat/a2av0` (Go).
- **Cloud Run with a default `.run.app` URL and auth:** grant the Discovery Engine service agent the invoker role:

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:service-PROJECT_NUMBER@gcp-sa-discoveryengine.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

- **Headers your agent receives:**
  - `X-Serverless-Authorization` carries a Google-signed OIDC token for the Discovery Engine service agent. It is sent only for `.run.app` URLs.
  - `Authorization: Bearer USER_OAUTH_TOKEN` is sent when OAuth is configured.
- **Minimal agent card** (paste it in the console under *Custom agent via A2A*):

```json
{
  "protocolVersion": "0.3",
  "name": "Hello World Agent",
  "description": "Just a hello world agent",
  "url": "https://example.com/myagent",
  "version": "1.0.0",
  "capabilities": {},
  "skills": [{"id": "data-analysis","name": "Data Analysis","description": "Data analysis","tags": []}],
  "defaultInputModes": ["text/plain"],
  "defaultOutputModes": ["text/plain"]
}
```

- **REST body:** POST to the same `.../assistants/default_assistant/agents` endpoint with `name`, `displayName`, `description`, `a2aAgentDefinition.jsonAgentCard` (the card as an **escaped JSON string**), and optionally `authorizationConfig.agentAuthorization`. Note that this field differs from the ADK path's `toolAuthorizations`. The response includes `"state": "ENABLED"`.
- **Apigee front door:**
  - OAuth is required.
  - The card `url` must be the proxy URL.
  - Validate third-party JWTs with VerifyJWT.
  - Opaque Google `ya29.` tokens need a ServiceCallout to `https://oauth2.googleapis.com/tokeninfo` that checks `aud` and `scope`.
- **Limitations (good exam material):**
  - **Agent Gateway policies do not apply** to agents registered this way.
  - Console Model Armor settings do not protect them.
  - GE **ignores the card's `securitySchemes` and `security` fields**.
  - `apiKey` auth, static API keys and custom headers are not supported.
  - The same daily creation quota applies.

---

## 7. Made-by-Google agents

- **Deep Research.** Source: https://docs.cloud.google.com/gemini/enterprise/docs/research-assistant
  - It drafts an **editable research plan**. After the user clicks **Start Research**, it streams the topics it is investigating, then writes a **cited report** with a **1–2 minute audio summary**.
  - Sources are indexed connector data, plus the web if web search is enabled.
  - API: call `streamAssist` with agent ID `deep_research`. This takes two calls: generate the plan, then send "Start Research" with the session ID. The API is GA only with an allowlist.
  - Observability settings entered Preview on 2026-06-23. Next '26 added an "Enhanced Deep Research agent".
- **Gemini Notebook Enterprise** (formerly NotebookLM Enterprise, renamed 2026-07-16).
  - Creating and publishing notebooks depends on edition.
  - It is also a **connector** source.
  - EU DRZ/MLP compliance for sources and chat came 2026-06-03; Discover Sources and Studio are not covered.
- **Data Insights** (the earlier "Data agent").
  - Natural-language insights over **BigQuery**.
  - Private Preview 2025-08-01; GA with allowlist 2026-03-24.
  - Not in Frontline.
  - Note: the separate "Data Science agent" brand belongs to Colab/BigQuery notebooks, not Gemini Enterprise. **[UNVERIFIED]**
- **Co-Scientist.** Listed under Made by Google in Agent Gallery, and the recommended replacement for Idea Generation.
- **Idea Generation.**
  - Private Preview 2025-04-09; Preview 2025-08-01; **removed 2026-07-14**.
  - Teaching point: preview agents can disappear.
- **Availability:** no Made-by-Google agents are available in the **Frontline** edition.

---

## 8. Connectors

Source: https://docs.cloud.google.com/gemini/enterprise/docs/connectors/introduction-to-connectors-and-data-stores

- **Two modes:**
  - **Data ingestion (indexing)** gives better quality but costs storage and sync time.
  - **Data federation** queries the source live, with no storage, but quality may be lower.
- **Sources include:**
  - **Google:** Drive, Gmail, Calendar, Chat, Sites, Groups, BigQuery, Spanner, Cloud SQL, AlloyDB, Firestore, Bigtable, GCS, Knowledge Catalog, Gemini Notebook Enterprise.
  - **Microsoft:** Entra ID, OneDrive, Outlook, SharePoint, Teams.
  - **Collaboration and dev:** Box, Dropbox, Notion, Slack, Confluence, Jira, GitHub.
  - **CRM and support:** Salesforce, ServiceNow, Zendesk, HubSpot, Intercom, Zoho, PagerDuty.
  - **Finance and data:** FactSet, Moody's, MSCI, S&P Global, Stripe, NetSuite, D&B.
  - **Custom:** **custom MCP servers** (Preview 2026-04-28) and custom connectors.
- **Operations:**
  - Full syncs plus incremental syncs. Incremental syncs default to **every 3 hours** and must run more often than full syncs.
  - Pausing a sync cancels the run in progress. Resuming schedules a new sync rather than continuing the old one.
  - Regions are global, US or EU. CMEK and static-IP egress are available.
- **Permission-aware search:** ACLs are synced along with identity data, so answers respect what each user is allowed to see.

---

## 9. Governance

- **Agent Registry.** A catalog of agents, MCP servers, tools and skills. Public Preview 2026-04-22; **GA 2026-06-18** with API v1, A2A v1 and Terraform.
- **Agent Gateway.** The control point for agent-to-tool and agent-to-agent egress, with Model Armor built in.
  - Private Preview 2026-04-22; **GA 2026-06-18**.
  - In GE, egress policies allow or deny traffic to agents and MCP servers (GA 2026-06-25).
  - VPC-SC enforcement and up to two associated Registry instances (2026-09-09).
  - **Antigravity Enterprise Gateway** support GA on 2026-10-20.
- **Agent Identity.** A unique cryptographic identity per agent, giving an auditable trail (GA 2026-04-22). The `agentidentity.googleapis.com` API (Preview 2026-06-18) replaces the legacy IAM Connectors API.
- **Model Armor.** Screens prompts and responses for GE apps (since 2025-09-15). It must be configured **in code** for ADK and A2A agents.
- **Security operations (Next '26):** Agent Anomaly Detection (including LLM-as-judge), an Agent Security dashboard (Security Command Center), and Wiz integrations. Usage audit logs in Cloud Logging have been GA since 2026-02-04.
- **Quality loop (Next '26, Agent Platform):** Agent Simulation (synthetic users, virtual tools), Agent Evaluation (continuous multi-turn autoraters on live traffic), and Agent Optimizer (clusters failures and proposes system instructions).
  - The CLI mirrors this: `agents-cli eval generate|grade|run|compare|analyze|dataset synthesize|optimize` (GEPA).
  - This ties into the user's "verifiers per step / evals" theme.

---

## 10. Marketplace for agents

Source: https://docs.cloud.google.com/marketplace/docs/partners/ai-agents (last updated 2026-10-22)

- **Listing types:**
  - **A2A AI agents**, which run on Google Cloud and integrate with GE.
  - SaaS.
  - Kubernetes apps.
  - Professional services.
- **A2A listing requirements:**
  - An **Agent Card** JSON stored in **Cloud Storage** and added in **Producer Portal**.
  - Default models must come from Model Garden.
  - The agent must be discoverable on surfaces such as Gemini Enterprise.
- **Pricing models:** Free, Subscription (prorated), Usage-based (the vendor reports usage), or Combined. Google's pricing review takes up to 4 business days.
- **Publishing:** after Google validates the listing, the vendor gets a `gcloud` command to make it public. Customers buy the agent, then run a command to add it to GE. The exact command is **[UNVERIFIED]**.
- **Customer-side timeline:**
  - Admin add: Preview 2025-12-05.
  - Sharing: GA 2026-02-23.
  - End-user access requests from the Gallery: Preview 2026-04-20.
  - Semantic search: Preview 2026-09-08.
- **Next '26:** the "Agent Marketplace" launched with **70+ partner-built agents**, and partners and startups can now sell agents to GE users.

---

## 11. Codelabs and samples

- I could not run catalog searches (search budget exhausted), and the codelabs catalog page renders client-side. I am not listing codelab titles because they are **unverified**. Before the deck ships, search https://codelabs.developers.google.com for "Gemini Enterprise", "Agentspace", "A2A" and "Agent Engine".
- Verified related assets:
  - The `google/adk-samples` README lists `contrib/python/retail-product-search` and `retail-virtual-tryon` as deployable to "Gemini Enterprise Agent Platform (Agent Engine), Gemini Enterprise (GE), Cloud Run, and Agent Garden".
  - `plugins/retail/skills/*` ship as **GE Desktop skills** with `SKILL.md` and `EVAL.yaml`.
  - Link: https://github.com/google/adk-samples

---

## 12. Interview questions (crisp answers)

1. **What happened to Agentspace?** It became part of Gemini Enterprise on 2025-10-09. Its agent orchestration tech powers GE. The admin role ID `discoveryengine.agentspaceAdmin` still carries the old name.
2. **Agent Engine vs Agent Runtime?** They are the same managed runtime, renamed on 2026-04-22 along with Vertex AI becoming the Gemini Enterprise Agent Platform. The API resource is still `reasoningEngines`, and the CLI is still `adk deploy agent_engine`.
3. **Two ways to bring code-built agents into GE?** First, an ADK agent on Agent Runtime, registered with `adkAgentDefinition.provisionedReasoningEngine.reasoningEngine`. Second, any A2A v0.3 endpoint, registered with `a2aAgentDefinition.jsonAgentCard`. Both use `.../engines/APP_ID/assistants/default_assistant/agents`.
4. **Why does my registration fail with a location error?** The GE app is `us` or `eu`, but the Agent Runtime region is outside `us-*` or `europe-*`.
5. **Does console Model Armor protect my custom agent?** No. Configure it in the agent's code through the REST API.
6. **How does an A2A agent on Cloud Run authenticate GE?** Grant `roles/run.invoker` to `service-PROJECT_NUMBER@gcp-sa-discoveryengine...` and verify `X-Serverless-Authorization`. To act as the user, configure OAuth; the user's token then arrives in `Authorization`.
7. **Why might `agents.create` return 429 in CI?** The pooled daily agent-creation quota (Standard 1, Plus 10, Frontline 0 per user per day) is exhausted.
8. **When should data be federated instead of ingested?** Federate when freshness and zero copy matter more than ranking quality. Ingest for the best retrieval quality and permission-aware indexing.
9. **No-code vs pro-code?** Workflow Builder (ex-Agent Designer) handles chat agents and trigger-based workflows with HITL steps. Agent Studio exports to ADK for code. ADK and A2A agents can be imported back as steps.
10. **What governs agent egress?** Agent Gateway policies, checked against the Agent Registry catalog. They do not apply to A2A agents registered directly.
11. **Why can't my Frontline users see Deep Research?** Made-by-Google agents are excluded from the Frontline edition.
12. **How is a partner agent monetized?** Through a Cloud Marketplace A2A listing with an Agent Card in GCS and a Free, Subscription, Usage or Combined pricing model.

---

## 13. Slide ideas (with explaining animation)

1. **"Three renames in 22 months."** A timeline bar runs Dec 2024 to Oct 2026. Logos morph in sequence: Agentspace to Gemini Enterprise (Oct 9 2025), Vertex AI to Agent Platform and Agent Engine to Agent Runtime (Apr 22 2026), Agent Designer to Workflow Builder and NotebookLM Ent to Gemini Notebook Ent (Jul to Sep 2026).
2. **"Six components."** The hexagon from the launch blog. Each segment lights up as you name it, then the whole hexagon collapses into the "front door" icon.
3. **"The stack."** Layers build bottom-up: Agent Platform (build), then Agent Runtime (run), then Registry/Gateway/Identity (govern), then the GE app (use). A user query animates down the stack and the answer travels back up.
4. **"ADK to GE in 3 commands."** A terminal typewriter shows `adk deploy agent_engine`, then the resource name is highlighted and flies into the JSON `reasoningEngine` field, then `agents-cli publish gemini`. The agent icon then pops into the Gallery.
5. **"A2A handshake."** A sequence diagram: GE fetches the agent card, sends a request with `X-Serverless-Authorization` and the user's OAuth token, and receives a streaming response. Red Xs fall on `securitySchemes` and `apiKey` to show what is ignored.
6. **"Location matrix."** A 3x3 grid with green and red tiles. Drag an Agent Runtime region pin onto a GE app location and watch it light green or flash red.
7. **"Ingest vs federate."** A split screen. On the left, documents copy into an index and a storage meter fills. On the right, a live query arrow goes to the source with the storage meter at zero. A quality slider tilts left.
8. **"Gallery anatomy."** Four tabs (Made by Google, Marketplace, Org, Yours) slide in one by one. A Marketplace card shows a "Request access" button that turns into an admin-approval toast.
9. **"Governance funnel."** An agent call flows through Agent Identity (badge), then Gateway (allow/deny gate), then Model Armor (shield). A blocked call bounces off and appears as an anomaly alert on the Security dashboard.
10. **"Preview agents can vanish."** An Idea Generation card fades out (removed 2026-07-14) and arrows redirect to Deep Research and Co-Scientist. Lesson: design for churn, and pin versions.

---

## 14. Primary URLs used
- https://docs.cloud.google.com/gemini/enterprise/docs/release-notes
- https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-adk-agent
- https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-a2a-agent
- https://docs.cloud.google.com/gemini/enterprise/docs/editions
- https://docs.cloud.google.com/gemini/enterprise/docs/agent-designer
- https://docs.cloud.google.com/gemini/enterprise/docs/agent-gallery
- https://docs.cloud.google.com/gemini/enterprise/docs/research-assistant
- https://docs.cloud.google.com/gemini/enterprise/docs/connectors/introduction-to-connectors-and-data-stores
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes
- https://docs.cloud.google.com/marketplace/docs/partners/ai-agents
- https://cloud.google.com/blog/products/ai-machine-learning/introducing-gemini-enterprise
- https://cloud.google.com/blog/products/ai-machine-learning/bringing-ai-agents-to-enterprises-with-google-agentspace
- https://cloud.google.com/blog/topics/google-cloud-next/google-cloud-next-2026-wrap-up
- https://blog.google/products/google-cloud/gemini-enterprise-sundar-pichai/
- https://adk.dev/deploy/agent-runtime/deploy/ ; https://adk.dev/deploy/agent-runtime/agents-cli/
- https://google.github.io/agents-cli/cli/
- https://github.com/google/adk-samples
