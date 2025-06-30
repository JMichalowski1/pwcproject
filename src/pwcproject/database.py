import pandas as pd
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
import json
import os
import numpy as np
from datetime import datetime
from pwcproject.config import Config
from pwcproject.models import DataSummary

class DatabaseManager:
    """Manages database operations for MVP purpose"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or Config.DATABASE_URL
        self.engine = create_engine(self.database_url)
        self._create_tables()
        self._load_default_data()
    
    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS data_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    file_path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    summary TEXT
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_source_id INTEGER,
                    question TEXT NOT NULL,
                    sql_query TEXT,
                    result TEXT,
                    analysis TEXT,
                    insights TEXT,
                    recommendations TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (data_source_id) REFERENCES data_sources (id)
                )
            """))
            conn.commit()
    
    def _load_default_data(self):
        """Load the default Excel file into the database"""
        excel_file_path = "data/Data Dump - Accrual Accounts (1) (1) (2).xlsx"
        
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM data_sources WHERE name = 'Accrual Accounts Data'"))
            count = result.fetchone()[0]
            if count > 0:
                print("✅ Default data already loaded")
                return
        
        try:
            if os.path.exists(excel_file_path):
                print(f"📊 Loading default data from: {excel_file_path}")
                
                df = pd.read_excel(excel_file_path)
                
                if "Unnamed: 0" in df.columns:
                    df = df.drop(columns=["Unnamed: 0"])
                    print("🗑️ Dropped index column 'Unnamed: 0'")
                
                df = self._clean_dataframe_for_json(df)
                
                table_name = "accrual_accounts_data"
                df.to_sql(table_name, self.engine, if_exists='replace', index=False)
                
                summary = self._generate_data_summary(df)
                with self.engine.connect() as conn:
                    result = conn.execute(text("""
                        INSERT INTO data_sources (name, file_path, summary)
                        VALUES (:name, :file_path, :summary)
                    """), {
                        "name": "Accrual Accounts Data",
                        "file_path": excel_file_path,
                        "summary": json.dumps(summary.dict())
                    })
                    conn.commit()
                
                print(f"✅ Successfully loaded {len(df)} rows and {len(df.columns)} columns")
                print(f"📋 Columns: {', '.join(df.columns.tolist())}")
                
            else:
                print(f"⚠️ Default Excel file not found at: {excel_file_path}")
                
        except Exception as e:
            print(f"❌ Error loading default data: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _clean_dataframe_for_json(self, df: pd.DataFrame) -> pd.DataFrame:
        df_clean = df.copy()
        
        for column in df_clean.columns:
            if pd.api.types.is_datetime64_any_dtype(df_clean[column]):
                df_clean[column] = df_clean[column].dt.strftime('%Y-%m-%d %H:%M:%S').fillna('')
            
            elif pd.api.types.is_numeric_dtype(df_clean[column]):
                df_clean[column] = df_clean[column].fillna(0)
            
            else:
                df_clean[column] = df_clean[column].astype(str).replace('NaT', '')
                df_clean[column] = df_clean[column].replace(['nan', 'None', 'NULL'], '')
        
        return df_clean
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        if hasattr(row, '_mapping'):
            return dict(row._mapping)
        elif hasattr(row, '__dict__'):
            return {k: v for k, v in row.__dict__.items() if not k.startswith('_')}
        else:
            return dict(row)
    
    def _generate_data_summary(self, df: pd.DataFrame) -> DataSummary:
        data_types = {}
        for col, dtype in df.dtypes.items():
            if pd.api.types.is_datetime64_any_dtype(dtype):
                data_types[col] = 'datetime64[ns]'
            elif pd.api.types.is_numeric_dtype(dtype):
                data_types[col] = str(dtype)
            else:
                data_types[col] = 'object'
        
        missing_values = {}
        for col in df.columns:
            missing_count = df[col].isna().sum()
            missing_values[col] = int(missing_count)
        
        sample_data = []
        sample_df = df.head(5)
        for _, row in sample_df.iterrows():
            clean_row = {}
            for col, value in row.items():
                if pd.isna(value) or value is None:
                    clean_row[col] = None
                elif isinstance(value, (np.integer, np.floating)):
                    clean_row[col] = float(value)
                elif isinstance(value, pd.Timestamp):
                    clean_row[col] = value.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    clean_row[col] = str(value)
            sample_data.append(clean_row)
        
        return DataSummary(
            file_name="",
            row_count=len(df),
            column_count=len(df.columns),
            columns=df.columns.tolist(),
            data_types=data_types,
            missing_values=missing_values,
            sample_data=sample_data
        )
    
    def get_default_data_source(self) -> Optional[Dict[str, Any]]:
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM data_sources WHERE name = 'Accrual Accounts Data'"))
            row = result.fetchone()
            return self._row_to_dict(row) if row else None
    
    def execute_query(self, query: str) -> pd.DataFrame:
        try:
            return pd.read_sql_query(query, self.engine)
        except SQLAlchemyError as e:
            raise Exception(f"SQL query execution failed: {str(e)}")
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        inspector = inspect(self.engine)
        columns = inspector.get_columns(table_name)
        return {
            "table_name": table_name,
            "columns": [{"name": col["name"], "type": str(col["type"])} for col in columns]
        }
    
    def get_accrual_accounts_schema(self) -> Dict[str, Any]:
        return self.get_table_schema("accrual_accounts_data")
    
    def save_analysis(self, data_source_id: str, state: Dict[str, Any]) -> str:
        clean_state = {}
        for key, value in state.items():
            if isinstance(value, (list, dict)):
                clean_state[key] = json.dumps(value)
            else:
                clean_state[key] = str(value) if value is not None else None
        
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                INSERT INTO analysis_history 
                (data_source_id, question, sql_query, result, analysis, insights, recommendations)
                VALUES (:data_source_id, :question, :sql_query, :result, :analysis, :insights, :recommendations)
            """), {
                "data_source_id": data_source_id,
                "question": clean_state.get("question", ""),
                "sql_query": clean_state.get("sql_query", ""),
                "result": clean_state.get("query_result", ""),
                "analysis": clean_state.get("analysis", ""),
                "insights": clean_state.get("insights", "[]"),
                "recommendations": clean_state.get("recommendations", "[]")
            })
            conn.commit()
            return str(result.lastrowid)
    
    def get_analysis_history(self, data_source_id: str = None) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            if data_source_id:
                result = conn.execute(text("""
                    SELECT * FROM analysis_history 
                    WHERE data_source_id = :data_source_id 
                    ORDER BY created_at DESC
                """), {"data_source_id": data_source_id})
            else:
                result = conn.execute(text("""
                    SELECT * FROM analysis_history 
                    ORDER BY created_at DESC
                """))
            return [self._row_to_dict(row) for row in result] 