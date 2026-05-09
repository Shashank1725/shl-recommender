# SHL Assessment Recommender

Conversational AI agent jo SHL catalog se assessments recommend karta hai.

## Files ka Structure

```
shl-recommender/
├── scraper.py        # SHL website se data scrape karta hai
├── vector_store.py   # FAISS index banata hai
├── agent.py          # AI agent logic
├── main.py           # FastAPI server
├── test_agent.py     # Tests
├── requirements.txt  # Dependencies
├── render.yaml       # Deployment config
└── .env.example      # API key template
```

## Step-by-Step Setup

### Step 1: Install karo
```bash
pip install -r requirements.txt
```

### Step 2: Gemini API key lo (FREE)
1. https://aistudio.google.com/app/apikey pe jao
2. "Create API Key" click karo
3. Copy karo

### Step 3: .env file banao
```bash
cp .env.example .env
# .env file mein apni key dalo:
# GEMINI_API_KEY=your_key_here
```

### Step 4: Catalog scrape karo
```bash
python scraper.py
# catalog.json ban jayegi
```

### Step 5: FAISS index banao
```bash
python vector_store.py
# faiss_index/ folder ban jayega
```

### Step 6: Server chalao
```bash
export GEMINI_API_KEY=your_key_here   # ya .env use karo
uvicorn main:app --reload --port 8000
```

### Step 7: Test karo
```bash
python test_agent.py
```

## API Endpoints

### GET /health
```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

### POST /chat
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "I am hiring a Java developer"}
    ]
  }'
```

## Deploy on Render (Free)

1. GitHub pe push karo (catalog.json aur faiss_index/ bhi include karo)
2. render.com pe jao → "New Web Service"
3. GitHub repo connect karo
4. Environment variable mein `GEMINI_API_KEY` dalo
5. Deploy!

## Response Schema

```json
{
  "reply": "Agent's reply",
  "recommendations": [
    {
      "name": "Java 8 (New)",
      "url": "https://www.shl.com/...",
      "test_type": "K"
    }
  ],
  "end_of_conversation": false
}
```

## Test Types
- A = Ability
- B = Biodata  
- C = Competency
- D = Development
- E = Assessment Exercise
- K = Knowledge/Skills
- M = Multimedia
- P = Personality
- S = Situational Judgment
