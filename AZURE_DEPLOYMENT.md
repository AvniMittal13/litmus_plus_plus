# Azure Deployment Instructions

## Environment Variables Configuration

After deploying to Azure Web App Service, you need to configure the following application settings in the Azure Portal:

1. Go to Azure Portal > App Services > litmusplusplus
2. Navigate to Configuration > Application settings
3. Add the following environment variables:

### Required Environment Variables:

```bash
# OpenAI Configuration
OPENAI_API_KEY=<your-openai-api-key>
OPENAI_BASE_URL=<your-openai-base-url>
OPENAI_API_TYPE=azure
OPENAI_API_VERSION=2024-12-01-preview
OPENAI_DEPLOYMENT_NAME=<your-deployment-name>
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Azure Configuration
AZURE_OPENAI_ENDPOINT_EMBEDDING=<your-azure-endpoint>
AZURE_OPENAI_API_KEY_EMBEDDING=<your-azure-api-key>
AZURE_PROJECT_ENDPOINT=<your-azure-project-endpoint>

# Firecrawl Configuration
FIRECRAWL_API_KEY=<your-firecrawl-api-key>

# Flask Configuration
FLASK_ENV=production

# Chroma Configuration
CHROMA_OPENAI_API_KEY=<your-chroma-api-key>

# Bing Search Configuration
BING_CONNECTION_NAME=<your-bing-connection-name>
```

## Deployment Process

1. Push code to the main branch
2. GitHub Actions will automatically build and deploy
3. Configure environment variables in Azure Portal
4. Restart the App Service

## Startup Command

The application uses `python startup.py` as the startup command, which:
- Loads environment variables
- Sets up proper Python path resolution
- Starts the Flask SocketIO application

## Port Configuration

The application automatically uses Azure's PORT environment variable for production deployment while defaulting to port 5000 for local development.
