"""
Pydantic models for chatbot specialists.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class IntentType(str, Enum):
    """Intent types for the chatbot."""
    SEARCH = "search"
    INFO = "info" 
    GENERAL = "general"
    SFC_LICENSE = "sfc_license"  # New intent for SFC license checking


class IntentAnalysis(BaseModel):
    """Model for intent analysis output."""
    intent: IntentType = Field(description="The classified intent of the user message")
    confidence: float = Field(description="Confidence score for the intent classification (0-1)")
    search_query: str = Field(description="Extracted search query for search/info intents", default="")
    reasoning: str = Field(description="Brief explanation of why this intent was chosen", default="")


class NameExtraction(BaseModel):
    """Model for name extraction output."""
    name: str = Field(description="Extracted candidate name, empty if not found", default="")
    confidence: float = Field(description="Confidence score for the name extraction (0-1)")
    reasoning: str = Field(description="Brief explanation of the extraction", default="")


class QueryEnhancement(BaseModel):
    """Model for query enhancement output."""
    enhanced_query: str = Field(description="Enhanced search query with related terms")
    original_query: str = Field(description="Original query for reference")
    added_terms: List[str] = Field(description="List of terms added to enhance the query", default_factory=list)
    reasoning: str = Field(description="Explanation of enhancements made", default="") 


class SFCLicenseQuery(BaseModel):
    """Model for SFC license query extraction."""
    candidate_name: str = Field(description="Name of the person to check for SFC license")
    confidence: float = Field(description="Confidence score for name extraction (0-1)")
    reasoning: str = Field(description="Brief explanation of the extraction", default="")

class SFCLicenseResult(BaseModel):
    """Model for SFC license check result."""
    candidate_name: str = Field(description="Name that was searched")
    has_license: bool = Field(description="Whether the candidate has a valid SFC license")
    license_details: Optional[str] = Field(description="Details about the license if found", default=None)
    search_url: str = Field(description="URL for manual verification")
    confidence: float = Field(description="Confidence in the result accuracy (0-1)")
    error_message: Optional[str] = Field(description="Error message if search failed", default=None)