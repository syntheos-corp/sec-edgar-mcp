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

# OpenAI Agents SDK Configuration
# Server runs with HTTP transport (Streamable HTTP)
# Creates MCP endpoint at /mcp/ for OpenAI compatibility
# PORT is provided by Render (typically 10000)
# SEC_EDGAR_USER_AGENT must be set with your information

CMD ["python", "sec_edgar_mcp/server.py"]
