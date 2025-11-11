# Talk-to-Plot AI

**LLM-Powered Data Visualization Platform**

Talk-to-Plot AI is a full-stack application that enables users to interact with tabular data through natural language. It uses OpenAI's GPT model to translate conversational prompts into validated, structured data queries and renders the results as dynamic charts.

---

## 🚀 Features

* **Natural Language to Visualization:** Type your question about a dataset and instantly receive an AI-generated chart.
* **Full-Stack Orchestration:** Unified architecture using **Turborepo** to manage FastAPI (backend) and Vite/React (frontend) workspaces.
* **Validated Data Pipeline:** Uses **pandas** and defensive validation to ensure safe and deterministic data transformations.
* **Dynamic Chart Rendering:** Frontend powered by **Recharts**, **React 18**, and **Vite** with heuristic chart-type inference.
* **Secure Configuration:** Environment variables control API keys, dataset paths, and exception handling.

---

## 🧱 Architecture Overview

### Monorepo Setup (Turborepo)

* **Root workspace** orchestrates the backend and frontend builds via `turbo.json`.
* Shared tasks for `dev`, `build`, and `lint` ensure consistent CI/CD workflows.

### Backend — FastAPI

* Located in `apps/backend/`.
* Exposes a single `/chat` endpoint that:

  1. Sends the user prompt to **OpenAI GPT-4o-mini**.
  2. Parses the model's JSON response.
  3. Loads and validates the Excel dataset.
  4. Aggregates data using `pandas` and returns structured results.
* Defensive error handling for malformed AI outputs, user input issues, and dataset misconfigurations.

### Frontend — React + Vite

* Located in `apps/frontend/`.
* Renders the AI output using **Recharts** components.
* Automatically infers chart types and axis bindings.
* REST requests managed through `api.js` using Axios.
* Provides intuitive chat interface and real-time feedback.

---

## ⚙️ Environment Setup

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
DATA_SOURCE_PATH=./data/sample.xlsx
EXCEPTION_COLUMNS=Notes,Comments
```

### Prerequisites

* Node.js 18+
* Python 3.10+
* npm or yarn

### Installation

```bash
git clone https://github.com/yourusername/talk-to-plot-ai.git
cd talk-to-plot-ai
npm install
cd apps/backend && pip install -r requirements.txt
```

### Development

Run backend and frontend in parallel:

```bash
npm run dev:backend  # FastAPI via Uvicorn
npm --prefix apps/frontend run dev  # Vite React app
```

---

## 🧩 Data Processing Pipeline

1. **Prompt Parsing:** Extracts chart metadata from OpenAI response.
2. **Validation:** Confirms valid numeric columns using `_validate_columns()`.
3. **Aggregation:** Executes aggregators (`_aggregate_raw_records`, `_aggregate_non_zero_count`, etc.) depending on LLM directives.
4. **Caching:** Uses `lru_cache` to keep dataset in memory between requests.
5. **Response:** Returns clean, JSON-structured chart-ready data to frontend.

---

## 🖥️ Frontend Experience

* **Chat Interface:** Managed by `ChatBox.jsx`, handles user input and loading state.
* **Plot Rendering:** `PlotView.jsx` displays charts with gradients, legends, and tooltips.
* **Error Transparency:** Backend error messages surfaced directly to the UI.

---
