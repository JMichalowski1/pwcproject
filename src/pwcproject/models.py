from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

class AnalysisState(BaseModel):
    """State for the analysis workflow"""
    question: str = Field(description="User's analysis question")
    data_summary: Optional[str] = Field(default=None, description="Summary of the data")
    sql_query: Optional[str] = Field(default=None, description="Generated SQL query")
    query_result: Optional[Union[str, Dict[str, Any]]] = Field(default=None, description="Result of SQL query (string or JSONL format)")
    analysis: Optional[str] = Field(default=None, description="GPT-4 analysis of results")
    insights: Optional[List[str]] = Field(default=None, description="Key insights from analysis")
    recommendations: Optional[List[str]] = Field(default=None, description="Recommendations based on analysis")
    error: Optional[str] = Field(default=None, description="Error message if any")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")

class AnalysisRequest(BaseModel):
    """Request model for analysis"""
    question: str = Field(description="Analysis question to answer")
    analysis_mode: str = Field(default="analysis", description="Mode: 'analysis' for GPT-4 analysis, 'query' for database query only")
    analysis_version: str = Field(default="long", description="Version: 'short' for brief insights, 'long' for detailed analysis")

class AnalysisResponse(BaseModel):
    """Response model for analysis results"""
    success: bool = Field(description="Whether the analysis was successful")
    state: AnalysisState = Field(description="Analysis state with results")
    execution_time: float = Field(description="Time taken for analysis in seconds")

class DataSummary(BaseModel):
    """Summary of uploaded data"""
    file_name: str = Field(description="Name of the data file")
    row_count: int = Field(description="Number of rows in the data")
    column_count: int = Field(description="Number of columns in the data")
    columns: List[str] = Field(description="List of column names")
    data_types: Dict[str, str] = Field(description="Data types of each column")
    missing_values: Dict[str, int] = Field(description="Missing value counts per column")
    sample_data: List[Dict[str, Any]] = Field(description="Sample of the data") 