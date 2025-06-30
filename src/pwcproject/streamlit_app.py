import streamlit as st
import pandas as pd
import requests
import json
from typing import Dict, List, Any
import time
import os

st.set_page_config(
    page_title="GPT-4 Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

API_BASE_URL = "http://localhost:8000"

class DataAnalystApp:
    """Main application class"""
    
    def __init__(self):
        self.session_state = st.session_state
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables"""
        if 'current_analysis' not in self.session_state:
            self.session_state.current_analysis = None
        if 'data_info' not in self.session_state:
            self.session_state.data_info = None
    
    def render_header(self):
        st.title("🤖 AI Data Analyst")
    
    def render_dashboard(self):
        st.header("🏠 Dashboard")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        st.subheader("📊 Data Overview")
        
        try:
            response = requests.get(f"{API_BASE_URL}/data-info", timeout=5)
            if response.status_code == 200:
                data_info = response.json()
                self.session_state.data_info = data_info
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Rows", data_info.get('total_rows', 0))
                with col2:
                    st.metric("Columns", len(data_info.get('columns', [])))
                with col3:
                    st.metric("Data Source", "Accrual Accounts")
                
                with st.expander("📋 Sample Data", expanded=False):
                    if data_info.get('sample_data'):
                        sample_df = pd.DataFrame(data_info['sample_data'])
                        st.dataframe(sample_df)
                
            else:
                st.warning("Could not load data information")
        except:
            st.warning("Could not connect to API")
        
        st.subheader("📋 Recent Activity")
        
        try:
            response = requests.get(f"{API_BASE_URL}/analysis-history", timeout=5)
            if response.status_code == 200:
                history = response.json()
                if history:
                    for item in history[:10]:
                        with st.expander(f"Analysis: {item.get('question', 'Unknown')[:50]}..."):
                            st.write(f"**Date:** {item.get('created_at', 'Unknown')}")
                            st.write(f"**Question:** {item.get('question', 'Unknown')}")
                            if item.get('insights'):
                                st.write("**Key Insights:**")
                                insights = json.loads(item['insights']) if isinstance(item['insights'], str) else item['insights']
                                for insight in insights[:3]:
                                    st.write(f"• {insight}")
                else:
                    st.info("No analysis history yet. Start by running an analysis!")
            else:
                st.warning("Could not load recent activity")
        except:
            st.warning("Could not connect to API")
    
    def render_data_overview(self):
        st.header("📋 Data Overview")
        
        try:
            response = requests.get(f"{API_BASE_URL}/data-info", timeout=5)
            if response.status_code == 200:
                data_info = response.json()
                self.session_state.data_info = data_info
                
                st.subheader("📊 Data Source Information")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Rows", data_info.get('total_rows', 0))
                with col2:
                    st.metric("Columns", len(data_info.get('columns', [])))
                with col3:
                    st.metric("Data Source", "Accrual Accounts")
                
                st.subheader("🏗️ Database Schema")
                if data_info.get('schema'):
                    schema = data_info['schema']
                    st.write(f"**Table Name:** {schema.get('table_name', 'Unknown')}")
                    
                    columns_df = pd.DataFrame(schema.get('columns', []))
                    if not columns_df.empty:
                        st.dataframe(columns_df, use_container_width=True)
                
                st.subheader("📋 Sample Data")
                if data_info.get('sample_data'):
                    sample_df = pd.DataFrame(data_info['sample_data'])
                    st.dataframe(sample_df, use_container_width=True)
                
            else:
                st.error("Could not load data information")
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
    
    def render_analysis(self):
        """Render the analysis page"""
        st.header("🔍 Data Analysis")
        
        st.subheader("📊 Current Data Source")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Name", "Accrual Accounts Data")
        with col2:
            if self.session_state.data_info:
                st.metric("Rows", self.session_state.data_info.get('total_rows', 0))
            else:
                st.metric("Rows", "Loading...")
        with col3:
            if self.session_state.data_info:
                st.metric("Columns", len(self.session_state.data_info.get('columns', [])))
            else:
                st.metric("Columns", "Loading...")
        
        st.subheader("📋 Available Columns")
        if self.session_state.data_info and self.session_state.data_info.get('schema'):
            columns = self.session_state.data_info['schema']['columns']
            if columns:
                columns_df = pd.DataFrame(columns)
                st.dataframe(columns_df, use_container_width=True, hide_index=True)
                
                st.info("💡 **Tip:** You can ask questions about any of these columns. For example: 'What are the top 5 authorization groups by transaction value?' or 'Show me the distribution of currencies used in transactions.'")
            else:
                st.warning("No column information available")
        else:
            st.info("Loading column information...")
        

        if self.session_state.current_analysis:
            st.subheader("📊 Current Analysis Results")
            self._display_analysis_results(self.session_state.current_analysis)
            st.divider()
        
        st.subheader("🤖 Ask Your Question")
        
        question = st.text_area(
            "What would you like to analyze?",
            placeholder="e.g., Are there any correlation between Document Is Back-Posted values and Transaction Values?",
            height=100
        )
        
        analysis_mode = st.toggle(
            "🔍 Enable GPT-4 Analysis",
            value=True,
            help="Toggle ON for AI-powered analysis with insights and recommendations. Toggle OFF for direct database query results only."
        )
        
        analysis_version = "long"
        if analysis_mode:
            analysis_version = st.radio(
                "📊 Analysis Version",
                options=["short", "long"],
                index=0,  # Default to short
                format_func=lambda x: "Short Analysis" if x == "short" else "Long Analysis",
                help="Short: Quick insights and basic recommendations. Long: Detailed analysis with comprehensive insights and multiple recommendations."
            )
        
        # Run analysis
        if st.button("🚀 Run Analysis", type="primary", disabled=not question):
            if question:
                with st.spinner("🤖 Processing your request..."):
                    try:
                        request_data = {
                            "question": question,
                            "analysis_mode": "analysis" if analysis_mode else "query",
                            "analysis_version": analysis_version if analysis_mode else "short"
                        }
                        
                        response = requests.post(
                            f"{API_BASE_URL}/analyze",
                            json=request_data,
                            timeout=60
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            self.session_state.current_analysis = result
                            
                            if analysis_mode:
                                st.success("✅ Analysis completed!")
                            else:
                                st.success("✅ Query executed!")
                            
                            self._display_analysis_results(result)
                        else:
                            st.error(f"❌ Request failed: {response.text}")
                    
                    except Exception as e:
                        st.error(f"❌ Request failed: {str(e)}")
    
    def _display_analysis_results(self, result: Dict[str, Any]):
        """Display analysis results"""
        state = result['state']
        show_only_ir = state.get('show_only_insights_and_recommendations', False)
        
        if state.get('error'):
            st.error(f"❌ **Error:** {state['error']}")
            st.info("💡 **Suggestion:** Try rephrasing your question or be more specific about what you'd like to analyze.")
            return
        
        if state.get('analysis') and ('couldn\'t understand' in state['analysis'].lower() or 'had trouble understanding' in state['analysis'].lower()):
            st.warning("🤖 **I need more details**")
            st.write(state['analysis'])
            
            if state.get('insights'):
                st.subheader("💡 Key Insights")
                for i, insight in enumerate(state['insights'], 1):
                    st.markdown(f"**{i}.** {insight}")
            
            if state.get('recommendations'):
                st.subheader("🎯 Recommendations")
                for i, rec in enumerate(state['recommendations'], 1):
                    st.markdown(f"**{i}.** {rec}")
            return
        
        has_sql_query = bool(state.get('sql_query'))
        has_query_result = bool(state.get('query_result'))
        has_analysis = bool(state.get('analysis'))
        has_insights = bool(state.get('insights'))
        
        if not any([has_sql_query, has_query_result, has_analysis, has_insights]):
            st.warning("⚠️ **No results found**")
            st.info("💡 **Suggestion:** Try rephrasing your question. For example:")
            st.markdown("""
            - Instead of: "What are the Document is Back-Posted column values"
            - Try: "Show me the unique values in the Document is Back-Posted column"
            - Or: "What are the different types of Document is Back-Posted values?"
            - Or: "Count how many records have each Document is Back-Posted value"
            """)
            return
        
        st.metric("⏱️ Execution Time", f"{result['execution_time']:.2f} seconds")
        
        if show_only_ir:
            if state.get('insights'):
                st.subheader("💡 Key Insights")
                for i, insight in enumerate(state['insights'], 1):
                    st.markdown(f"**{i}.** {insight}")
            if state.get('recommendations'):
                st.subheader("🎯 Recommendations")
                for i, rec in enumerate(state['recommendations'], 1):
                    st.markdown(f"**{i}.** {rec}")
            return
        
        if state.get('sql_query'):
            with st.expander("🔍 Generated SQL Query", expanded=False):
                st.code(state['sql_query'], language='sql')
        
        if state.get('analysis'):
            st.subheader("📊 Analysis Results")
            st.write(state['analysis'])
        
        if state.get('insights'):
            st.subheader("💡 Key Insights")
            for i, insight in enumerate(state['insights'], 1):
                st.markdown(f"**{i}.** {insight}")
        
        if state.get('recommendations'):
            st.subheader("🎯 Recommendations")
            for i, rec in enumerate(state['recommendations'], 1):
                st.markdown(f"**{i}.** {rec}")
        
        if state.get('query_result'):
            with st.expander("📋 Query Results", expanded=False):
                query_result = state['query_result']
                
                if isinstance(query_result, dict) and "data" in query_result:
                    summary = query_result["summary"]
                    data = query_result["data"]
                    
                    st.write(f"**Summary:** {summary['info']}")
                    st.write(f"**Columns:** {', '.join(summary['columns'])}")
                    
                    if data:
                        df = pd.DataFrame(data)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No data returned from query")
                else:
                    st.text(str(query_result))
    
    def run(self):
        """Run the main application"""
        self.render_header()
        
        tab1, tab2, tab3 = st.tabs([
            "🏠 Dashboard", 
            "📋 Data Overview", 
            "🔍 Analysis"
        ])
        
        with tab1:
            self.render_dashboard()
        
        with tab2:
            self.render_data_overview()
        
        with tab3:
            self.render_analysis()

if __name__ == "__main__":
    app = DataAnalystApp()
    app.run() 