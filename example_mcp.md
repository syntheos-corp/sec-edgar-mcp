# MCP Server Implementation Guide
## Building Streamable-HTTP MCP Servers for Cloud Deployment

### Table of Contents
1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Project Setup](#project-setup)
4. [Creating Your MCP Server](#creating-your-mcp-server)
5. [Deployment to Render](#deployment-to-render)
6. [Testing & Integration](#testing--integration)
7. [Common Pitfalls & Solutions](#common-pitfalls--solutions)
8. [Best Practices](#best-practices)

---

## Introduction

### What is MCP?
The Model Context Protocol (MCP) is an open standard for connecting AI assistants to external tools and data sources. It provides a standardized way for AI models to interact with databases, APIs, and other services through a simple tool interface.

### Why Streamable-HTTP Transport?
- **Cloud-native**: Designed for deployment on platforms like Render, Heroku, or AWS
- **Stateless**: Perfect for horizontal scaling
- **Modern**: Replaces older SSE (Server-Sent Events) transport
- **Compatible**: Works seamlessly with OpenAI's Agents SDK and other AI platforms

### Architecture Overview
```
┌─────────────┐     HTTP/JSON-RPC    ┌──────────────┐
│   OpenAI    │◄────────────────────►│  MCP Server  │
│   Agent     │                      │(streamable)  │
└─────────────┘                      └──────┬───────┘
                                            │
                                     ┌──────▼───────┐
                                     │   Database   │
                                     │   or API     │
                                     └──────────────┘
```

---

## Prerequisites

### Required Knowledge
- Python 3.11+ basics
- Async/await concepts
- Basic understanding of REST APIs
- Docker fundamentals (for deployment)

### Development Environment
```bash
# Install Python 3.11+
python --version  # Should show 3.11 or higher

# Install required packages
pip install fastmcp>=2.11.0
pip install python-dotenv
pip install pydantic-settings

# For database integration (optional)
pip install asyncpg  # PostgreSQL
pip install redis    # Redis
```

---

## Project Setup

### 1. Create Project Structure
```
my-mcp-server/
├── server.py           # Main server file
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker configuration
├── render.yaml        # Render deployment config
├── .env.example       # Environment variables template
└── README.md          # Documentation
```

### 2. Create requirements.txt
```txt
# Core MCP Framework
fastmcp>=2.11.0

# Configuration
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0

# Optional: Database
asyncpg>=0.29.0  # For PostgreSQL

# Optional: Testing
aiohttp>=3.8.0
```

---

## Creating Your MCP Server

### Step 1: Basic Server Setup (server.py)

```python
"""
Minimal MCP Server with Streamable-HTTP Transport
"""

import os
import logging
from typing import Dict, Any
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("My MCP Server")

# Define your tools
@mcp.tool()
async def get_data(query: str) -> Dict[str, Any]:
    """
    Retrieve data based on a query.
    
    Args:
        query: Search query string
        
    Returns:
        Dictionary with results
    """
    # Your tool implementation here
    logger.info(f"Processing query: {query}")
    
    # Example response
    return {
        "success": True,
        "query": query,
        "results": ["Example result 1", "Example result 2"],
        "count": 2
    }


@mcp.tool()
async def process_data(
    data: str,
    operation: str = "analyze"
) -> Dict[str, Any]:
    """
    Process data with specified operation.
    
    Args:
        data: Input data to process
        operation: Type of operation (analyze, transform, validate)
        
    Returns:
        Processed results
    """
    logger.info(f"Processing data with operation: {operation}")
    
    return {
        "success": True,
        "operation": operation,
        "processed_data": f"Processed: {data[:100]}...",
        "metadata": {
            "length": len(data),
            "operation": operation
        }
    }


def main():
    """Main entry point for the server."""
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info("Starting MCP server with streamable-http transport")
    logger.info(f"Configuration: host={host}, port={port}")
    
    try:
        # Run with streamable-http transport
        # IMPORTANT: Don't pass 'path' parameter - let FastMCP handle it
        mcp.run(
            transport="streamable-http",
            host=host,
            port=port,
            log_level="info",
            stateless_http=True  # Critical for cloud deployment
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
```

### Step 2: Configuration Management (config.py)

```python
"""
Configuration management using Pydantic
"""

import os
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

class ServerConfig(BaseSettings):
    """Server configuration with validation."""
    
    # Server settings
    host: str = Field(
        default="0.0.0.0",
        description="Host to bind to"
    )
    
    port: int = Field(
        default=8000,
        description="Port to bind to"
    )
    
    @field_validator("port", mode="before")
    @classmethod
    def get_port(cls, v):
        """Get port from PORT environment variable (Render sets this)."""
        port_str = os.getenv("PORT", str(v or 8000))
        try:
            return int(port_str)
        except ValueError:
            return 8000
    
    # Optional: Database configuration
    database_url: str = Field(
        default="",
        description="Database connection string"
    )
    
    # Logging
    log_level: str = Field(
        default="info",
        description="Logging level"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### Step 3: Advanced Server with Database

```python
"""
Advanced MCP Server with Database Integration
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncpg
from fastmcp import FastMCP
from config import ServerConfig

logger = logging.getLogger(__name__)

# Initialize server
mcp = FastMCP("Advanced MCP Server")

# Global database pool
db_pool: Optional[asyncpg.Pool] = None


async def init_database(database_url: str):
    """Initialize database connection pool."""
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            database_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        
        # Create tables if needed
        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    data JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


@mcp.tool()
async def search_items(
    query: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search items in the database.
    
    Args:
        query: Search query
        limit: Maximum results to return
        
    Returns:
        Search results
    """
    global db_pool
    
    if not db_pool:
        return {"error": "Database not initialized"}
    
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, name, data, created_at
                FROM items
                WHERE name ILIKE $1
                LIMIT $2
            """, f"%{query}%", limit)
            
            results = [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "data": dict(row["data"]) if row["data"] else {},
                    "created_at": row["created_at"].isoformat()
                }
                for row in rows
            ]
            
            return {
                "success": True,
                "results": results,
                "count": len(results)
            }
            
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {"error": str(e)}


@mcp.tool()
async def add_item(
    name: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add a new item to the database.
    
    Args:
        name: Item name
        data: Item data as dictionary
        
    Returns:
        Created item with ID
    """
    global db_pool
    
    if not db_pool:
        return {"error": "Database not initialized"}
    
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO items (name, data)
                VALUES ($1, $2)
                RETURNING id, created_at
            """, name, data)
            
            return {
                "success": True,
                "id": row["id"],
                "name": name,
                "created_at": row["created_at"].isoformat()
            }
            
    except Exception as e:
        logger.error(f"Add item error: {e}")
        return {"error": str(e)}


def main():
    """Main entry point."""
    config = ServerConfig()
    
    # Initialize database if configured
    if config.database_url:
        import asyncio
        asyncio.run(init_database(config.database_url))
    
    logger.info("Starting Advanced MCP server")
    
    try:
        mcp.run(
            transport="streamable-http",
            host=config.host,
            port=config.port,
            log_level=config.log_level,
            stateless_http=True
        )
    finally:
        # Cleanup
        if db_pool:
            import asyncio
            asyncio.run(db_pool.close())


if __name__ == "__main__":
    main()
```

---

## Deployment to Render

### Step 1: Create Dockerfile

```dockerfile
# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (Render will override with PORT env var)
EXPOSE 8000

# Run the server
CMD ["python", "server.py"]
```

### Step 2: Create render.yaml

```yaml
services:
  - type: web
    name: my-mcp-server
    runtime: docker
    dockerfilePath: ./Dockerfile
    branch: main
    
    # Environment variables
    envVars:
      # Database (if needed)
      - key: DATABASE_URL
        sync: false  # Set manually in Render dashboard
      
      # Logging
      - key: LOG_LEVEL
        value: info
      
      # Optional: API authentication
      - key: API_KEY
        generateValue: true
    
    # Scaling
    scaling:
      minInstances: 1
      maxInstances: 3
      targetMemoryPercent: 80
      targetCPUPercent: 80
```

### Step 3: Deploy to Render

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial MCP server"
   git push origin main
   ```

2. **Connect to Render**
   - Go to [render.com](https://render.com)
   - Create new Web Service
   - Connect your GitHub repository
   - Render will auto-detect render.yaml

3. **Set Environment Variables**
   - DATABASE_URL (if using database)
   - Any API keys needed

4. **Deploy**
   - Render will automatically build and deploy
   - Your server will be available at: `https://your-server.onrender.com/mcp`

---

## Testing & Integration

### Local Testing

```python
# test_local.py
import asyncio
import aiohttp
import json

async def test_mcp_server():
    """Test MCP server locally."""
    url = "http://localhost:8000/mcp"
    
    # Test JSON-RPC call
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "get_data",
            "arguments": {"query": "test"}
        },
        "id": 1
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()
            print(f"Response: {json.dumps(result, indent=2)}")

asyncio.run(test_mcp_server())
```

### OpenAI Integration

```python
# openai_integration.py
import os
from openai import OpenAI

client = OpenAI()

# Create agent with MCP tools
agent = client.beta.assistants.create(
    model="gpt-4-turbo-preview",
    name="MCP Agent",
    instructions="You have access to custom tools via MCP.",
    tools=[
        {
            "type": "mcp",
            "mcp": {
                "server_url": "https://your-server.onrender.com/mcp",
                "require_approval": "never"
            }
        }
    ]
)

# Use the agent
thread = client.beta.threads.create()

message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="Search for 'example' in the database"
)

run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=agent.id
)

# Wait for completion and get response
# ... (see full example in openai_integration.py)
```

---

## Common Pitfalls & Solutions

### 1. PATH Environment Variable Issue
**Problem**: Server uses system PATH instead of MCP path  
**Solution**: Never pass `path` parameter to `mcp.run()` - let FastMCP handle it internally

```python
# ❌ WRONG - Don't do this
mcp.run(
    transport="streamable-http",
    host=host,
    port=port,
    path="/mcp"  # This can cause issues!
)

# ✅ CORRECT - Let FastMCP handle path
mcp.run(
    transport="streamable-http",
    host=host,
    port=port,
    stateless_http=True
)
```

### 2. Transport Confusion
**Problem**: Using wrong transport type  
**Solution**: Always use `streamable-http` for cloud deployment, not `http` or `sse`

```python
# ❌ WRONG - These are legacy/incorrect
transport="http"  # This becomes streamable-http anyway
transport="sse"   # Deprecated

# ✅ CORRECT
transport="streamable-http"
```

### 3. Missing stateless_http Parameter
**Problem**: Session management issues  
**Solution**: Always include `stateless_http=True` in run()

```python
# ✅ ALWAYS include for cloud deployment
mcp.run(
    transport="streamable-http",
    host=host,
    port=port,
    stateless_http=True  # Critical!
)
```

### 4. Port Configuration on Render
**Problem**: Server doesn't bind to correct port  
**Solution**: Read PORT from environment

```python
# Render sets PORT environment variable
port = int(os.getenv("PORT", "8000"))
```

### 5. Database Connection Issues
**Problem**: Database URL format incompatible  
**Solution**: Handle postgres:// to postgresql:// conversion

```python
database_url = os.getenv("DATABASE_URL", "")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
```

---

## Best Practices

### 1. Tool Design
- **Keep tools focused**: Each tool should do one thing well
- **Use clear names**: `search_documents` not `sd` or `doSearch`
- **Document thoroughly**: Include examples in docstrings
- **Validate inputs**: Use type hints and validation

```python
@mcp.tool()
async def search_documents(
    query: str,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Search documents with pagination.
    
    Args:
        query: Search query string
        limit: Maximum results (1-100)
        offset: Skip first N results
        
    Returns:
        Dictionary with 'results' and 'total_count'
        
    Example:
        search_documents("machine learning", limit=5)
    """
    # Validate inputs
    limit = max(1, min(100, limit))
    offset = max(0, offset)
    
    # ... implementation
```

### 2. Error Handling
- **Always return structured responses**
- **Include success/error indicators**
- **Log errors for debugging**

```python
@mcp.tool()
async def process_data(data: str) -> Dict[str, Any]:
    try:
        # Process data
        result = await do_processing(data)
        return {
            "success": True,
            "result": result
        }
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return {
            "success": False,
            "error": f"Invalid input: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "success": False,
            "error": "Internal server error"
        }
```

### 3. Security Considerations
- **Never expose sensitive data in responses**
- **Validate and sanitize all inputs**
- **Use environment variables for secrets**
- **Implement rate limiting if needed**

```python
# Use environment variables for sensitive data
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable required")

# Don't log sensitive data
logger.info(f"Connecting to service...")  # Don't log API_KEY!
```

### 4. Performance Optimization
- **Use connection pooling for databases**
- **Implement caching where appropriate**
- **Keep responses concise**
- **Use async/await properly**

```python
# Connection pooling
db_pool = await asyncpg.create_pool(
    database_url,
    min_size=5,
    max_size=20
)

# Caching example
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_cached_data(key: str):
    # Expensive operation cached
    return await fetch_from_database(key)
```

### 5. Monitoring & Logging
- **Log server startup and configuration**
- **Log tool invocations**
- **Monitor error rates**
- **Track response times**

```python
import time

@mcp.tool()
async def timed_operation(param: str) -> Dict[str, Any]:
    start = time.time()
    
    try:
        result = await do_operation(param)
        elapsed = time.time() - start
        
        logger.info(f"Operation completed in {elapsed:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": elapsed
        }
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"Operation failed after {elapsed:.2f}s: {e}")
        raise
```

---

## Troubleshooting

### Server Won't Start
1. Check Python version (3.11+ required)
2. Verify all dependencies installed
3. Check environment variables
4. Look for port conflicts

### Can't Connect from OpenAI
1. Verify server is publicly accessible
2. Check URL format: `https://your-server.onrender.com/mcp`
3. Test with curl first
4. Check server logs on Render

### Tools Not Working
1. Verify tool decorators (`@mcp.tool()`)
2. Check async/await usage
3. Validate return types
4. Review error messages in logs

### Debugging Tips
```python
# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Add debug endpoints
@mcp.tool()
async def debug_echo(message: str) -> Dict[str, Any]:
    """Echo back the message for testing."""
    return {"echo": message, "timestamp": datetime.now().isoformat()}

# Log all tool calls
@mcp.tool()
async def wrapped_tool(param: str) -> Dict[str, Any]:
    logger.debug(f"Tool called with: {param}")
    result = await actual_tool(param)
    logger.debug(f"Tool returned: {result}")
    return result
```

---

## Conclusion

Building MCP servers with streamable-http transport is straightforward when you follow these patterns:

1. **Use FastMCP** with `transport="streamable-http"`
2. **Always include** `stateless_http=True`
3. **Never pass** the `path` parameter
4. **Deploy to Render** with Docker
5. **Test thoroughly** before production

This guide should help you avoid common pitfalls and build robust MCP servers that integrate seamlessly with AI platforms like OpenAI.

For more examples and updates, check:
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Specification](https://modelcontextprotocol.io)
- [OpenAI Agents Documentation](https://platform.openai.com/docs/agents)

---

## Quick Reference

### Minimal Server Template
```python
from fastmcp import FastMCP
import os

mcp = FastMCP("My Server")

@mcp.tool()
async def my_tool(param: str) -> dict:
    return {"result": f"Processed: {param}"}

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        stateless_http=True
    )
```

### Essential Files Checklist
- [ ] server.py - Main server code
- [ ] requirements.txt - Dependencies
- [ ] Dockerfile - Container configuration  
- [ ] render.yaml - Deployment configuration
- [ ] .gitignore - Exclude .env, __pycache__, etc.
- [ ] README.md - Documentation

### Deployment Checklist
- [ ] Code pushed to GitHub
- [ ] Render service created
- [ ] Environment variables set
- [ ] Deployment successful
- [ ] Test endpoint accessible
- [ ] OpenAI integration tested

Happy building! 🚀