# EcoAI Commerce Engine

## 🔹 Project Overview
EcoAI Commerce Engine is a production-ready AI-powered backend designed for sustainable B2B commerce. It automates catalog management, optimizes proposal generation, and enhances customer sustainability reporting using advanced LLM integration. Built with FastAPI and MongoDB, the system ensures high scalability and clear separation between AI orchestration and business logic grounding.

## 🔹 Implemented Modules

### Module 1: AI Auto-Category & Tag Generator
- **Purpose**: Automates the manual effort of product cataloging.
- **Features**: 
    - Auto-assigns primary categories from a predefined list.
    - Suggests sub-categories and generates 5-10 SEO-optimized tags.
    - Identifies sustainability filters (plastic-free, compostable, etc.).
    - Returns structured JSON and persists metadata to MongoDB.

### Module 2: AI B2B Proposal Generator
- **Purpose**: Generates budget-constrained sustainable product proposals.
- **Features**:
    - Suggests a sustainable product mix within a provided budget limit.
    - Provides detailed cost breakdowns and quantities.
    - Generates an impact positioning summary to justify the proposal.
    - Validates budget math to ensure allocations never exceed limits.

## 🔹 Architecture Overview

The system follows a clean, layered architecture to ensure maintainability and separation of concerns:

```text
Client (Web/Mobile)
  ↓ [POST /api/v1/ai/...]
FastAPI Routes (API Layer)
  ↓ [Validates Request Schema]
Controllers (Orchestration Layer)
  ↓ [Coordinates Service Calls]
AI Services (Logic Layer) —————→ MongoDB (Persistence)
  ↓ [Prompts LLM (Groq)]         • Prompt Logs
Groq LLM (OpenAI Compatible)     • Results (Auto-Category/Proposals)
```

## 🔹 AI Prompt Design Strategy

This project prioritizes **Reliability** and **Auditability** in AI operations:

- **Structured JSON Output**: Using OpenAI-compatible JSON modes to ensure the AI returns machine-readable data, eliminating expensive parsing errors and allowing direct integration with downstream business logic.
- **Validation Guards**: Every AI response is validated through Pydantic models and logic checks (e.g., budget math validation in Module 2) before storage. This prevents "AI hallucinations" from entering the production database.
- **Prompt Logging**: Every interaction is stored in the `prompt_logs` collection. This allows for prompt engineering debugging, cost auditing, and historical analysis of AI performance.
- **Business Logic Separation**: AI is used for *generation* and *reasoning*, while core business rules (like allowed category lists or math constraints) are maintained in the service layer, keeping the LLM properly grounded.

## 🔹 Architecture for Remaining Modules

According to the requirements, here is the architecture outline for the pending modules:

### Module 3: AI Impact Reporting Generator
- **Proposed Endpoint**: `POST /api/v1/ai/impact-report`
- **Proposed Flow**: `Client → Route → Controller → Service → AI → MongoDB`
- **Proposed Pydantic Models**: 
    - `ImpactReportRequest` (product_name, quantity, material, origin)
    - `ImpactReportResponse` (plastic_saved_kg, carbon_avoided_kg, statement)
- **Business Logic**:
    - `plastic_saved = quantity × avg_plastic_per_unit`
    - `carbon_avoided = plastic_saved × carbon_factor`
- **Storage**: `impact_reports` collection.

### Module 4: AI WhatsApp Support Bot
- **Proposed Endpoint**: `POST /api/v1/ai/support-bot`
- **Proposed Flow**: 
    1. **Classify Intent**: LLM identifies if the user wants `order_status`, `refund`, or `return_policy`.
    2. **Grounding**: If `order_status`, the service fetches data from the `orders` collection before the LLM generates a reply.
    3. **Escalation**: If `refund` or high-priority detected, the system flags `escalated: true`.
- **Storage**: `orders` and `support_conversations` collections.
- **Separation**: LLM handles natural language generation; Service layer handles database query security.

---

## 🔹 Setup & Run Instructions

1. **Prerequisites**: Python 3.10+, MongoDB running locally.
2. **Environment**:
    - `cp .env.example .env` (Add your `GROQ_API_KEY`)
3. **Installation**:
    ```bash
    cd backend
    python -m venv .venv
    source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```
4. **Execution**:
    ```bash
    uvicorn app.main:app --reload
    ```
    Access docs at: `http://127.0.0.1:8000/docs`
