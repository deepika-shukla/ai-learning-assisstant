# 🎓 AI Learning Assistant v2

> **A production-ready, multi-agent AI learning platform built with LangGraph, FastAPI, and external API integrations.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange.svg)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

![Architecture](https://img.shields.io/badge/Architecture-Multi--Agent-purple)
![APIs](https://img.shields.io/badge/APIs-YouTube%20%7C%20Wikipedia%20%7C%20GitHub-red)
![Auth](https://img.shields.io/badge/Auth-JWT-brightgreen)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Interview Guide](#-interview-guide)
- [Contributing](#-contributing)

---

## 🌟 Overview

AI Learning Assistant is a comprehensive learning platform that creates **personalized learning curriculums** for any topic. It uses a **multi-agent architecture** powered by LangGraph to handle different aspects of the learning experience.

### What Makes This Project Special?

| Feature | Implementation |
|---------|---------------|
| **Multi-Agent System** | 12 specialized agents (router, curriculum, quiz, resources, etc.) |
| **External APIs** | YouTube videos, Wikipedia summaries, GitHub repos |
| **REST API** | FastAPI with JWT authentication, versioned endpoints |
| **Persistence** | SQLite with session restoration |
| **Human-in-the-Loop** | Curriculum confirmation before starting |
| **Testing** | 50+ unit/integration tests with pytest |
| **CI/CD** | GitHub Actions pipeline |
| **Deployment** | Docker + Docker Compose ready |

---

## ✨ Features

### 🤖 Multi-Agent Architecture
```
User Input → Router (NLP) → Specialized Agent → Response
                ↓
   ┌───────────┼───────────┐
   ↓           ↓           ↓
Curriculum   Quiz      Resources
  Agent     Agent       Agent
```

### 📚 Learning Features
- **Custom Curriculums**: AI-generated learning plans for any topic
- **Daily Tasks**: Actionable todo lists for each day
- **Quizzes**: Knowledge-check assessments with explanations
- **Progress Tracking**: Visual progress with achievements
- **Q&A**: Ask questions about your learning topic

### 🌐 External Content Integration
- **YouTube**: Tutorial video recommendations
- **Wikipedia**: Topic summaries and related concepts
- **GitHub**: Relevant code repositories and examples

### 🔐 API Features
- **JWT Authentication**: Secure user sessions
- **RESTful Design**: Proper HTTP methods and status codes
- **Versioned Endpoints**: `/api/v1/` prefix for future compatibility
- **Swagger Docs**: Interactive API documentation at `/docs`

---

## 🏗 Architecture

### System Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
├──────────────┬──────────────┬──────────────────────────────────┤
│   CLI App    │ Streamlit GUI │        FastAPI (REST)            │
│  (main.py)   │   (app.py)   │        (api/main.py)             │
└──────┬───────┴──────┬───────┴──────────────┬───────────────────┘
       │              │                       │
       └──────────────┼───────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                      LANGGRAPH CORE                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┐                                                     │
│  │ Router  │──┬──→ Curriculum Agent ──→ Creates learning plans │
│  │ (NLP)   │  │                                                  │
│  └─────────┘  ├──→ Quiz Agent ────────→ Generates assessments   │
│               ├──→ Resources Agent ───→ Fetches external content│
│               ├──→ Progress Agent ────→ Tracks achievements     │
│               ├──→ Q&A Agent ─────────→ Answers questions       │
│               └──→ Todo Agent ────────→ Daily task breakdown    │
└─────────────────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                     EXTERNAL SERVICES                            │
├──────────────┬──────────────┬───────────────────────────────────┤
│  YouTube API │ Wikipedia API │         GitHub API                │
│  (videos)    │  (summaries)  │         (repos)                   │
└──────────────┴──────────────┴───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                      DATA LAYER                                  │
├─────────────────────────────────────────────────────────────────┤
│  SQLite Database │ LangGraph Checkpointer │ User Sessions        │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Flow
```
START
  │
  ▼
┌─────────────┐
│   Router    │◄─── LLM-based intent classification
│   Agent     │     (handles typos, variations)
└──────┬──────┘
       │
       ├──────────────────────────────────────┐
       │                                      │
       ▼                                      ▼
┌─────────────┐                        ┌─────────────┐
│ Curriculum  │                        │   Quiz      │
│   Agent     │                        │   Agent     │
└──────┬──────┘                        └──────┬──────┘
       │                                      │
       ▼                                      ▼
┌─────────────┐                        ┌─────────────┐
│  Confirm    │◄── Human-in-the-loop   │   Grader    │
│   Agent     │                        │   Agent     │
└──────┬──────┘                        └─────────────┘
       │
       ▼
     END
```

---

## 🛠 Tech Stack

| Category | Technology |
|----------|------------|
| **AI Framework** | LangGraph, LangChain |
| **LLM** | OpenAI GPT-4o-mini |
| **API Framework** | FastAPI |
| **Web GUI** | Streamlit |
| **Database** | SQLite |
| **Authentication** | JWT (python-jose) |
| **External APIs** | YouTube, Wikipedia, GitHub |
| **Testing** | pytest, pytest-cov |
| **CI/CD** | GitHub Actions |
| **Containerization** | Docker, Docker Compose |
| **Type Checking** | Pydantic, TypedDict |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API Key

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/ai-learning-assistant.git
cd ai-learning-assistant

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Running the Application

#### Option 1: CLI Interface
```bash
python -m main
```

#### Option 2: Streamlit GUI
```bash
streamlit run app.py
```

#### Option 3: FastAPI Server
```bash
uvicorn api.main:app --reload
# API docs at: http://localhost:8000/docs
```

#### Option 4: Docker
```bash
docker-compose up
# API at: http://localhost:8000
# GUI at: http://localhost:8501
```

---

## 📖 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "email": "user@example.com", "password": "password123"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password123"}'
```

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login and get JWT |
| GET | `/auth/me` | Get current user |
| POST | `/courses` | Create learning course |
| GET | `/courses` | List user's courses |
| GET | `/courses/{id}` | Get course details |
| POST | `/chat` | Send message to AI |
| GET | `/courses/{id}/resources` | Get learning resources |
| POST | `/courses/{id}/quiz` | Generate quiz |
| GET | `/courses/{id}/progress` | Get progress |

### Example: Create a Course
```bash
curl -X POST http://localhost:8000/api/v1/courses \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Python Programming",
    "duration_days": 7,
    "skill_level": "beginner"
  }'
```

---

## 📁 Project Structure

```
ai-learning-assistant/
├── 📦 Core Application
│   ├── state.py              # State definitions (TypedDict)
│   ├── agents.py             # 12 specialized agents
│   ├── graph.py              # LangGraph workflow
│   ├── main.py               # CLI interface
│   └── app.py                # Streamlit GUI
│
├── 🌐 External Services
│   └── services/
│       ├── youtube_service.py
│       ├── wikipedia_service.py
│       └── github_service.py
│
├── 🔌 REST API
│   └── api/
│       ├── main.py           # FastAPI application
│       ├── models.py         # Pydantic schemas
│       ├── auth.py           # JWT authentication
│       └── database.py       # Database operations
│
├── 🧪 Tests
│   └── tests/
│       ├── conftest.py       # Fixtures
│       ├── test_agents.py    # Agent tests
│       ├── test_graph.py     # Integration tests
│       ├── test_api.py       # API tests
│       └── test_services.py  # Service tests
│
├── ⚙️ Configuration
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── .env.example
│   └── .gitignore
│
├── 🐳 Deployment
│   ├── Dockerfile
│   └── docker-compose.yml
│
└── 🔄 CI/CD
    └── .github/workflows/ci.yml
```

---

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Specific Tests
```bash
# Agent tests
pytest tests/test_agents.py -v

# API tests
pytest tests/test_api.py -v

# Integration tests
pytest tests/test_graph.py -v
```

### Test Categories
| File | Coverage | Description |
|------|----------|-------------|
| test_agents.py | Agents | Unit tests for all 12 agents |
| test_graph.py | Graph | LangGraph workflow tests |
| test_api.py | API | FastAPI endpoint tests |
| test_services.py | Services | External API integration tests |

---

## 🚢 Deployment

### Docker Deployment
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Manual Deployment
```bash
# API Server
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Streamlit
streamlit run app.py --server.port 8501
```

### Environment Variables (Production)
```bash
OPENAI_API_KEY=sk-...
JWT_SECRET_KEY=<secure-random-string>
DATABASE_URL=postgresql://user:pass@host/db
ENVIRONMENT=production
DEBUG=false
```

---

## 🎤 Interview Guide

### Key Talking Points

1. **Architecture Decision**
   > "I chose a multi-agent architecture because learning has distinct phases - planning, execution, assessment. Each agent specializes in one task, following the Single Responsibility Principle."

2. **Why LangGraph?**
   > "LangGraph provides stateful, cyclic workflows with persistence. Unlike simple chains, I needed conditional routing based on user intent and the ability to resume sessions."

3. **External API Integration**
   > "I integrated YouTube, Wikipedia, and GitHub to provide comprehensive learning resources. The services are designed with fallbacks - if an API fails, users still get curated content."

4. **Testing Strategy**
   > "I implemented unit tests for agents, integration tests for the graph, and API tests for endpoints. Mocking the LLM ensures tests are fast and deterministic."

### Common Questions

**Q: How does the router handle typos?**
> "The router uses LLM-based intent classification instead of keyword matching. The LLM understands context and can interpret 'shwo progrss' as 'show_progress'."

**Q: How do you handle state persistence?**
> "LangGraph's SqliteSaver checkpointer automatically persists state after each node execution. Users can restore sessions using their thread_id."

**Q: What's your testing approach?**
> "I mock the LLM calls to ensure deterministic tests. The conftest.py provides fixtures for different state configurations. I aim for 70%+ coverage."

---

## 📊 Project Stats

| Metric | Value |
|--------|-------|
| Lines of Code | ~3,500 |
| Agents | 12 |
| API Endpoints | 15+ |
| Test Cases | 50+ |
| External APIs | 3 |
| Documentation | Comprehensive |

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) - Stateful AI workflows
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [OpenAI](https://openai.com/) - GPT models
- [Streamlit](https://streamlit.io/) - Data app framework

---

**Built with ❤️ by [Your Name]**
