# AI Travel Planner Architecture

## Overview

The project delivers a full-stack web application that simplifies travel planning with AI assistance. It comprises a Python-based backend, a browser client, and deployment artifacts (Docker, GitHub Actions) to satisfy the course requirements. Key goals:

- Capture travel intents through voice or text.
- Generate itineraries, budgets, and travel tips using a Large Language Model (LLM).
- Track expenses and manage multiple saved plans per authenticated user.
- Synchronize data via a cloud-capable REST API, enabling multi-device access.

## Technology Choices

- **Backend Framework**: FastAPI (Python 3.11). Chosen for async capabilities, modern tooling (Pydantic, dependency injection), and native OpenAPI docs.
- **Database**: SQLAlchemy ORM with Alembic migrations. Defaults to SQLite for local development; configurable for PostgreSQL/Supabase via environment variables (`DATABASE_URL`).
- **Authentication**: JWT-based session tokens, password hashing with `passlib`. Aligns with assignment’s requirement for login/registration without embedding credentials in code.
- **LLM Integration**: Abstracted `LLMClient` wrapping HTTP APIs (e.g., Alibaba DashScope, OpenAI). Runtime keys supplied via environment variables or runtime settings screen.
- **Speech Recognition**: Backend endpoint forwarding audio to configurable providers (e.g., iFlyTek Open Platform). The frontend also leverages the browser Web Speech API as a progressive enhancement.
- **Frontend**: Server-Rendered HTML (Jinja2) plus modular JavaScript (Alpine.js) for interactivity. This avoids heavy build tooling while keeping the stack Python-centric.
- **Mapping**: AMap (高德) JavaScript SDK rendered client-side. API key is provided by the user via the settings UI or `.env`.
- **Deployment**: Dockerfile builds complete stack. Optional GitHub Actions workflow builds and pushes the image to Alibaba Cloud Container Registry (ACR) when secrets are supplied.

## Backend Components

- `app/main.py`: FastAPI application factory, routing, middleware.
- `app/api/routes`: Versioned REST endpoints for auth, itineraries, expenses, speech, and configuration.
- `app/services`: Domain logic (planning, budgeting, llm, speech, mapping).
- `app/models`: SQLAlchemy ORM models (`User`, `TravelPlan`, `ItineraryItem`, `Expense`, `Preference`).
- `app/schemas`: Pydantic schemas mirroring API contracts.
- `app/core`: Config management, security utilities (JWT helpers), dependency wiring.
- `app/db`: Database session management and migrations.

## Frontend Modules

- `templates/index.html`: Main SPA-like shell showing map, itinerary timeline, expense ledger.
- `static/js/app.js`: Handles voice capture, API calls, renders responses, persists auth tokens.
- `static/css/style.css`: Tailwind-lite custom utility classes for consistent styling.
- `templates/settings.html`: Allows entering API keys (LLM, speech, maps) stored in browser localStorage and forwarded to backend when required.

## Data Flow

1. User authenticates via `/auth/register` and `/auth/login` (JWT).
2. Voice or text intent triggers `/speech/transcribe` (optional) followed by `/plans/generate`.
3. `PlanningService` calls `LLMClient` with normalized prompt to obtain itinerary and budget suggestions.
4. Response stored in database, returned to client. Map markers derived from itinerary items (geocoded via AMap API if keys present).
5. User manages expenses via `/expenses` endpoints; totals update in UI and DB.

## Configuration & Secrets

All API keys are provided at runtime via:

- `.env` file loaded by `pydantic-settings`.
- Docker environment variables.
- Frontend settings form (keys kept in browser storage, sent with requests when needed).

No secret is hardcoded or committed to source control.

## Future Enhancements

- Realtime collaboration (WebSocket updates).
- Push notifications for itinerary changes or travel advisories.
- Enhanced analytics dashboard for spending vs. plan projections.
