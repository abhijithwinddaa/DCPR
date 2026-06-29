# 🏙️ DCPR 2034 Legal Intelligence & Urban Planning Reasoning Engine

> An enterprise-grade, privacy-first Knowledge Base & Reasoning Platform designed specifically for the **Mumbai Development Control and Promotion Regulations (DCPR 2034)**. Combining a **Deterministic Rule Engine**, a **Neo4j Knowledge Graph**, and an **Async Hybrid RAG Architecture** powered by local **Qwen 3 AI**.

---

## 🌟 Architecture Overview

Modern urban planning regulations contain dense mathematical logic, interlinked statutory clauses, and tabular thresholds spread across 1,000+ pages. Traditional RAG systems suffer from hallucinations or fail on mathematical rules. 

**DCPR 2034 Platform** resolves this via a **3-Tier Hybrid Architecture**:

```
                                    ┌────────────────────────────────────────────────────────┐
                                    │               User Interface (React + Vite)            │
                                    └────────────────────────────────────────────────────────┘
                                                                 │
                                                                 ▼
                                    ┌────────────────────────────────────────────────────────┐
                                    │          FastAPI Async Gateway & Middleware            │
                                    └────────────────────────────────────────────────────────┘
                                                                 │
                 ┌───────────────────────────────────────────────┼───────────────────────────────────────────────┐
                 ▼                                               ▼                                               ▼
┌─────────────────────────────────┐             ┌─────────────────────────────────┐             ┌─────────────────────────────────┐
│  1. Deterministic Rule Engine   │             │    2. Knowledge Graph Engine    │             │   3. Hybrid Retrieval RAG       │
│  (Python Math Calculator)       │             │    (Neo4j AuraDB Cloud)         │             │   (ChromaDB + BM25 + Qwen 3)    │
└─────────────────────────────────┘             └─────────────────────────────────┘             └─────────────────────────────────┘
  • Scheme 33(9) Cluster Redevelop.               • 208 Statutory Nodes                           • Sub-10ms BM25 Disk Index (.pkl)
  • Basic & Incentive FSI Caps                    • 244 Inter-clause Edges                        • Silent LLM / Dictionary Rewriter
  • Total Permissible BUA Math                    • Cross-reference dependencies                  • Grounded Qwen 3 reasoning traces
```

---

## 🔥 Key Technical Features

### ⚡ 1. Silent LLM & Dictionary Query Rewriter
* **0ms Static Mapping**: Instantly translates layman phrasing (*"metro station permissions"*) into formal DCPR terminology (*"Transit-Oriented Development under Regulation 33(2)"*) at $0 cost.
* **Non-Blocking Async Execution**: Built with `httpx.AsyncClient` and a 60-second Circuit Breaker to prevent thread starvation during model cold starts.

### 🎯 2. Code-Aware Hybrid Retrieval Engine
* **Statutory Token Preservation**: Custom regex tokenizer (`\b\d+(?:\(\d+\)|[\-\(][a-z\d]+\)?)*\b`) preserves alphanumeric codes like `Regulation 33(7)(A)` as unified tokens instead of splitting them.
* **Reciprocal Rank Fusion (RRF)**: Merges sparse BM25 keyword matching and dense ChromaDB vector embeddings with deterministic `hashlib.md5()` fingerprinting for multi-worker process stability.
* **Post-Fusion Cross-Encoder Re-Ranking**: Uses `ms-marco-MiniLM-L-6-v2` to select the top 5 most contextually relevant excerpts.

### 📊 3. Table-Preserving Ingestion Pipeline
* **Layout-Aware PDF Extraction**: Extracts complex numerical matrices into clean Markdown tables.
* **Functional Purpose Summarization**: Attaches operational summaries to table metadata so dense vector search locates tables by function rather than raw column headers.
* **Sliding-Window Aggregation**: Groups text paragraphs into optimal ~800–1,000 character windows to preserve complete statutory context.

---

## 🛠️ Tech Stack & Dependencies

* **Frontend**: React 18, TypeScript, Vite, TailwindCSS, Lucide Icons, Zustand.
* **Backend**: FastAPI, Python 3.13, Uvicorn, Pydantic v2.
* **Vector Database**: ChromaDB (`sentence-transformers/all-MiniLM-L6-v2`).
* **Sparse Retrieval**: BM25 (`rank_bm25`).
* **Graph Database**: Neo4j AuraDB (Bolt protocol) / NetworkX fallback.
* **Local LLM Engine**: Ollama (`qwen3:8b`).
* **Cross-Encoder**: `cross-encoder/ms-marco-MiniLM-L-6-v2`.

---

## 🚀 Getting Started

### Prerequisites
1. Install [Python 3.10+](https://www.python.org/).
2. Install [Node.js 18+](https://nodejs.org/).
3. Install [Ollama](https://ollama.ai/) and pull the Qwen 3 model:
   ```bash
   ollama pull qwen3:8b
   ```

---

### Installation & Local Setup

#### 1. Clone Repository
```bash
git clone https://github.com/abhijithwinddaa/DCPR.git
cd DCPR
```

#### 2. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows Powershell:
.\venv\Scripts\Activate.ps1
# Install dependencies:
pip install -r requirements.txt
```

#### 3. Frontend Setup
```bash
cd ../frontend
npm install
```

---

## 🏃 Execution Commands

Run the application across **3 terminal windows**:

#### Terminal 1: Ollama AI Engine
```bash
ollama run qwen3:8b
```

#### Terminal 2: FastAPI Backend Server
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```
* API Documentation: `http://localhost:8000/docs`

#### Terminal 3: React Frontend Client
```bash
cd frontend
npm run dev
```
* Web Application Dashboard: `http://localhost:5173`

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
