from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import json
from typing import List, Dict, Any, Optional
import time
from datetime import datetime

from pwcproject.config import Config
from pwcproject.models import (
    AnalysisRequest, AnalysisResponse, AnalysisState
)
from pwcproject.database import DatabaseManager
from pwcproject.workflow import DataAnalysisWorkflow
from pwcproject.llm import GPT4Analyzer

app = FastAPI(
    title="GPT-4 Data Analyst API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DatabaseManager()
workflow = DataAnalysisWorkflow()
analyzer = GPT4Analyzer()

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        Config.validate()
        print("✅ Configuration validated successfully")
        
        default_source = db.get_default_data_source()
        if default_source:
            print(f"✅ Default data source loaded: {default_source['name']}")
        else:
            print("⚠️ Default data source not found")
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        raise e

@app.get("/data-info")
async def get_data_info():
    """Get information about the loaded data"""
    try:
        default_source = db.get_default_data_source()
        if not default_source:
            raise HTTPException(status_code=404, detail="Default data source not found")
        
        schema = db.get_accrual_accounts_schema()
        
        sample_df = db.execute_query("""
            SELECT * FROM accrual_accounts_data 
            WHERE "Authorization Group" IS NOT NULL 
            AND "Bus. Transac. Type" IS NOT NULL 
            AND "Transaction Value" IS NOT NULL 
            AND "Currency" IS NOT NULL 
            AND "Debit/Credit ind" IS NOT NULL
            AND "Calculate Tax" IS NOT NULL
            LIMIT 5
        """)
        
        count_df = db.execute_query("SELECT COUNT(*) as count FROM accrual_accounts_data")
        total_rows = int(count_df.iloc[0]['count']) if not count_df.empty else 0
        
        return {
            "data_source": default_source,
            "schema": schema,
            "sample_data": sample_df.to_dict('records'),
            "total_rows": total_rows,
            "columns": schema["columns"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get data info: {str(e)}")

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_data(request: AnalysisRequest):
    try:
        default_source = db.get_default_data_source()
        if not default_source:
            raise HTTPException(status_code=404, detail="Default data source not found")
        
        result = workflow.run_analysis(request.question, request.analysis_mode, request.analysis_version)
        
        state_dict = result["state"]
        analysis_state = AnalysisState(
            question=state_dict.get("question", ""),
            data_summary=state_dict.get("data_summary"),
            sql_query=state_dict.get("sql_query"),
            query_result=state_dict.get("query_result"),
            analysis=state_dict.get("analysis"),
            insights=state_dict.get("insights"),
            recommendations=state_dict.get("recommendations"),
            error=state_dict.get("error"),
            timestamp=datetime.fromtimestamp(state_dict.get("timestamp", time.time()))
        )
        
        return AnalysisResponse(
            success=result["success"],
            state=analysis_state,
            execution_time=result["execution_time"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/analysis-history", response_model=List[Dict[str, Any]])
async def get_analysis_history():
    """Get analysis history"""
    try:
        history = db.get_analysis_history()
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analysis history: {str(e)}")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": time.time()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.pwcproject.api:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG
    ) 