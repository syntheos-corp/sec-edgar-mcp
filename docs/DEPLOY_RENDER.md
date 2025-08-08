# Deploying SEC EDGAR MCP to Render

This guide explains how to deploy the SEC EDGAR MCP server to [Render](https://render.com) as a web service.

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
| `MCP_TRANSPORT` | `streamable-http` | **Required** - Enables HTTP transport for cloud deployment |
| `SEC_EDGAR_USER_AGENT` | `Your Name (your@email.com)` | **Required** - SEC requires identification |
| `PORT` | (auto-set by Render) | Render provides this automatically |

### 4. Deploy

1. Click "Create Web Service"
2. Render will build and deploy your service automatically
3. The deployment process takes 5-10 minutes
4. Once deployed, you'll receive a URL like `https://sec-edgar-mcp-xxxx.onrender.com`

## Verifying the Deployment

After deployment, your service will be accessible via HTTP. You can verify it's running by:

1. The Render dashboard shows "Live" status
2. The logs show: `Uvicorn running on http://0.0.0.0:<PORT>`
3. Visit the health check endpoint: `https://your-service-name.onrender.com/health`
   - Should return: `{"status": "healthy", "service": "SEC EDGAR MCP Server", "transport": "streamable-http", "version": "1.0.0-alpha"}`
4. The service responds to MCP protocol requests at the root path

## Using the Deployed Service

### With MCP Clients

Configure your MCP client to connect via HTTP:

```json
{
  "mcpServers": {
    "sec-edgar-mcp": {
      "url": "https://your-service-name.onrender.com",
      "transport": "streamable-http"
    }
  }
}
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
- Verify `MCP_TRANSPORT=streamable-http` is set in environment variables
- Check that `SEC_EDGAR_USER_AGENT` is properly formatted
- Review the logs for any error messages

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

- **Heroku**: Set `MCP_TRANSPORT=streamable-http` and deploy with Docker
- **Google Cloud Run**: Deploy as a containerized service
- **AWS App Runner**: Deploy with automatic scaling
- **Azure Container Apps**: Deploy with built-in load balancing

Each platform will provide a `PORT` environment variable that the server will use automatically.

## Support

For issues specific to:
- **SEC EDGAR MCP**: [GitHub Issues](https://github.com/stefanoamorelli/sec-edgar-mcp/issues)
- **Render Platform**: [Render Support](https://render.com/docs)
- **MCP Protocol**: [MCP Documentation](https://modelcontextprotocol.io)