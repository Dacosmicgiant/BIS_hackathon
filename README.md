# BIS Copilot

AI-powered BIS standard recommendation engine for Indian Micro and Small Enterprises (MSEs).

Built for the **Bureau of Indian Standards × Sigma Squad AI Hackathon** — IIT Tirupati, 2026.

---

## What It Does

Converts a plain-language product description into precise BIS standard recommendations in under 100ms.

> *"We manufacture 33 grade ordinary Portland cement"*
> → **IS 269 : 1989** · IS 8112 : 1989 · IS 12269 : 1987 · ...

---

## Architecture

```
Product Description
        ↓
  Query Validator (Gemini Flash Lite)
        ↓
   ┌─────────────────────────────┐
   │       Hybrid Retriever      │
   ├──────────────┬──────────────┤
   │ Dense (BGE)  │ Sparse (BM25)│
   │  ChromaDB    │  rank_bm25   │
   └──────────────┴──────────────┘
        ↓ RRF Fusion
   Top 5 Candidates
        ↓
   Rationale Generator (Gemini Flash Lite)
        ↓
   Structured Response + PDF Export
```

**Key innovation:** Structured parsing — each of the 566 BIS standards is a typed JSON object, not a generic text chunk. IS codes live in metadata, never generated. Zero hallucination risk on standard numbers.

---

## Performance

| Metric | Score | Target |
|---|---|---|
| Hit Rate @3 | 100% | >80% |
| MRR @5 | 0.8833 | >0.7 |
| Avg Latency | ~50ms (no rationale) | <5s |

Evaluated on the 10-query public test set from BIS SP 21.

---

## Dataset

**BIS SP 21 : 2005** — Summaries of Indian Standards for Building Materials.

- 566 unique standards parsed
- 27 sections covered (Section 1–27)
- 566/566 scope coverage (100%)
- Sections range from Cement & Concrete to Wiring Accessories

---

## Tech Stack

| Layer | Tool |
|---|---|
| PDF Parsing | pdfplumber |
| Embeddings | BAAI/bge-small-en-v1.5 |
| Vector Store | ChromaDB |
| Sparse Search | rank_bm25 (BM25Okapi) |
| Fusion | Reciprocal Rank Fusion |
| LLM | Gemini 2.0 Flash Lite |
| Backend | FastAPI |
| Frontend | React + Tailwind |
| PDF Export | ReportLab |

---

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- A Gemini API key from [aistudio.google.com](https://aistudio.google.com)

### 1. Clone and install

```bash
git clone https://github.com/your-username/BIS_copilot.git
cd BIS_copilot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Build the index

Place `SP21.pdf` in the `data/` folder, then:

```bash
python3 src/parser.py      # Parse PDF → data/standards.json
python3 src/indexer.py     # Build ChromaDB + BM25 index
```

### 4. Run

```bash
# Backend
python3 app.py

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

---

## Running Inference (Judge Evaluation)

```bash
python3 inference.py --input data/public_test_set.json --output data/results_public.json
python3 eval_script.py --results data/results_public.json
```

---

## Repository Structure

```
BIS_copilot/
├── src/
│   ├── parser.py        # PDF → structured standard objects
│   ├── indexer.py       # Build ChromaDB + BM25 index
│   ├── retriever.py     # Hybrid search + RRF fusion
│   ├── pipeline.py      # End-to-end orchestration + Gemini
│   └── exporter.py      # PDF report generation
├── frontend/            # React + Tailwind UI
├── data/
│   ├── standards.json       # Parsed standards (generated)
│   └── public_test_set.json # Public evaluation queries
├── index/               # ChromaDB + BM25 index (generated)
├── inference.py         # Judge entry point
├── eval_script.py       # Provided evaluation script
├── app.py               # FastAPI server
├── requirements.txt
├── .env.example
└── README.md
```

---

## Future Scope

- **Compliance Readiness Score** — gap analysis via structured questionnaire
- **ISI Mark Application Assistant** — guides MSEs through certification
- **Standard Revision Alerts** — notify when an IS code is updated
- **Multi-product Portfolio Mapping** — compliance across entire product line
- **Vernacular Support** — Hindi, Marathi, Tamil for MSE owners
- **BIS Portal API Integration** — when BIS opens programmatic access

---

## Team

Solo submission — BIS × Sigma Squad AI Hackathon, IIT Tirupati, April–May 2026.

---

## Acknowledgements

- Bureau of Indian Standards for BIS SP 21 : 2005
- IIT Tirupati Sigma Squad for organizing the hackathon
- BAAI for the BGE embedding model
- Google for Gemini Flash Lite API