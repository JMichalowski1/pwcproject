import openai
from typing import Dict, List, Optional, Any
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from pwcproject.config import Config
from pwcproject import logger

class GPT4Analyzer:    
    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=Config.OPENAI_TEMPERATURE,
            max_tokens=Config.OPENAI_MAX_TOKENS,
            openai_api_key=Config.OPENAI_API_KEY
        )
    
    def generate_sql_query(self, question: str, schema_info: str, sample_data: str) -> str:
        system_prompt = f"""
        You are an expert SQL query generator. Given a user's question and database schema information, 
        generate a valid SQL query to answer the question.
        
        Database Schema:
        {schema_info}
        
        Sample Data:
        {sample_data}
        
        Instructions:
        1. Generate only the SQL query, no explanations
        2. Use proper SQL syntax
        3. Include appropriate WHERE clauses and aggregations
        4. Limit results to reasonable number of rows if needed
        5. Use table aliases for clarity
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Question: {question}")
        ]
        
        response = self.llm.invoke(messages)
        logger.info(f"SQL Query: {response.content.strip()}")
        return response.content.strip()
    
    def analyze_data(self, question: str, query_result: str, data_summary: str, analysis_version: str = "long") -> Dict[str, Any]:
        if analysis_version == "short":
            system_prompt = f"""
            You are an expert data analyst. Provide a BRIEF analysis of the provided data and query results.
            Focus on the most important insights only.
            
            Data Summary:
            {data_summary}
            
            Query Results:
            {query_result}
            
            Instructions:
            1. Provide a concise analysis (2-3 paragraphs maximum)
            2. Focus on the most critical insights only
            3. Keep recommendations brief and actionable
            4. Be specific but concise
            """
        else:
            system_prompt = f"""
            You are an expert data analyst. Analyze the provided data and query results to answer the user's question.
            Provide comprehensive analysis including insights and recommendations.
            
            Data Summary:
            {data_summary}
            
            Query Results:
            {query_result}
            
            Instructions:
            1. Analyze the data thoroughly
            2. Identify key patterns and trends
            3. Provide actionable insights
            4. Give business recommendations
            5. Be specific and data-driven
            """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Analysis Question: {question}")
        ]
        
        response = self.llm.invoke(messages)
        analysis = response.content
        
        insights = self._extract_insights(analysis)
        recommendations = self._extract_recommendations(analysis)
        
        return {
            "analysis": analysis,
            "insights": insights,
            "recommendations": recommendations
        }
    
    def _extract_insights(self, analysis: str) -> List[str]:
        """Extract key insights from analysis"""
        system_prompt = """
        Extract 1-3 key insights from the provided analysis. 
        Each insight should be a single, clear sentence.
        Return only the insights as a numbered list.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=analysis)
        ]
        
        response = self.llm.invoke(messages)
        insights_text = response.content
        
        insights = []
        for line in insights_text.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-') or line.startswith('*')):
                insight = line.lstrip('0123456789.•-* ').strip()
                if insight:
                    insights.append(insight)
        
        return insights[:3]
    
    def _extract_recommendations(self, analysis: str) -> List[str]:
        system_prompt = """
        Extract 1-3 actionable recommendations from the provided analysis.
        Each recommendation should be specific and actionable.
        Return only the recommendations as a numbered list.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=analysis)
        ]
        
        response = self.llm.invoke(messages)
        recommendations_text = response.content
        
        recommendations = []
        for line in recommendations_text.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-') or line.startswith('*')):
                recommendation = line.lstrip('0123456789.•-* ').strip()
                if recommendation:
                    recommendations.append(recommendation)
        
        return recommendations[:3]
    
    def validate_sql_query(self, query: str, schema_info: str) -> Dict[str, Any]:
        system_prompt = f"""
        You are an expert SQL validator. Review the provided SQL query against the database schema.
        If the query is valid, return it as-is. If there are issues, provide a corrected version.
        
        Database Schema:
        {schema_info}
        
        Instructions:
        1. Check for syntax errors
        2. Verify table and column names exist
        3. Ensure proper JOIN conditions
        4. Validate data types in WHERE clauses
        5. Return JSON with 'valid' (boolean) and 'corrected_query' (string) fields
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"SQL Query to validate: {query}")
        ]
        
        response = self.llm.invoke(messages)
        
        try:
            import json
            result = json.loads(response.content)
            return result
        except:
            return {
                "valid": True,
                "corrected_query": query
            } 