"""
Deep Research compatible tools for OpenAI integration.

These tools provide Search and Fetch capabilities that OpenAI Deep Research
expects for exploring SEC EDGAR data.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import hashlib
import json
from edgar import get_filings
from ..core.client import EdgarClient
from ..utils.exceptions import FilingNotFoundError, CompanyNotFoundError
from .types import ToolResponse


class DeepResearchTools:
    """Tools optimized for OpenAI Deep Research integration."""
    
    def __init__(self):
        self.client = EdgarClient()
        # Cache for object ID mappings
        self._object_cache: Dict[str, Dict[str, Any]] = {}
        
    def _generate_object_id(self, data_type: str, identifier: str) -> str:
        """Generate a consistent object ID for any data type."""
        raw_id = f"{data_type}:{identifier}"
        return hashlib.md5(raw_id.encode()).hexdigest()[:16]
    
    def _score_relevance(self, query: str, text: str) -> float:
        """Simple relevance scoring based on query term matches."""
        query_terms = query.lower().split()
        text_lower = text.lower()
        
        matches = sum(1 for term in query_terms if term in text_lower)
        return matches / max(len(query_terms), 1)
    
    def search(
        self,
        query: str,
        data_types: Optional[List[str]] = None,
        top_k: int = 10,
        date_range_days: Optional[int] = 90
    ) -> ToolResponse:
        """
        Search through SEC EDGAR data for relevant information.
        
        This tool searches across companies, filings, and financial data
        to find the most relevant results for Deep Research exploration.
        
        Args:
            query: Search query string
            data_types: Types to search ["companies", "filings", "financials"] (default: all)
            top_k: Number of top results to return (default: 10)
            date_range_days: Limit filing search to recent N days (default: 90)
            
        Returns:
            Dictionary with top-k search results including object IDs for fetching
        """
        try:
            if data_types is None:
                data_types = ["companies", "filings"]
            
            all_results = []
            
            # Search companies
            if "companies" in data_types:
                try:
                    # Search by query
                    companies = self.client.search_companies(query, limit=top_k * 2)
                    
                    for company in companies:
                        obj_id = self._generate_object_id("company", company.cik)
                        
                        # Build searchable text
                        search_text = f"{company.name} {' '.join(getattr(company, 'tickers', []))} CIK:{company.cik}"
                        relevance = self._score_relevance(query, search_text)
                        
                        result = {
                            "object_id": obj_id,
                            "type": "company",
                            "title": company.name,
                            "cik": company.cik,
                            "ticker": getattr(company, 'tickers', [None])[0] if hasattr(company, 'tickers') else None,
                            "description": f"SEC registered company - CIK: {company.cik}",
                            "relevance_score": relevance
                        }
                        
                        # Cache for fetch
                        self._object_cache[obj_id] = {
                            "type": "company",
                            "cik": company.cik,
                            "data": result
                        }
                        
                        all_results.append(result)
                except Exception as e:
                    # Continue even if company search fails
                    pass
            
            # Search filings
            if "filings" in data_types:
                try:
                    # Try to find company first for targeted search
                    target_company = None
                    try:
                        # Check if query looks like a ticker or CIK
                        target_company = self.client.get_company(query)
                    except:
                        pass
                    
                    if target_company:
                        # Company-specific filing search
                        filings = target_company.get_filings()
                    else:
                        # Global filing search
                        filings = get_filings(count=top_k * 3)
                    
                    # Process filings
                    filing_count = 0
                    for filing in filings:
                        if filing_count >= top_k * 2:
                            break
                            
                        # Apply date filter if specified
                        if date_range_days:
                            cutoff_date = datetime.now() - timedelta(days=date_range_days)
                            filing_date = filing.filing_date
                            if isinstance(filing_date, str):
                                filing_date = datetime.fromisoformat(filing_date.replace('Z', '+00:00'))
                            if filing_date < cutoff_date:
                                continue
                        
                        obj_id = self._generate_object_id("filing", filing.accession_number)
                        
                        # Build searchable text
                        search_text = f"{filing.company} {filing.form} {filing.accession_number}"
                        relevance = self._score_relevance(query, search_text)
                        
                        # Boost relevance for certain form types if mentioned in query
                        query_lower = query.lower()
                        if filing.form.lower() in query_lower:
                            relevance += 0.5
                        
                        result = {
                            "object_id": obj_id,
                            "type": "filing",
                            "title": f"{filing.company} - {filing.form}",
                            "form_type": filing.form,
                            "company": filing.company,
                            "cik": filing.cik,
                            "accession_number": filing.accession_number,
                            "filing_date": filing.filing_date.isoformat() if hasattr(filing.filing_date, 'isoformat') else str(filing.filing_date),
                            "description": f"{filing.form} filing from {filing.company}",
                            "relevance_score": relevance
                        }
                        
                        # Cache for fetch
                        self._object_cache[obj_id] = {
                            "type": "filing",
                            "cik": filing.cik,
                            "accession_number": filing.accession_number,
                            "data": result
                        }
                        
                        all_results.append(result)
                        filing_count += 1
                        
                except Exception as e:
                    # Continue even if filing search fails
                    pass
            
            # Sort by relevance and return top-k
            all_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            top_results = all_results[:top_k]
            
            return {
                "success": True,
                "query": query,
                "results": top_results,
                "total_found": len(all_results),
                "returned": len(top_results),
                "data_types_searched": data_types,
                "message": f"Found {len(top_results)} relevant results for '{query}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "query": query
            }
    
    def fetch(
        self,
        object_ids: Union[str, List[str]],
        include_content: bool = False
    ) -> ToolResponse:
        """
        Fetch detailed information for specific object IDs.
        
        This tool retrieves full details for objects found via search,
        enabling Deep Research to explore specific items in depth.
        
        Args:
            object_ids: Single object ID or list of object IDs to fetch
            include_content: Whether to include full filing content (default: False)
            
        Returns:
            Dictionary with detailed information for each object ID
        """
        try:
            # Normalize to list
            if isinstance(object_ids, str):
                object_ids = [object_ids]
            
            results = []
            errors = []
            
            for obj_id in object_ids:
                try:
                    # Check cache first
                    if obj_id in self._object_cache:
                        cached = self._object_cache[obj_id]
                        obj_type = cached["type"]
                        
                        if obj_type == "company":
                            # Fetch full company details
                            company = self.client.get_company(cached["cik"])
                            
                            result = {
                                "object_id": obj_id,
                                "type": "company",
                                "cik": company.cik,
                                "name": company.name,
                                "tickers": getattr(company, "tickers", []),
                                "sic": getattr(company, "sic", None),
                                "sic_description": getattr(company, "sic_description", None),
                                "exchange": getattr(company, "exchange", None),
                                "state": getattr(company, "state", None),
                                "fiscal_year_end": getattr(company, "fiscal_year_end", None),
                                "business_address": getattr(company, "business_address", None),
                                "mailing_address": getattr(company, "mailing_address", None),
                                "former_names": getattr(company, "former_names", []),
                                "description": f"Full company information for {company.name}"
                            }
                            
                        elif obj_type == "filing":
                            # Fetch full filing details
                            cik = cached["cik"]
                            accession = cached["accession_number"]
                            
                            company = self.client.get_company(cik)
                            
                            # Find the specific filing
                            filing = None
                            for f in company.get_filings():
                                if f.accession_number.replace("-", "") == accession.replace("-", ""):
                                    filing = f
                                    break
                            
                            if not filing:
                                raise FilingNotFoundError(f"Filing {accession} not found")
                            
                            result = {
                                "object_id": obj_id,
                                "type": "filing",
                                "accession_number": filing.accession_number,
                                "cik": filing.cik,
                                "company": filing.company,
                                "form_type": filing.form,
                                "filing_date": filing.filing_date.isoformat() if hasattr(filing.filing_date, 'isoformat') else str(filing.filing_date),
                                "period_of_report": getattr(filing, "period_of_report", None),
                                "file_number": getattr(filing, "file_number", None),
                                "acceptance_datetime": getattr(filing, "acceptance_datetime", None),
                                "documents": getattr(filing, "documents", []),
                                "primary_document": getattr(filing, "primary_document", None),
                                "sec_url": f"https://www.sec.gov/Archives/edgar/data/{filing.cik}/{filing.accession_number.replace('-', '')}/{filing.accession_number}-index.htm"
                            }
                            
                            # Include content if requested
                            if include_content:
                                try:
                                    content = filing.text()
                                    # Limit content size for response
                                    if len(content) > 50000:
                                        content = content[:50000] + "\n\n[Content truncated - too large for response]"
                                    result["content"] = content
                                except:
                                    result["content"] = "Content not available"
                                    
                        else:
                            result = cached.get("data", {"object_id": obj_id, "error": "Unknown object type"})
                        
                        results.append(result)
                        
                    else:
                        # Try to decode and fetch fresh
                        # This is a fallback for when cache is cleared
                        errors.append({
                            "object_id": obj_id,
                            "error": "Object ID not found in cache. Please search again."
                        })
                        
                except Exception as e:
                    errors.append({
                        "object_id": obj_id,
                        "error": str(e)
                    })
            
            return {
                "success": True if results else False,
                "results": results,
                "errors": errors if errors else None,
                "fetched": len(results),
                "failed": len(errors)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Fetch failed: {str(e)}",
                "object_ids": object_ids
            }


# Create singleton instance
deep_research_tools = DeepResearchTools()