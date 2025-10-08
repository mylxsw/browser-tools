# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Browser Tools is a FastAPI-based web service that provides document conversion and web scraping capabilities. The service offers REST APIs for:
- Converting HTML/URLs to images
- Converting PDFs to images, text, or markdown (using AI)
- Health checking endpoints

## Development Environment Setup

### Prerequisites
- Python 3.12+
- uv (for dependency management)
- Chrome/Chromium browser
- OpenAI API key (for PDF to markdown conversion)

### Local Development Commands

```bash
# Install dependencies
uv sync

# Run the development server
uv run python main.py

# Run with uvicorn directly
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Environment setup
cp .env.example .env
# Edit .env with your configuration
```

### Docker Development

```bash
# Build and run with docker-compose
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Architecture Overview

### Core Components

**Infrastructure Layer (`browser/core/`)**
- `Infra`: Singleton class managing global resources (database, config, models)
- `Config`: Environment-based configuration management with .env support
- Global exception handling and structured logging (JSON/colored output)

**Server Layer (`browser/server/`)**
- `BrowserServer`: Main service class handling all conversion operations
- Uses `Html2Image` for HTML/URL to image conversion
- Uses `pypdfium2` for PDF text extraction and image conversion
- Integrates `pyzerox` for AI-powered PDF to markdown conversion

**API Layer (`browser/route/`)**
- `converter.py`: Main conversion endpoints (PDF/HTML processing)
- `healthcheck.py`: Service health monitoring
- `route.py`: Router registration and URL prefix management

**Data Models (`browser/schema/`)**
- Pydantic models for request/response validation
- `ImageResponse`, `TextResponse`, `TextWithTokenUsageResponse`
- Token usage tracking for AI operations

### Key Architectural Patterns

**Singleton Pattern**: Config and Infra classes use singleton decorator to ensure single instances
**Middleware Stack**: CORS, correlation ID tracking, request logging
**Error Handling**: Custom business/internal error types with unified JSON responses
**Resource Management**: Automatic cleanup of temporary files using context managers

## Configuration

Environment variables (see `.env.example`):
- `BROWSER_TOOLS_CORS_ENABLED`: Enable CORS (default: false)
- `BROWSER_TOOLS_DEBUG`: Debug mode (default: false)
- `BROWSER_TOOLS_LOG_JSON_MODE`: JSON logging (default: true)
- `BROWSER_TOOLS_ZEROX_MODEL`: AI model for PDF conversion (default: gpt-4o-mini)
- `OPENAI_API_KEY`: Required for PDF to markdown conversion
- `OPENAI_BASE_URL`: OpenAI API endpoint (default: https://api.openai.com/v1)

## API Endpoints

### Health Check
- `GET /v1/browser/health` - Service health status

### Document Conversion
- `POST /v1/browser/pdf/to-image` - Convert PDF to PNG image
- `POST /v1/browser/pdf/to-text` - Extract text from PDF
- `POST /v1/browser/pdf/to-markdown` - Convert PDF to markdown using AI
- `POST /v1/browser/html/to-image` - Convert HTML/URL to PNG image

All endpoints return JSON with `success` boolean and appropriate data/error messages.

## Development Notes

### File Management
- Temporary files are automatically created with UUID-based naming
- Files are cleaned up using context managers in route handlers
- Server includes cleanup methods for old temporary files

### Error Handling Strategy
- All API responses use 200 status code with `success` field
- Custom `BusinessError` for user-facing errors
- Custom `InternalError` for server-side issues
- Global exception handlers ensure consistent error responses

### Logging
- Request correlation IDs for tracing
- Structured logging with user/org context
- Configurable JSON or colored console output
- Request timing and status code logging

### AI Integration
- PDF to markdown uses `pyzerox` library
- Configurable AI model selection
- Token usage tracking and reporting
- Async processing for AI operations

## Docker Considerations

The Dockerfile uses `ghcr.io/astral-sh/uv:python3.12-bookworm` base image and includes:
- Chromium browser for HTML rendering
- GraphicsMagick for image processing
- Poppler utilities for PDF handling
- Custom Chromium flags for containerized execution (`--no-sandbox --disable-dev-shm-usage`)

Health check endpoint is configured for container orchestration at `/v1/browser/health`.