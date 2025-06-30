from typing import Dict, Any
from langgraph.graph import StateGraph, END
import time
from pwcproject.llm import GPT4Analyzer
from pwcproject.database import DatabaseManager
import json

class DataAnalysisWorkflow:
    
    def __init__(self):
        self.analyzer = GPT4Analyzer()
        self.db = DatabaseManager()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        workflow = StateGraph(Dict[str, Any])
        
        workflow.add_node("generate_sql", self._generate_sql_node)
        workflow.add_node("execute_query", self._execute_query_node)
        workflow.add_node("analyze_results", self._analyze_results_node)
        workflow.add_node("generate_insights", self._generate_insights_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        workflow.set_entry_point("generate_sql")
        
        workflow.add_conditional_edges(
            "generate_sql",
            self._should_continue,
            {
                "continue": "execute_query",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "execute_query",
            self._should_continue,
            {
                "continue": "analyze_results",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "analyze_results",
            self._should_continue,
            {
                "continue": "generate_insights",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("generate_insights", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _should_continue(self, state: Dict[str, Any]) -> str:
        return "error" if state.get("error") else "continue"
    
    def _generate_sql_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SQL query from natural language question"""
        try:
            data_source = self.db.get_default_data_source()
            if not data_source:
                state["error"] = "Default data source not found"
                return state
            
            schema_info = self.db.get_accrual_accounts_schema()
            
            sample_query = "SELECT * FROM accrual_accounts_data LIMIT 5"
            sample_df = self.db.execute_query(sample_query)
            sample_data = sample_df.to_string()
            
            sql_query = self.analyzer.generate_sql_query(
                state["question"],
                str(schema_info),
                sample_data
            )
            
            if not sql_query or sql_query.strip() == "":
                state["analysis"] = f"""
                I couldn't understand your question: "{state['question']}"
                
                Please be more specific about what you want to know. For example:
                - What specific information are you looking for?
                - Do you want to see data, count records, find patterns, or compare values?
                - Which columns are you interested in?
                
                Try rephrasing your question with more details about what you want to analyze.
                """
                state["insights"] = ["Question was too vague to generate a meaningful query"]
                state["recommendations"] = ["Please provide more specific details about what you want to analyze"]
                return state
            
            validation = self.analyzer.validate_sql_query(sql_query, str(schema_info))
            if not validation.get("valid", True):
                sql_query = validation.get("corrected_query", sql_query)
            
            state["sql_query"] = sql_query
            state["data_source_id"] = data_source["id"]
            return state
            
        except Exception as e:
            state["analysis"] = f"""
            I had trouble understanding your question: "{state['question']}"
            
            This might be because:
            - The question is too vague or unclear
            - You're asking about columns that don't exist in the data
            - The question format is not something I can analyze
            
            Please try rephrasing your question with more specific details about what you want to know.
            """
            state["insights"] = ["Question format needs to be more specific"]
            state["recommendations"] = ["Try asking about specific data, counts, patterns, or comparisons"]
            return state
    
    def _execute_query_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if not state.get("sql_query"):
                state["error"] = "No SQL query to execute"
                return state
            
            df = self.db.execute_query(state["sql_query"])
            
            if len(df) > 100:
                result_data = df.head(100).to_dict('records')
                result_info = f"Showing first 100 rows of {len(df)} total rows"
            else:
                result_data = df.to_dict('records')
                result_info = f"Showing all {len(df)} rows"
            
            state["query_result"] = {
                "data": result_data,
                "summary": {
                    "total_rows": len(df),
                    "displayed_rows": len(result_data),
                    "columns": df.columns.tolist(),
                    "info": result_info
                }
            }
            state["result_df"] = df
            return state
            
        except Exception as e:
            state["error"] = f"Error executing SQL query: {str(e)}"
            return state
    
    def _analyze_results_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if state.get("analysis_mode") == "query":
                state["analysis"] = "Query-only mode: No analysis performed"
                state["insights"] = ["Query executed successfully"]
                state["recommendations"] = ["Use analysis mode for AI-powered insights"]
                state["show_only_insights_and_recommendations"] = True
                return state
            
            if not state.get("query_result"):
                state["error"] = "No query results to analyze"
                return state
            
            data_source = self.db.get_default_data_source()
            data_summary = data_source.get("summary", "{}") if data_source else "{}"
            
            query_result = state["query_result"]
            if isinstance(query_result, dict) and "data" in query_result:
                result_summary = query_result["summary"]
                result_data = query_result["data"]
                
                analysis_input = f"""
                Query Results Summary:
                - Total rows: {result_summary['total_rows']}
                - Displayed rows: {result_summary['displayed_rows']}
                - Columns: {', '.join(result_summary['columns'])}
                - Info: {result_summary['info']}
                
                Data (first {len(result_data)} rows):
                {json.dumps(result_data, indent=2)}
                """
            else:
                analysis_input = str(query_result)
            
            analysis_result = self.analyzer.analyze_data(
                state["question"],
                analysis_input,
                data_summary,
                state.get("analysis_version", "long")
            )
            
            state["analysis"] = analysis_result["analysis"]
            state["insights"] = analysis_result["insights"]
            state["recommendations"] = analysis_result["recommendations"]
            if state.get("analysis_version", "long") == "short":
                state["show_only_insights_and_recommendations"] = True
            else:
                state["show_only_insights_and_recommendations"] = False
            return state
            
        except Exception as e:
            state["error"] = f"Error analyzing results: {str(e)}"
            return state
    
    def _generate_insights_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final insights and save to database"""
        try:
            if state.get("data_source_id"):
                self.db.save_analysis(state["data_source_id"], state)
            
            final_summary = f"""
            Analysis completed successfully!
            
            Question: {state['question']}
            
            Key Insights:
            {chr(10).join([f"• {insight}" for insight in state.get('insights', [])])}
            
            Recommendations:
            {chr(10).join([f"• {rec}" for rec in state.get('recommendations', [])])}
            """
            
            state["final_summary"] = final_summary
            return state
            
        except Exception as e:
            state["error"] = f"Error generating final insights: {str(e)}"
            return state
    
    def _handle_error_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle errors in the workflow"""
        error_msg = state.get("error", "Unknown error occurred")
        state["analysis"] = f"Error during analysis: {error_msg}"
        state["insights"] = ["Analysis could not be completed due to an error"]
        return state
    
    def run_analysis(self, question: str, analysis_mode: str = "analysis", analysis_version: str = "long") -> Dict[str, Any]:
        """Run the complete analysis workflow"""
        start_time = time.time()
        
        try:
            initial_state = {
                "question": question,
                "analysis_mode": analysis_mode,
                "analysis_version": analysis_version,
                "data_summary": None,
                "sql_query": None,
                "query_result": None,
                "analysis": None,
                "insights": None,
                "recommendations": None,
                "error": None,
                "timestamp": time.time()
            }
            
            result = self.graph.invoke(initial_state)
            
            execution_time = time.time() - start_time
            
            return {
                "success": not bool(result.get("error")),
                "state": result,
                "execution_time": execution_time
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "state": {
                    "question": question,
                    "analysis_mode": analysis_mode,
                    "analysis_version": analysis_version,
                    "error": f"Workflow execution failed: {str(e)}",
                    "timestamp": time.time()
                },
                "execution_time": execution_time
            } 