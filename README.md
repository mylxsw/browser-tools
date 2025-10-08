# Browser Tools

A powerful FastAPI-based web service for document conversion and web scraping. Convert HTML/URLs to images, extract text from PDFs, and leverage AI to convert PDFs to markdown.

## Features

- 🖼️ **HTML/URL to Image**: Convert web pages and HTML content to high-quality PNG images
- 📄 **PDF Processing**: Extract text from PDFs or convert entire pages to images
- 🤖 **AI-Powered PDF to Markdown**: Use OpenAI models to intelligently convert PDFs to markdown format
- 🏥 **Health Monitoring**: Built-in health check endpoints for monitoring service status
- 🔄 **Async Processing**: Fast, non-blocking operations with proper resource management
- 📊 **Token Usage Tracking**: Monitor AI model usage and costs
- 🛡️ **Robust Error Handling**: Comprehensive error handling with detailed logging

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Chrome/Chromium browser (for HTML to image conversion)
- OpenAI API key (for PDF to markdown conversion)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/mylxsw/browser-scrape.git
   cd browser-scrape
   ```

2. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the service**
   ```bash
   # Using uv
   uv run python main.py
   
   # Or directly with uvicorn
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

The service will be available at `http://localhost:8000`

### Docker Setup

```bash
# Build and run with docker-compose
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f
```

## API Documentation

Once the service is running, visit `http://localhost:8000/docs` for interactive API documentation.

### Endpoints

#### Health Check
- `GET /v1/browser/health` - Service health status

#### Document Conversion
- `POST /v1/browser/pdf/to-image` - Convert PDF to PNG image
- `POST /v1/browser/pdf/to-text` - Extract text from PDF
- `POST /v1/browser/pdf/to-markdown` - Convert PDF to markdown using AI
- `POST /v1/browser/html/to-image` - Convert HTML/URL to PNG image

### Example Usage

#### Convert HTML to Image
```bash
curl -X POST "http://localhost:8000/v1/browser/html/to-image" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "html_or_url=https://example.com"
```

#### Convert PDF to Text
```bash
curl -X POST "http://localhost:8000/v1/browser/pdf/to-text" \
     -H "Content-Type: multipart/form-data" \
     -F "source_file=@document.pdf"
```

#### Convert PDF to Markdown (AI)
```bash
curl -X POST "http://localhost:8000/v1/browser/pdf/to-markdown" \
     -H "Content-Type: multipart/form-data" \
     -F "source_file=@document.pdf" \
     -F "maintainFormat=true"
```

## Configuration

Configure the service using environment variables in your `.env` file:

| Variable | Description | Default |
|----------|-------------|----------|
| `BROWSER_TOOLS_CORS_ENABLED` | Enable CORS | `false` |
| `BROWSER_TOOLS_DEBUG` | Enable debug mode | `false` |
| `BROWSER_TOOLS_LOG_JSON_MODE` | Use JSON logging format | `true` |
| `BROWSER_TOOLS_ZEROX_MODEL` | AI model for PDF conversion | `gpt-4o-mini` |
| `OPENAI_API_KEY` | OpenAI API key (required for PDF to markdown) | - |
| `OPENAI_BASE_URL` | OpenAI API endpoint | `https://api.openai.com/v1` |

## Architecture

The service follows a clean, layered architecture:

- **Infrastructure Layer** (`browser/core/`): Configuration management and global resources
- **Server Layer** (`browser/server/`): Core business logic and document processing
- **API Layer** (`browser/route/`): REST endpoints and request handling
- **Data Models** (`browser/schema/`): Pydantic models for request/response validation

### Key Features

- **Singleton Pattern**: Ensures single instances of configuration and infrastructure
- **Middleware Stack**: CORS, correlation ID tracking, request logging
- **Resource Management**: Automatic cleanup of temporary files
- **Error Handling**: Unified error responses with proper HTTP status codes
- **Logging**: Structured logging with correlation IDs for request tracing

## Development

### Running Tests

```bash
# Run tests (when available)
pytest
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Deployment

### Docker Production

```bash
# Build production image
docker build -t browser-tools .

# Run with environment file
docker run -d \
  --env-file .env \
  -p 8000:8000 \
  --name browser-tools \
  browser-tools
```

### Health Checks

The service includes built-in health checks at `/v1/health` for monitoring and orchestration.

## Troubleshooting

### Common Issues

1. **Chrome/Chromium not found**: Ensure Chrome or Chromium is installed and accessible
2. **PDF processing fails**: Check that system has sufficient memory and disk space
3. **AI conversion fails**: Verify OpenAI API key is valid and has sufficient credits

### Docker Issues

- For containerized environments, the service uses `--no-sandbox --disable-dev-shm-usage` flags for Chromium
- Ensure sufficient memory allocation for Docker containers when processing large documents

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**mylxsw** - [mylxsw@aicode.cc](mailto:mylxsw@aicode.cc)

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
- [html2image](https://github.com/vgalin/html2image) - HTML to image conversion
- [pypdfium2](https://github.com/pypdfium2-team/pypdfium2) - PDF processing
- [pyzerox](https://github.com/frozenbean/pyzerox) - AI-powered PDF to markdown conversion

---

⭐ If you find this project helpful, please give it a star on GitHub!