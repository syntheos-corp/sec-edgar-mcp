FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Ensure local package is discoverable
ENV PYTHONPATH=/app

# Default to stdio transport for local usage
ENV MCP_TRANSPORT=stdio

# For cloud deployments (Render, Heroku, etc.):
# Set MCP_TRANSPORT=streamable-http
# The PORT environment variable will be automatically provided by the platform

# Example configurations:
# 
# Local MCP client (stdio transport):
# "mcpServers": {
#   "sec-edgar-mcp": {
#     "command": "docker",
#     "args": [
#       "run",
#       "--rm",
#       "-i",
#       "-e", "SEC_EDGAR_USER_AGENT=<First Name, Last name (your@email.com)>",
#       "stefanoamorelli/sec-edgar-mcp:latest"
#     ]
#   }
# }
#
# For HTTP deployment on cloud platforms:
# Set environment variables:
# - MCP_TRANSPORT=streamable-http
# - PORT=<provided by platform>
# - SEC_EDGAR_USER_AGENT=<First Name, Last name (your@email.com)>

CMD ["python", "sec_edgar_mcp/server.py"]
