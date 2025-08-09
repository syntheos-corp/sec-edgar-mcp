# Deploying SEC EDGAR MCP to Render

This guide explains how to deploy the SEC EDGAR MCP server to [Render](https://render.com) with full OpenAI compatibility using HTTP transport (Streamable HTTP).

## Prerequisites

- A Render account ([sign up here](https://render.com))
- A GitHub account with the SEC EDGAR MCP repository forked or connected
- SEC EDGAR User Agent configured (your name and email)

## Deployment Steps

### 1. Create a New Web Service

1. Log into your [Render Dashboard](https://dashboard.render.com)
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository containing SEC EDGAR MCP
4. Select the repository and branch to deploy

### 2. Configure the Service

Fill in the following settings:

- **Name**: `sec-edgar-mcp` (or your preferred name)
- **Region**: Choose the closest region to you
- **Branch**: `main` (or your preferred branch)
- **Root Directory**: Leave blank (uses repository root)
- **Runtime**: Docker
- **Instance Type**: Free tier is sufficient for testing

### 3. Set Environment Variables

Add the following environment variables in the Render dashboard:

| Variable | Value | Description |
|----------|-------|-------------|
| `SEC_EDGAR_USER_AGENT` | `Your Name (your@email.com)` | **Required** - SEC requires identification |
| `MCP_TRANSPORT` | `http` (default) or `sse` | **Optional** - Transport protocol |
| `PORT` | (auto-set by Render) | Render provides this automatically (10000) |

### 4. Deploy

1. Click "Create Web Service"
2. Render will build and deploy your service automatically
3. The deployment process takes 5-10 minutes
4. Once deployed, you'll receive a URL like `https://sec-edgar-mcp-xxxx.onrender.com`

## Verifying the Deployment

After deployment, your service will be accessible via HTTP. You can verify it's running by:

1. The Render dashboard shows "Live" status
2. The logs show: `Starting SEC EDGAR MCP server with HTTP transport on 0.0.0.0:10000`
3. The logs show: `OpenAI Agents SDK endpoint: http://0.0.0.0:10000/mcp/`
4. The MCP endpoint is available at: `https://your-service-name.onrender.com/mcp/`

## Using the Deployed Service

### Method 1: OpenAI Agents SDK (Recommended)

The server uses HTTP transport (Streamable HTTP) for optimal compatibility:

```python
from openai_agents import Agent, MCPServerStreamableHttp

# Connect to your deployed server
# IMPORTANT: Include /mcp/ in the URL
server = MCPServerStreamableHttp(
    params={
        "url": "https://your-service-name.onrender.com/mcp/"
    }
)

# Create an agent with the MCP server
agent = Agent(
    name="SEC EDGAR Agent",
    model="gpt-4",
    mcp_servers=[server]
)

# The agent now has access to all SEC EDGAR tools
response = await agent.run("Get the latest 10-K filing for NVDA")
```

### Method 2: OpenAI Responses API

You can also use the MCP server directly with OpenAI's Responses API:

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-4",
    tools=[
        {
            "type": "mcp",
            "server_label": "sec_edgar",
            "server_url": "https://your-service-name.onrender.com/mcp/",
            "require_approval": "never"
        }
    ],
    input="What were NVIDIA's revenues in the latest 10-K?"
)
```

### Using SSE Transport (Alternative)

If you prefer SSE transport, set `MCP_TRANSPORT=sse` in Render environment variables:

```python
from openai_agents import Agent, MCPServerSse

# With SSE, no /mcp/ path is needed
server = MCPServerSse(
    params={
        "url": "https://your-service-name.onrender.com"
    }
)
```

### Security Considerations

For production use, consider:

1. **Authentication**: Add API key authentication to restrict access
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **CORS**: Configure CORS policies for browser-based clients
4. **Monitoring**: Set up logging and monitoring for usage tracking

## Troubleshooting

### Service Exits Immediately

If the service exits with "Application exited early":
- Check that `SEC_EDGAR_USER_AGENT` is properly formatted
- Ensure you're using the correct endpoint URL (include `/mcp/` for HTTP transport)
- Review the logs for any error messages

### Connection Issues

If OpenAI can't connect to your server:
- For HTTP transport: Ensure you're using the `/mcp/` endpoint
- For SSE transport: Use the root URL without `/mcp/`
- Verify the service is "Live" in Render dashboard

### Connection Refused

If clients can't connect:
- Ensure the service is showing as "Live" in Render dashboard
- Verify the URL is correct (including https://)
- Check that the client is configured for HTTP transport

### Module Import Errors

If you see import errors:
- Ensure all dependencies are in `pyproject.toml` or Dockerfile
- Verify the Dockerfile includes all required packages
- Check that `PYTHONPATH` is set correctly in Dockerfile

## Updating the Service

Render automatically redeploys when you push changes to the connected GitHub branch:

1. Make changes to your code
2. Commit and push to GitHub
3. Render detects the changes and redeploys automatically
4. Monitor the deployment in the Render dashboard

## Costs

- **Free Tier**: Limited to 750 hours/month, suitable for testing
- **Paid Plans**: Start at $7/month for always-on service
- **Scaling**: Can scale horizontally by increasing instances

## Alternative Deployment Options

If Render doesn't meet your needs, the same configuration works with:

- **Heroku**: Deploy with Docker and set `SEC_EDGAR_USER_AGENT`
- **Google Cloud Run**: Deploy as a containerized service with HTTP transport
- **AWS App Runner**: Deploy with automatic scaling and stateless HTTP
- **Azure Container Apps**: Deploy with built-in load balancing

Each platform will provide a `PORT` environment variable that the server uses automatically.

## Important Notes

1. **Endpoint URL**: When using HTTP transport (default), always include `/mcp/` in your URL
2. **Stateless HTTP**: The server uses `stateless_http=True` for OpenAI compatibility
3. **Transport Selection**: HTTP transport is recommended for better scalability and compatibility
4. **Authentication**: Consider adding authentication headers for production deployments

## Support

For issues specific to:
- **SEC EDGAR MCP**: [GitHub Issues](https://github.com/stefanoamorelli/sec-edgar-mcp/issues)
- **Render Platform**: [Render Support](https://render.com/docs)
- **MCP Protocol**: [MCP Documentation](https://modelcontextprotocol.io)