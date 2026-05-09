# Approach Document: SHL Assessment Recommender

## 1. Design Choices
Our objective was to build a highly responsive, stateless conversational AI agent that strictly adheres to the provided JSON response schema while acting within the boundaries of an SHL catalog recommender. We selected the following stack:
- **FastAPI / Uvicorn**: Lightweight and highly performant framework for exposing the required stateless `POST /chat` and `GET /health` endpoints.
- **Google Gemini 1.5 Flash**: Chosen for its fast inference capability, excellent instruction-following, and generous free tier, enabling us to consistently output structured JSON data under the 30-second timeout constraints.
- **Sentence Transformers & FAISS**: For semantic vector search. We used the lightweight `all-MiniLM-L6-v2` local embedding model because it runs quickly on typical CPU instances without requiring dedicated GPUs. FAISS (`IndexFlatIP` on normalized vectors) provided lightning-fast, exact inner-product (cosine similarity) matching.

## 2. Retrieval Setup
Our retrieval architecture follows a classic low-latency Retrieval-Augmented Generation (RAG) pattern:
1. **Scraping**: A custom Python script (`scraper.py`) extracted assessment names, URLs, test types, and remote/adaptive capabilities from the SHL product catalog.
2. **Embedding**: We concatenated these fields into dense textual descriptions and embedded them using `all-MiniLM-L6-v2`. The embeddings and payloads are serialized locally alongside the FAISS index.
3. **Query Extraction**: Passing the entire raw conversational history directly into a vector search often introduces noise. We mitigate this by extracting and merging only the most recent user messages to formulate a clean search query.
4. **Context Injection**: We retrieve the Top-15 most semantically relevant catalog items and strictly inject them into the LLM system prompt as the *only* permissible knowledge base.

## 3. Prompt Design
The prompt is engineered for strict behavioral guardrails and schema compliance. It enforces the following core behaviors:
- **Clarify vs. Recommend**: Explicit guidelines inform the model to probe for more details if the user prompt is vague (e.g., "I need an assessment"), and restrict recommendations to an empty array `[]` during this gathering phase.
- **No Hallucinations**: The prompt mandates using *only* the injected SHL context. The JSON parser logic further sanitizes the output by aggressively filtering out any URLs hallucinated by the model that do not exist in the retrieved subset.
- **Off-Topic Refusals**: Strict rules dictate polite refusal strategies for out-of-scope interactions (e.g., general hiring advice, prompt injections). 
- **JSON Enforcement**: We utilize a `temperature=0.2` setting to maintain highly deterministic schema structures, alongside localized regex-fallback parsers in `agent.py` to safeguard against unexpected markdown-wrapping.

## 4. Evaluation Approach
We adopted a multi-layered evaluation strategy to align with the automated replay harness scoring requirements:
- **Unit Behavior Tests (`test_agent.py`)**: Localized test sweeps verifying binary assertions around behavior mapping. We structured tests for *Vague Queries* (asserting empty recommendations), *Specific Queries*, *Off-topic Refusals*, *Mid-conversation Refinements*, and *Prompt-Injection Handling*.
- **Recall Verifications**: We iteratively tuned the metadata string combinations (e.g., emphasizing descriptive keywords alongside categorical codes) before passing them to the SentenceTransformer to ensure domain-specific queries correctly elevate the required assessments into the Top 15 slice.

## 5. Iterations & What Didn't Work
- **Naive Conversational Search**: Initially, feeding conversational logs directly into the semantic model yielded poor recall because conversational fillers degraded the vector quality. **Improvement**: We pivoted to a localized heuristic where only the last three user-utterances are combined to drive the semantic query.
- **Cold Boot & Request Latency**: Dynamically loading the dense transformer models and FAISS indices per request led to unacceptable latencies and risked the 30-second cap. **Improvement**: We refactored `vector_store.py` to utilize a globally cached module state, loading the assets purely into application memory during Uvicorn's startup cycle.

## 6. Use of AI Tools
Generative coding assistants (Antigravity/Gemini) were used during the construction of this prototype. They were leveraged for:
- Bootstrapping the initial FastAPI server boilerplate.
- Troubleshooting indentation syntax errors and refining pagination boundary logic during the web-scraping phase.
- Implementing architectural optimizations (caching the FAISS and transformer models to bypass heavy computational restarts per request).
- Drafting this architectural approach overview.
