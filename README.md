# Litmus Agent System

A sophisticated multi-agent system built with AutoGen, featuring both command-line and web-based interfaces for intelligent query processing and analysis.

## 🏗️ Project Structure

```
litmus/
├── agents/                     # Core agent implementations
│   ├── main_agent.py          # Primary orchestration agent
│   ├── thought_agent.py       # Specialized thought processing agent
│   ├── custom_agents/         # Custom agent implementations
│   ├── prompts/              # Agent prompt templates
│   └── tools/                # Agent tools and utilities
├── web_interface/            # Flask web application
│   ├── app.py               # Main Flask application
│   ├── services/            # Web service layer
│   ├── templates/           # HTML templates
│   ├── static/              # CSS, JS, images
│   └── agents_enhanced/     # Enhanced web-specific agents
├── knowledge/               # Knowledge base and documents
├── utils/                   # Utility functions and helpers
├── tmp/                     # Temporary files and database
├── entry.py                # CLI entry point for main agent
├── entry_thought.py        # CLI entry point for thought agent
└── startup.py              # Production startup script
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Git
- Azure OpenAI API access
- Firecrawl API key (optional, for web scraping)

### 1. Environment Setup

**Clone and navigate to the project:**
```bash
git clone <repository-url>
cd litmus
```

**Create and activate virtual environment:**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

### 2. Configuration

**Create environment file:**
```bash
cp .env.example .env  # If example exists, or create new .env
```

**Required environment variables in `.env`:**
```env
# OpenAI Configuration
OPENAI_API_KEY=your_azure_openai_api_key
OPENAI_BASE_URL=https://your-resource.openai.azure.com/
OPENAI_API_TYPE=azure
OPENAI_API_VERSION=2024-12-01-preview
OPENAI_DEPLOYMENT_NAME=your_deployment_name

# Azure Configuration
AZURE_OPENAI_ENDPOINT_EMBEDDING=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY_EMBEDDING=your_embedding_api_key

# Optional: Firecrawl for web scraping
FIRECRAWL_API_KEY=your_firecrawl_api_key

# ChromaDB Configuration
CHROMA_OPENAI_API_KEY=your_chroma_api_key
```

## 🖥️ Running the Application

### Web Interface (Recommended)

**Start the Flask web application:**
```bash
python web_interface/app.py
```

**Access the application:**
- Open your browser to: `http://localhost:5000`
- Features:
  - Real-time chat interface
  - Multi-session support
  - Enhanced agent responses
  - File upload capabilities
  - Session management

**Production deployment:**
```bash
python startup.py
```

### Command Line Interface

**Run the Main Agent:**
```bash
python entry.py
```
- Primary orchestration agent
- Handles complex multi-step queries
- Coordinates between different specialized agents
- Best for comprehensive analysis tasks

**Run the Thought Agent:**
```bash
python entry_thought.py
```
- Specialized for deep thinking and reasoning
- Focused on analytical and philosophical queries
- Ideal for research and reflection tasks

**Interactive usage:**
```
Enter your query: What are the latest trends in AI research?
Processing your query...

Response:
[Agent provides detailed analysis...]

Enter your query: exit  # To quit
```

## 🔧 Key Components

### Agents

- **MainAgent**: Primary orchestration agent that coordinates tasks
- **ThoughtAgent**: Specialized for deep analysis and reasoning
- **Custom Agents**: Domain-specific agents in `agents/custom_agents/`

### Web Interface Features

- **Real-time Communication**: WebSocket-based chat interface
- **Session Management**: Multiple concurrent user sessions
- **Enhanced Responses**: Rich formatting and interactive elements
- **Agent Selection**: Choose between different agent types
- **File Handling**: Upload and process documents

### Database & Storage

- **ChromaDB**: Vector database for knowledge storage and retrieval
- **SQLite**: Embedded database for session and metadata storage
- **File Storage**: Local file system for temporary and uploaded files

## 🛠️ Development

### Local Development Setup

**Install development dependencies:**
```bash
pip install -r requirements.txt
```

**Run in development mode:**
```bash
# Web interface with debug mode
FLASK_ENV=development python web_interface/app.py

# CLI agents with verbose logging
python entry.py --verbose
```

### Testing

**Run application tests:**
```bash
python web_interface/test_setup.py
```

**Verify ChromaDB setup:**
```bash
python web_interface/initialize_chroma.py
```

## 🌐 Deployment

### Azure App Service

**Using GitHub Actions (automated):**
1. Push to main branch triggers deployment
2. GitHub Actions builds and deploys automatically
3. Configure environment variables in Azure Portal

**Manual deployment:**
```bash
# Using Azure CLI
az webapp up --name your-app-name --resource-group your-rg
```

### Docker Deployment

**Build and run container:**
```bash
docker build -t litmus-agent .
docker run -p 5000:5000 --env-file .env litmus-agent
```

## 📋 Configuration Options

### Agent Behavior

Customize agent behavior by modifying:
- `agents/prompts/`: Agent prompt templates
- `agents/tools/`: Available tools and functions
- Environment variables for model selection

### Web Interface

Configure web interface in `web_interface/app.py`:
- Port settings
- CORS configuration
- Session timeout
- File upload limits

### Database

ChromaDB configuration:
- Database path: `./tmp/db` (default)
- Collection settings in `web_interface/initialize_chroma.py`
- Embedding model configuration

## 🔍 Troubleshooting

### Common Issues

**SQLite Version Error (ChromaDB):**
```bash
# Install compatible SQLite
pip install pysqlite3-binary>=0.5.2
```

**Import Errors:**
```bash
# Ensure virtual environment is activated
# Check Python path in entry scripts
```

**API Key Issues:**
```bash
# Verify .env file exists and contains valid keys
# Check Azure OpenAI endpoint URLs
```

**Port Conflicts:**
```bash
# Change port in app.py or use environment variable
export PORT=8000
python web_interface/app.py
```

### Debug Mode

**Enable verbose logging:**
```bash
# Set environment variable
export FLASK_ENV=development
export DEBUG=True

# Or modify app.py directly
debug_mode = True
```
---

**Happy coding with Litmus Agent System! 🚀**
