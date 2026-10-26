# Lab 4 · industry · one bounded agent call per question (the PANW pattern)

Palo Alto Networks builds a "Document of Record" (DOR) from 140+ standard questions. Version 1 sent
all questions through one agent context and hit "Out of Memory" errors. The fix: one question per
agent call, state in the orchestrator, batches of five. `dor.py` is that pattern on google-adk 2.13.0,
with seven sample questions about the fictional customer Acme.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install "google-adk==2.13.0"
```

## Environment

`InMemoryRunner` does not load `.env`, so export the variables:

```bash
export GOOGLE_GENAI_USE_ENTERPRISE=FALSE
export GOOGLE_API_KEY="<key from Google AI Studio>"
```

## Run

```bash
python dor.py
```

## Expected output (illustrative, not executed)

The agent has no retrieval tool in this file, so most answers are `UNKNOWN`. Add your own
`rag_tool` (for example a Vertex AI RAG Engine tool) to get grounded answers.

```
Q: Which cloud providers does Acme use?
A: UNKNOWN

Q: How many security analysts does Acme employ?
A: UNKNOWN
...
```

## What to notice

- `asyncio.Semaphore(5)` keeps five questions in flight, like PANW's batches of five.
- A fresh session per question, so the agent context never grows.
- `asyncio.gather` collects every answer into one dict in your process.

Source: Google Cloud blog, "Palo Alto Networks customer intelligence agentic design" (2026-01-14),
https://cloud.google.com/blog/topics/partners/palo-alto-networks-customer-intelligence-agentic-design
