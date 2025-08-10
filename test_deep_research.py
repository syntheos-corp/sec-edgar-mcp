#!/usr/bin/env python3
"""
Test script for Deep Research tools integration.

This script tests the search and fetch tools that are compatible
with OpenAI Deep Research.
"""

import asyncio
import json
from sec_edgar_mcp.tools.deep_research import deep_research_tools


async def test_search():
    """Test the search tool with various queries."""
    print("=" * 60)
    print("Testing Search Tool")
    print("=" * 60)
    
    test_queries = [
        ("NVDA", ["companies", "filings"], 5),
        ("Apple 10-K", None, 3),
        ("insider trading", ["filings"], 5),
        ("TSLA", ["companies"], 2),
    ]
    
    for query, data_types, top_k in test_queries:
        print(f"\nSearching for: '{query}'")
        print(f"Data types: {data_types}, Top-k: {top_k}")
        print("-" * 40)
        
        result = deep_research_tools.search(
            query=query,
            data_types=data_types,
            top_k=top_k,
            date_range_days=90
        )
        
        if result["success"]:
            print(f"Found {result['returned']} results out of {result['total_found']} total")
            for i, item in enumerate(result["results"][:3], 1):
                print(f"{i}. [{item['type']}] {item['title']}")
                print(f"   Object ID: {item['object_id']}")
                print(f"   Relevance: {item['relevance_score']:.2f}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    return result["results"][0]["object_id"] if result["success"] and result["results"] else None


async def test_fetch(object_id):
    """Test the fetch tool with an object ID."""
    print("\n" + "=" * 60)
    print("Testing Fetch Tool")
    print("=" * 60)
    
    if not object_id:
        print("No object ID available for testing")
        return
    
    print(f"\nFetching object: {object_id}")
    print("-" * 40)
    
    # Test without content
    result = deep_research_tools.fetch(
        object_ids=object_id,
        include_content=False
    )
    
    if result["success"]:
        print(f"Fetched {result['fetched']} objects successfully")
        for item in result["results"]:
            print(f"\nObject Type: {item['type']}")
            if item['type'] == 'company':
                print(f"Company: {item['name']}")
                print(f"CIK: {item['cik']}")
                print(f"Tickers: {item.get('tickers', [])}")
                print(f"Exchange: {item.get('exchange', 'N/A')}")
            elif item['type'] == 'filing':
                print(f"Company: {item['company']}")
                print(f"Form: {item['form_type']}")
                print(f"Date: {item['filing_date']}")
                print(f"Accession: {item['accession_number']}")
                if 'sec_url' in item:
                    print(f"SEC URL: {item['sec_url']}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    # Test with content (for filings)
    if result["success"] and result["results"][0]["type"] == "filing":
        print("\n" + "-" * 40)
        print("Fetching with content...")
        
        result_with_content = deep_research_tools.fetch(
            object_ids=[object_id],
            include_content=True
        )
        
        if result_with_content["success"] and result_with_content["results"]:
            content = result_with_content["results"][0].get("content", "")
            if content:
                print(f"Content preview (first 500 chars):")
                print(content[:500] + "..." if len(content) > 500 else content)


async def test_deep_research_workflow():
    """Test a complete Deep Research workflow."""
    print("\n" + "=" * 60)
    print("Testing Complete Deep Research Workflow")
    print("=" * 60)
    
    # Step 1: Search for a company
    print("\nStep 1: Search for NVIDIA information")
    search_result = deep_research_tools.search(
        query="NVIDIA",
        data_types=["companies", "filings"],
        top_k=5
    )
    
    if not search_result["success"] or not search_result["results"]:
        print("Search failed or no results")
        return
    
    # Collect object IDs
    object_ids = [r["object_id"] for r in search_result["results"][:3]]
    print(f"Found {len(object_ids)} objects to fetch")
    
    # Step 2: Fetch details for multiple objects
    print("\nStep 2: Fetch details for found objects")
    fetch_result = deep_research_tools.fetch(
        object_ids=object_ids,
        include_content=False
    )
    
    if fetch_result["success"]:
        print(f"Successfully fetched {fetch_result['fetched']} objects")
        for obj in fetch_result["results"]:
            print(f"- {obj['type']}: {obj.get('title', obj.get('name', 'Unknown'))}")
    
    print("\n" + "=" * 60)
    print("Deep Research Tools Test Complete!")
    print("=" * 60)


async def main():
    """Run all tests."""
    # Test search
    object_id = await test_search()
    
    # Test fetch with an object from search
    if object_id:
        await test_fetch(object_id)
    
    # Test complete workflow
    await test_deep_research_workflow()


if __name__ == "__main__":
    asyncio.run(main())