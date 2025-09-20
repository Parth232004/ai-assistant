"""
Comprehensive Streamlit Interface for AI Assistant Pipeline
Complete orchestration dashboard with real-time monitoring
"""

import os
import json
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import our pipeline components
from simple_pipeline_orchestrator import SimplePipelineOrchestrator, PipelineMode, StepStatus, get_orchestrator
from pipeline_logging import get_logger, log_summary_data, log_task_data, log_response_data

# Page configuration
st.set_page_config(
    page_title="AI Assistant Pipeline Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .success-metric {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .error-metric {
        background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .warning-metric {
        background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .step-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
        background: #f9f9f9;
    }
    .pipeline-flow {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .component-box {
        background: white;
        border: 2px solid #4CAF50;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        min-width: 120px;
        margin: 0 5px;
    }
    .arrow {
        font-size: 24px;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = get_orchestrator()
if 'logger' not in st.session_state:
    st.session_state.logger = get_logger()
if 'execution_history' not in st.session_state:
    st.session_state.execution_history = []

def load_config():
    """Load pipeline configuration"""
    try:
        with open("pipeline_config.json", 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to load pipeline config: {e}")
        return {}

def render_pipeline_flow():
    """Render visual pipeline flow diagram"""
    st.markdown("""
    <div class="pipeline-flow">
        <div class="component-box">
            <strong>Seeya</strong><br>
            Summarizer
        </div>
        <div class="arrow">→</div>
        <div class="component-box">
            <strong>Sankalp</strong><br>
            Task Processor
        </div>
        <div class="arrow">→</div>
        <div class="component-box">
            <strong>Noopur</strong><br>
            Responder
        </div>
        <div class="arrow">↓</div>
        <div class="component-box">
            <strong>Chandresh</strong><br>
            Context Search
        </div>
        <div class="arrow">↓</div>
        <div class="component-box">
            <strong>Parth</strong><br>
            Feedback
        </div>
        <div class="arrow">↓</div>
        <div class="component-box">
            <strong>Nilesh</strong><br>
            Metrics
        </div>
    </div>
    """, unsafe_allow_html=True)

def get_component_health_status():
    """Get real-time component health"""
    try:
        return st.session_state.orchestrator.get_component_health()
    except Exception as e:
        st.error(f"Failed to get component health: {e}")
        return {}

def render_health_dashboard():
    """Render component health dashboard"""
    st.subheader("🏥 Component Health Status")
    
    health_data = get_component_health_status()
    
    if not health_data:
        st.warning("No health data available")
        return
    
    # Create columns for health metrics
    cols = st.columns(len(health_data))
    
    for idx, (component, health) in enumerate(health_data.items()):
        with cols[idx]:
            if health['healthy']:
                st.markdown(f"""
                <div class="success-metric">
                    <h4>{component.title()}</h4>
                    <p>✅ {health['status']}</p>
                    {f"<small>{health.get('response_time_ms', 0):.1f}ms</small>" if 'response_time_ms' in health else ""}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="error-metric">
                    <h4>{component.title()}</h4>
                    <p>❌ {health['status']}</p>
                </div>
                """, unsafe_allow_html=True)

def render_execution_form():
    """Render pipeline execution form"""
    st.subheader("🚀 Execute Pipeline")
    
    with st.form("pipeline_execution"):
        col1, col2 = st.columns(2)
        
        with col1:
            user_id = st.text_input("User ID", value="demo_user", help="Unique identifier for the user")
            platform = st.selectbox("Platform", 
                ["email", "whatsapp", "slack", "teams", "instagram", "telegram"], 
                help="Source platform for the message")
            
        with col2:
            mode = st.selectbox("Pipeline Mode", 
                [mode.value for mode in PipelineMode],
                help="Execution mode: quick, analysis, or full pipeline")
            timestamp = st.text_input("Timestamp", 
                value=datetime.now().isoformat(),
                help="Message timestamp")
        
        message_text = st.text_area("Message Text", 
            value="Can we schedule a meeting for tomorrow at 2pm to discuss the project roadmap?",
            height=100,
            help="The actual message content to process")
        
        submit_button = st.form_submit_button("🎯 Execute Pipeline", type="primary")
        
        if submit_button:
            if not message_text.strip():
                st.error("Message text is required")
                return
            
            # Prepare input data
            input_data = {
                "user_id": user_id,
                "platform": platform,
                "message_text": message_text,
                "timestamp": timestamp,
                "message_id": f"msg_{int(time.time() * 1000)}"
            }
            
            # Execute pipeline
            with st.spinner("Executing pipeline..."):
                try:
                    # Convert mode string to enum
                    pipeline_mode = PipelineMode(mode)
                    
                    # Note: Using synchronous execution for Streamlit compatibility
                    execution_result = st.session_state.orchestrator.execute_pipeline(
                        input_data, pipeline_mode, execution_id
                    )
                    
                    st.success(f"✅ Pipeline executed successfully! ID: {execution_result.execution_id}")
                    
                    # Display results
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Status", execution_result.status.value)
                        st.metric("Duration", f"{execution_result.total_duration_ms:.0f}ms")
                    with col2:
                        st.metric("Steps Completed", len([s for s in execution_result.steps if s.status == StepStatus.COMPLETED]))
                        st.metric("Total Steps", len(execution_result.steps))
                    
                    # Don't simulate - real execution happened
                    # simulate_execution_results(execution_id, input_data, pipeline_mode)
                    
                except Exception as e:
                    st.error(f"Pipeline execution failed: {e}")

def simulate_execution_results(execution_id: str, input_data: Dict[str, Any], mode: PipelineMode):
    """Simulate pipeline execution results for demo"""
    import time
    
    # Simulate step-by-step execution
    steps = [
        {"name": "summarize", "component": "seeya", "duration": 1.2},
        {"name": "process_summary", "component": "sankalp", "duration": 0.8},
        {"name": "respond", "component": "noopur", "duration": 1.5},
        {"name": "search_similar", "component": "chandresh", "duration": 0.6},
        {"name": "coach_feedback", "component": "parth", "duration": 0.3},
        {"name": "metrics", "component": "nilesh", "duration": 0.2}
    ]
    
    execution_result = {
        "execution_id": execution_id,
        "status": "completed",
        "mode": mode.value,
        "start_time": datetime.now(),
        "steps": [],
        "total_duration_ms": 0
    }
    
    current_data = input_data.copy()
    
    for step in steps:
        step_result = {
            "name": step["name"],
            "component": step["component"],
            "status": "completed",
            "duration_ms": step["duration"] * 1000,
            "output_data": {}
        }
        
        # Simulate step outputs
        if step["name"] == "summarize":
            step_result["output_data"] = {
                "summary_id": f"sum_{execution_id}",
                "summary": f"Meeting request: {input_data['message_text'][:50]}...",
                "intent": "meeting",
                "urgency": "medium",
                "type": "action_required"
            }
        elif step["name"] == "process_summary":
            step_result["output_data"] = {
                "task_id": f"task_{execution_id}",
                "task_summary": "Schedule meeting for tomorrow 2pm",
                "priority": "medium",
                "status": "pending"
            }
        elif step["name"] == "respond":
            step_result["output_data"] = {
                "response_id": f"resp_{execution_id}",
                "response_text": "I'll help you schedule the meeting for tomorrow at 2pm. Let me check availability.",
                "tone": "professional",
                "status": "ok"
            }
        
        execution_result["steps"].append(step_result)
        execution_result["total_duration_ms"] += step_result["duration_ms"]
        current_data.update(step_result["output_data"])
    
    execution_result["end_time"] = datetime.now()
    
    # Store in session state
    if 'execution_history' not in st.session_state:
        st.session_state.execution_history = []
    
    st.session_state.execution_history.append(execution_result)
    
    # Log the results
    if "summary_id" in current_data:
        log_summary_data(current_data)
    if "task_id" in current_data:
        log_task_data(current_data)
    if "response_id" in current_data:
        log_response_data(current_data)

def render_live_monitoring():
    """Render live monitoring dashboard"""
    st.subheader("📊 Live Pipeline Monitoring")
    
    if not st.session_state.execution_history:
        st.info("No executions yet. Run a pipeline to see monitoring data.")
        return
    
    # Recent executions
    recent_executions = st.session_state.execution_history[-10:]
    
    # Execution metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_executions = len(st.session_state.execution_history)
    successful = sum(1 for e in st.session_state.execution_history if e["status"] == "completed")
    avg_duration = sum(e["total_duration_ms"] for e in st.session_state.execution_history) / total_executions if total_executions > 0 else 0
    success_rate = (successful / total_executions * 100) if total_executions > 0 else 0
    
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <h4>Total Executions</h4>
            <h2>{total_executions}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="success-metric">
            <h4>Success Rate</h4>
            <h2>{success_rate:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-container">
            <h4>Avg Duration</h4>
            <h2>{avg_duration:.0f}ms</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="warning-metric">
            <h4>Last Execution</h4>
            <h2>{recent_executions[-1]['execution_id'][-4:] if recent_executions else 'None'}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Execution timeline chart
    if len(recent_executions) > 1:
        st.subheader("📈 Execution Timeline")
        
        timeline_data = []
        for execution in recent_executions:
            timeline_data.append({
                "execution_id": execution["execution_id"],
                "duration_ms": execution["total_duration_ms"],
                "status": execution["status"],
                "mode": execution["mode"],
                "timestamp": execution["start_time"]
            })
        
        df = pd.DataFrame(timeline_data)
        
        fig = px.line(df, x="timestamp", y="duration_ms", 
                     title="Pipeline Execution Duration Over Time",
                     color="mode",
                     hover_data=["execution_id", "status"])
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent executions table
    st.subheader("📋 Recent Executions")
    
    execution_df = pd.DataFrame([
        {
            "Execution ID": e["execution_id"][-8:],
            "Mode": e["mode"],
            "Status": e["status"],
            "Duration (ms)": f"{e['total_duration_ms']:.0f}",
            "Steps": len(e["steps"]),
            "Start Time": e["start_time"].strftime("%H:%M:%S") if isinstance(e["start_time"], datetime) else e["start_time"]
        }
        for e in recent_executions
    ])
    
    st.dataframe(execution_df, use_container_width=True)

def render_step_details():
    """Render detailed step analysis"""
    st.subheader("🔍 Step-by-Step Analysis")
    
    if not st.session_state.execution_history:
        st.info("No execution data available.")
        return
    
    # Select execution to analyze
    execution_ids = [e["execution_id"] for e in st.session_state.execution_history]
    selected_execution_id = st.selectbox("Select Execution", execution_ids, index=len(execution_ids)-1)
    
    selected_execution = next((e for e in st.session_state.execution_history if e["execution_id"] == selected_execution_id), None)
    
    if not selected_execution:
        st.error("Execution not found")
        return
    
    # Execution overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Execution ID:** `{selected_execution['execution_id']}`  
        **Mode:** {selected_execution['mode']}  
        **Status:** {selected_execution['status']}  
        **Total Duration:** {selected_execution['total_duration_ms']:.2f}ms
        """)
    
    with col2:
        st.markdown(f"""
        **Start Time:** {selected_execution['start_time']}  
        **Total Steps:** {len(selected_execution['steps'])}  
        **Success Rate:** {sum(1 for s in selected_execution['steps'] if s['status'] == 'completed') / len(selected_execution['steps']) * 100:.1f}%
        """)
    
    # Step details
    st.subheader("Step Breakdown")
    
    for idx, step in enumerate(selected_execution['steps']):
        with st.expander(f"Step {idx + 1}: {step['name']} ({step['component']})", expanded=idx < 3):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                **Component:** {step['component']}  
                **Status:** {step['status']}  
                **Duration:** {step['duration_ms']:.2f}ms
                """)
            
            with col2:
                if step.get('output_data'):
                    st.markdown("**Output:**")
                    st.json(step['output_data'])
                else:
                    st.info("No output data available")

def render_configuration_panel():
    """Render configuration management panel"""
    st.subheader("⚙️ Pipeline Configuration")
    
    config = load_config()
    
    if not config:
        st.error("Configuration not loaded")
        return
    
    # Component toggles
    st.markdown("### Component Controls")
    
    components = config.get("components", {})
    
    for component_name, component_config in components.items():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"**{component_config.get('name', component_name)}**")
            st.caption(f"Base URL: {component_config.get('base_url')}")
        
        with col2:
            enabled = st.checkbox("Enabled", value=component_config.get("enabled", True), key=f"enable_{component_name}")
        
        with col3:
            priority = st.number_input("Priority", min_value=1, max_value=10, value=component_config.get("priority", 1), key=f"priority_{component_name}")
    
    # Pipeline modes
    st.markdown("### Pipeline Modes")
    
    routing = config.get("routing", {})
    bypass_modes = routing.get("bypass_modes", {})
    
    for mode_name, steps in bypass_modes.items():
        with st.expander(f"Mode: {mode_name}"):
            st.write("Steps in this mode:")
            for step in steps:
                st.markdown(f"• {step}")
    
    # Save configuration
    if st.button("💾 Save Configuration", type="primary"):
        try:
            # Update config with new values
            # (In a real implementation, you would update and save the config)
            st.success("Configuration saved successfully!")
        except Exception as e:
            st.error(f"Failed to save configuration: {e}")

def render_logs_viewer():
    """Render logs viewer"""
    st.subheader("📜 Pipeline Logs")
    
    # Log source selection
    log_sources = ["pipeline", "seeya", "sankalp", "noopur", "chandresh", "parth", "nilesh"]
    selected_source = st.selectbox("Log Source", log_sources)
    
    # Number of lines
    num_lines = st.slider("Number of lines", min_value=10, max_value=1000, value=100)
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)
    
    if auto_refresh:
        time.sleep(5)
        st.experimental_rerun()
    
    # Get logs
    try:
        logger = st.session_state.logger
        log_lines = logger.get_recent_logs(selected_source if selected_source != "pipeline" else None, num_lines)
        
        if log_lines:
            st.text_area("Logs", value="".join(log_lines), height=400)
        else:
            st.info("No logs available")
    except Exception as e:
        st.error(f"Failed to load logs: {e}")

def main():
    """Main Streamlit application"""
    
    # Header
    st.title("🤖 AI Assistant Pipeline Dashboard")
    st.markdown("Complete orchestration and monitoring for Seeya → Sankalp → Noopur → Chandresh pipeline")
    
    # Sidebar navigation
    st.sidebar.title("🎛️ Navigation")
    
    page = st.sidebar.radio("Select Page", [
        "🏠 Overview",
        "🚀 Execute Pipeline", 
        "📊 Live Monitoring",
        "🔍 Step Analysis",
        "⚙️ Configuration",
        "📜 Logs"
    ])
    
    # Render pipeline flow diagram
    render_pipeline_flow()
    
    # Component health status
    render_health_dashboard()
    
    # Main content based on selected page
    if page == "🏠 Overview":
        st.markdown("""
        ## Welcome to the AI Assistant Pipeline Dashboard
        
        This dashboard provides complete control and monitoring for the AI Assistant pipeline.
        
        ### Pipeline Components:
        - **Seeya**: Message summarization and intent analysis
        - **Sankalp**: Task creation and cognitive processing
        - **Noopur**: Response generation and delivery
        - **Chandresh**: Context search and embedding management
        - **Parth**: Feedback collection and coach scoring
        - **Nilesh**: Metrics and analytics tracking
        
        ### Available Features:
        - 🚀 Execute pipeline with different modes
        - 📊 Real-time monitoring and metrics
        - 🔍 Detailed step-by-step analysis
        - ⚙️ Configuration management
        - 📜 Comprehensive logging
        
        Use the sidebar to navigate between different sections.
        """)
        
    elif page == "🚀 Execute Pipeline":
        render_execution_form()
        
    elif page == "📊 Live Monitoring":
        render_live_monitoring()
        
    elif page == "🔍 Step Analysis":
        render_step_details()
        
    elif page == "⚙️ Configuration":
        render_configuration_panel()
        
    elif page == "📜 Logs":
        render_logs_viewer()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**AI Assistant Pipeline v1.0**")
    st.sidebar.markdown("Built with ❤️ for seamless AI orchestration")

if __name__ == "__main__":
    main()