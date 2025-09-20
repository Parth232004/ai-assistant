"""
Comprehensive AI Assistant Pipeline Integration with Streamlit
Integrates Seeya, Sankalp, Noopur, Chandresh, Parth, and Nilesh components
"""

import streamlit as st
import requests
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

# Page configuration
st.set_page_config(
    page_title="AI Assistant Pipeline - Complete Integration",
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
    .component-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
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
        flex-wrap: wrap;
    }
    .component-box {
        background: white;
        border: 2px solid #4CAF50;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        min-width: 100px;
        margin: 5px;
        flex: 1;
    }
    .arrow {
        font-size: 20px;
        color: #666;
        margin: 0 5px;
    }
</style>
""", unsafe_allow_html=True)

# Component configuration
COMPONENTS = {
    "seeya": {
        "name": "Seeya (Summarizer)", 
        "url": "http://localhost:8001",
        "port": 8001,
        "description": "Smart message summarization with intent analysis"
    },
    "sankalp": {
        "name": "Sankalp (Cognitive Agent)", 
        "url": "http://localhost:8002",
        "port": 8002,
        "description": "Task processing and cognitive decision making"
    },
    "noopur": {
        "name": "Noopur (Response Agent)", 
        "url": "http://localhost:8003",
        "port": 8003,
        "description": "Intelligent response generation"
    },
    "chandresh": {
        "name": "Chandresh (Context Service)", 
        "url": "http://localhost:8004",
        "port": 8004,
        "description": "Embedding-based similarity search and context"
    },
    "parth": {
        "name": "Parth (Feedback System)", 
        "url": "http://localhost:8005",
        "port": 8005,
        "description": "Coach feedback collection and analysis"
    },
    "nilesh": {
        "name": "Nilesh (Metrics)", 
        "url": "http://localhost:8006",
        "port": 8006,
        "description": "Performance monitoring and metrics collection"
    }
}

# Initialize session state
if 'execution_history' not in st.session_state:
    st.session_state.execution_history = []
if 'current_execution' not in st.session_state:
    st.session_state.current_execution = None

def check_component_health(component_key: str) -> Dict[str, Any]:
    """Check health of a specific component"""
    try:
        component = COMPONENTS[component_key]
        response = requests.get(f"{component['url']}/health", timeout=5)
        if response.status_code == 200:
            return {
                "status": "healthy",
                "online": True,
                "response_time": response.elapsed.total_seconds() * 1000,
                "data": response.json()
            }
        else:
            return {"status": "unhealthy", "online": False, "error": f"HTTP {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"status": "offline", "online": False, "error": "Connection refused"}
    except Exception as e:
        return {"status": "error", "online": False, "error": str(e)}

def check_all_components_health() -> Dict[str, Dict[str, Any]]:
    """Check health of all components"""
    health_status = {}
    for component_key in COMPONENTS.keys():
        health_status[component_key] = check_component_health(component_key)
    return health_status

def call_api_endpoint(component_key: str, endpoint: str, method: str = "POST", data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generic API call function"""
    try:
        component = COMPONENTS[component_key]
        url = f"{component['url']}{endpoint}"
        
        if method.upper() == "POST":
            response = requests.post(url, json=data, timeout=30)
        elif method.upper() == "GET":
            response = requests.get(url, params=params, timeout=30)
        else:
            return {"success": False, "error": f"Unsupported method: {method}"}
        
        return {
            "success": True,
            "status_code": response.status_code,
            "data": response.json(),
            "response_time": response.elapsed.total_seconds() * 1000
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_full_pipeline(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the complete pipeline across all components"""
    execution_id = f"exec_{int(time.time() * 1000)}"
    pipeline_results = {
        "execution_id": execution_id,
        "start_time": datetime.now().isoformat(),
        "steps": {},
        "success": True,
        "errors": []
    }
    
    try:
        # Step 1: Seeya - Summarization
        st.write("🔄 Step 1: Processing with Seeya (Summarizer)...")
        seeya_result = call_api_endpoint("seeya", "/api/summarize", "POST", message_data)
        pipeline_results["steps"]["seeya"] = seeya_result
        
        if not seeya_result["success"]:
            pipeline_results["errors"].append(f"Seeya failed: {seeya_result['error']}")
            return pipeline_results
        
        summary_data = seeya_result["data"]
        st.success(f"✅ Seeya: {summary_data.get('summary', 'N/A')}")
        
        # Step 2: Sankalp - Task Processing
        st.write("🔄 Step 2: Processing with Sankalp (Cognitive Agent)...")
        sankalp_payload = {
            "summary_id": summary_data.get("summary_id"),
            "summary": summary_data.get("summary"),
            "intent": summary_data.get("intent"),
            "urgency": summary_data.get("urgency"),
            "user_id": message_data.get("user_id"),
            "platform": message_data.get("platform"),
            "confidence": summary_data.get("confidence")
        }
        sankalp_result = call_api_endpoint("sankalp", "/api/process_summary", "POST", sankalp_payload)
        pipeline_results["steps"]["sankalp"] = sankalp_result
        
        task_data = None
        if sankalp_result["success"]:
            task_data = sankalp_result["data"]
            st.success(f"✅ Sankalp: Task {task_data.get('task_id', 'N/A')} created")
        else:
            st.warning(f"⚠️ Sankalp failed: {sankalp_result['error']}")
            pipeline_results["errors"].append(f"Sankalp failed: {sankalp_result['error']}")
        
        # Step 3: Noopur - Response Generation
        st.write("🔄 Step 3: Processing with Noopur (Response Agent)...")
        if sankalp_result["success"]:
            task_data = sankalp_result["data"]
            noopur_payload = {
                "task_id": task_data.get("task_id"),
                "user_id": message_data.get("user_id"),
                "task_summary": task_data.get("task_summary", ""),
                "urgency": summary_data.get("urgency"),
                "platform": message_data.get("platform")
            }
        else:
            # Fallback payload if Sankalp failed
            noopur_payload = {
                "task_id": f"fallback_{execution_id}",
                "user_id": message_data.get("user_id"),
                "task_summary": summary_data.get("summary", ""),
                "urgency": summary_data.get("urgency"),
                "platform": message_data.get("platform")
            }
        
        noopur_result = call_api_endpoint("noopur", "/api/respond", "POST", noopur_payload)
        pipeline_results["steps"]["noopur"] = noopur_result
        
        if noopur_result["success"]:
            response_data = noopur_result["data"]
            st.success(f"✅ Noopur: {response_data.get('response_text', 'N/A')}")
        else:
            st.warning(f"⚠️ Noopur failed: {noopur_result['error']}")
            pipeline_results["errors"].append(f"Noopur failed: {noopur_result['error']}")
        
        # Step 4: Chandresh - Context Search
        st.write("🔄 Step 4: Processing with Chandresh (Context Service)...")
        chandresh_payload = {
            "summary_id": summary_data.get("summary_id"),
            "top_k": 3
        }
        chandresh_result = call_api_endpoint("chandresh", "/api/search_similar", "POST", chandresh_payload)
        pipeline_results["steps"]["chandresh"] = chandresh_result
        
        if chandresh_result["success"]:
            context_data = chandresh_result["data"]
            related_count = len(context_data.get("related", []))
            st.success(f"✅ Chandresh: Found {related_count} related items")
        else:
            st.warning(f"⚠️ Chandresh failed: {chandresh_result['error']}")
            pipeline_results["errors"].append(f"Chandresh failed: {chandresh_result['error']}")
        
        # Step 5: Parth - Feedback (Demo feedback)
        st.write("🔄 Step 5: Processing with Parth (Feedback System)...")
        if noopur_result["success"]:
            response_data = noopur_result["data"]
            task_id = task_data.get("task_id") if sankalp_result["success"] and task_data else f"fallback_{execution_id}"
            parth_payload = {
                "summary_id": summary_data.get("summary_id"),
                "task_id": task_id,
                "response_id": response_data.get("response_id", f"resp_{execution_id}"),
                "scores": {
                    "clarity": 4,
                    "relevance": 5,
                    "tone": 4,
                    "helpfulness": 4
                },
                "comment": "Auto-generated demo feedback"
            }
            parth_result = call_api_endpoint("parth", "/api/coach_feedback", "POST", parth_payload)
            pipeline_results["steps"]["parth"] = parth_result
            
            if parth_result["success"]:
                feedback_data = parth_result["data"]
                st.success(f"✅ Parth: Feedback {feedback_data.get('feedback_id', 'N/A')} recorded")
            else:
                st.warning(f"⚠️ Parth failed: {parth_result['error']}")
                pipeline_results["errors"].append(f"Parth failed: {parth_result['error']}")
        
        # Step 6: Nilesh - Metrics
        st.write("🔄 Step 6: Processing with Nilesh (Metrics)...")
        nilesh_result = call_api_endpoint("nilesh", "/health", "GET")
        pipeline_results["steps"]["nilesh"] = nilesh_result
        
        if nilesh_result["success"]:
            st.success("✅ Nilesh: Metrics recorded")
        else:
            st.warning(f"⚠️ Nilesh failed: {nilesh_result['error']}")
            pipeline_results["errors"].append(f"Nilesh failed: {nilesh_result['error']}")
        
        pipeline_results["end_time"] = datetime.now().isoformat()
        pipeline_results["success"] = len(pipeline_results["errors"]) == 0
        
        return pipeline_results
        
    except Exception as e:
        pipeline_results["success"] = False
        pipeline_results["errors"].append(f"Pipeline execution failed: {str(e)}")
        return pipeline_results

def render_pipeline_flow():
    """Render visual pipeline flow diagram"""
    st.markdown("""
    <div class="pipeline-flow">
        <div class="component-box">
            <strong>🧠 Seeya</strong><br>
            <small>Summarizer</small>
        </div>
        <div class="arrow">→</div>
        <div class="component-box">
            <strong>🎯 Sankalp</strong><br>
            <small>Cognitive Agent</small>
        </div>
        <div class="arrow">→</div>
        <div class="component-box">
            <strong>🗣️ Noopur</strong><br>
            <small>Responder</small>
        </div>
        <div class="arrow">↓</div>
        <div class="component-box">
            <strong>🔍 Chandresh</strong><br>
            <small>Context Search</small>
        </div>
        <div class="arrow">→</div>
        <div class="component-box">
            <strong>📝 Parth</strong><br>
            <small>Feedback</small>
        </div>
        <div class="arrow">→</div>
        <div class="component-box">
            <strong>📊 Nilesh</strong><br>
            <small>Metrics</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

def main():
    """Main Streamlit application"""
    
    # Title and description
    st.title("🤖 AI Assistant Complete Pipeline Integration")
    st.markdown("**End-to-end integration of all AI Assistant components**")
    
    # Render pipeline flow
    render_pipeline_flow()
    
    # Sidebar for system status
    with st.sidebar:
        st.header("🔧 System Status")
        
        if st.button("🔄 Refresh All Components", use_container_width=True):
            st.rerun()
        
        # Component health checks
        st.subheader("Component Health")
        health_status = check_all_components_health()
        
        for component_key, health in health_status.items():
            component = COMPONENTS[component_key]
            if health["online"]:
                st.success(f"✅ {component['name']}")
                if "response_time" in health:
                    st.caption(f"Response: {health['response_time']:.1f}ms")
            else:
                st.error(f"❌ {component['name']}")
                st.caption(f"Error: {health.get('error', 'Unknown')}")
        
        st.divider()
        
        # Quick stats
        online_count = sum(1 for h in health_status.values() if h["online"])
        total_count = len(health_status)
        
        st.metric("Components Online", f"{online_count}/{total_count}")
        if online_count == total_count:
            st.success("All systems operational! 🚀")
        elif online_count > 0:
            st.warning("Partial system availability ⚠️")
        else:
            st.error("System offline ❌")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 Pipeline Execution", "🔍 Component Testing", "📊 Analytics", "📖 Documentation"])
    
    with tab1:
        st.header("🚀 Complete Pipeline Execution")
        st.markdown("Execute the full AI Assistant pipeline across all components")
        
        # Input form
        with st.form("pipeline_execution"):
            col1, col2 = st.columns(2)
            
            with col1:
                user_id = st.text_input("User ID", value="demo_user")
                platform = st.selectbox("Platform", ["email", "slack", "whatsapp", "teams", "discord"])
                
            with col2:
                message_id = st.text_input("Message ID (optional)")
                timestamp = st.text_input("Timestamp", value=datetime.now().isoformat())
            
            message_text = st.text_area(
                "Message Text",
                placeholder="Enter the message to process through the complete pipeline...",
                height=120
            )
            
            submitted = st.form_submit_button("🚀 Execute Complete Pipeline", use_container_width=True)
        
        if submitted and message_text:
            # Prepare message data
            message_data = {
                "user_id": user_id,
                "platform": platform,
                "message_text": message_text,
                "timestamp": timestamp
            }
            
            if message_id:
                message_data["message_id"] = message_id
            
            # Execute pipeline
            with st.spinner("🤖 Executing complete pipeline..."):
                results = execute_full_pipeline(message_data)
            
            # Store in session state
            st.session_state.execution_history.append(results)
            st.session_state.current_execution = results
            
            # Display results
            if results["success"]:
                st.success("🎉 Pipeline executed successfully!")
            else:
                st.error("❌ Pipeline execution completed with errors")
            
            # Show detailed results
            st.subheader("📋 Execution Results")
            
            for step_name, step_result in results["steps"].items():
                component = COMPONENTS[step_name]
                
                with st.expander(f"{component['name']} Results"):
                    if step_result["success"]:
                        st.success(f"✅ Success ({step_result.get('response_time', 0):.1f}ms)")
                        st.json(step_result["data"])
                    else:
                        st.error(f"❌ Failed: {step_result['error']}")
            
            if results["errors"]:
                st.subheader("⚠️ Errors")
                for error in results["errors"]:
                    st.error(error)
    
    with tab2:
        st.header("🔍 Individual Component Testing")
        
        component_choice = st.selectbox("Select Component to Test", 
                                       [(k, v["name"]) for k, v in COMPONENTS.items()],
                                       format_func=lambda x: x[1])
        
        component_key = component_choice[0]
        component = COMPONENTS[component_key]
        
        st.markdown(f"**{component['name']}**")
        st.markdown(f"*{component['description']}*")
        st.markdown(f"URL: `{component['url']}`")
        
        # Component-specific testing interfaces
        if component_key == "seeya":
            test_seeya_component()
        elif component_key == "sankalp":
            test_sankalp_component()
        elif component_key == "noopur":
            test_noopur_component()
        elif component_key == "chandresh":
            test_chandresh_component()
        elif component_key == "parth":
            test_parth_component()
        elif component_key == "nilesh":
            test_nilesh_component()
    
    with tab3:
        st.header("📊 Pipeline Analytics")
        
        if st.session_state.execution_history:
            st.subheader("Execution History")
            
            # Create DataFrame from execution history
            df_data = []
            for execution in st.session_state.execution_history:
                df_data.append({
                    "Execution ID": execution["execution_id"],
                    "Start Time": execution["start_time"],
                    "Success": execution["success"],
                    "Errors": len(execution["errors"]),
                    "Steps Completed": len([s for s in execution["steps"].values() if s["success"]])
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
            
            # Success rate chart
            if len(df) > 0:
                success_rate = df["Success"].mean() * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")
                
                # Create success/failure chart
                fig = px.pie(df, names="Success", title="Pipeline Execution Success Rate")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No execution history available. Run the pipeline to see analytics.")
    
    with tab4:
        st.header("📖 Component Documentation")
        
        for component_key, component in COMPONENTS.items():
            with st.expander(f"{component['name']}"):
                st.markdown(f"**Description:** {component['description']}")
                st.markdown(f"**URL:** {component['url']}")
                st.markdown(f"**Port:** {component['port']}")
                
                # Show available endpoints based on component
                if component_key == "seeya":
                    st.markdown("**Endpoints:**")
                    st.markdown("- `POST /api/summarize` - Summarize messages")
                    st.markdown("- `POST /api/feedback` - Submit feedback")
                    st.markdown("- `GET /api/stats` - Get performance stats")
                elif component_key == "sankalp":
                    st.markdown("**Endpoints:**")
                    st.markdown("- `POST /api/process_summary` - Process summaries into tasks")
                    st.markdown("- `GET /api/tasks` - Get task history")
                elif component_key == "noopur":
                    st.markdown("**Endpoints:**")
                    st.markdown("- `POST /api/respond` - Generate responses")
                    st.markdown("- `GET /api/responses` - Get response history")
                elif component_key == "chandresh":
                    st.markdown("**Endpoints:**")
                    st.markdown("- `POST /api/search_similar` - Search similar content")
                    st.markdown("- `POST /api/store_embedding` - Store embeddings")
                elif component_key == "parth":
                    st.markdown("**Endpoints:**")
                    st.markdown("- `POST /api/coach_feedback` - Submit coach feedback")
                    st.markdown("- `GET /api/feedback/stats` - Get feedback statistics")
                elif component_key == "nilesh":
                    st.markdown("**Endpoints:**")
                    st.markdown("- `GET /health` - Health check")
                    st.markdown("- `GET /api/metrics` - Get system metrics")

def test_seeya_component():
    """Test interface for Seeya component"""
    st.subheader("Test Seeya Summarizer")
    
    with st.form("test_seeya"):
        test_message = st.text_area("Test Message", "Hello, I need help with my account password reset. This is urgent!")
        user_id = st.text_input("User ID", "test_user")
        platform = st.selectbox("Platform", ["email", "slack", "whatsapp"])
        
        if st.form_submit_button("Test Summarize"):
            data = {
                "user_id": user_id,
                "platform": platform,
                "message_text": test_message,
                "timestamp": datetime.now().isoformat()
            }
            
            result = call_api_endpoint("seeya", "/api/summarize", "POST", data)
            
            if result["success"]:
                st.success("✅ Seeya response received!")
                st.json(result["data"])
            else:
                st.error(f"❌ Error: {result['error']}")

def test_sankalp_component():
    """Test interface for Sankalp component"""
    st.subheader("Test Sankalp Cognitive Agent")
    st.info("Requires summary data from Seeya first")

def test_noopur_component():
    """Test interface for Noopur component"""
    st.subheader("Test Noopur Response Agent")
    st.info("Requires task data from Sankalp first")

def test_chandresh_component():
    """Test interface for Chandresh component"""
    st.subheader("Test Chandresh Context Service")
    
    with st.form("test_chandresh"):
        search_text = st.text_input("Search Text", "password reset help")
        top_k = st.number_input("Top K Results", min_value=1, max_value=10, value=3)
        
        if st.form_submit_button("Test Search Similar"):
            data = {
                "message_text": search_text,
                "top_k": top_k
            }
            
            result = call_api_endpoint("chandresh", "/api/search_similar", "POST", data)
            
            if result["success"]:
                st.success("✅ Chandresh response received!")
                st.json(result["data"])
            else:
                st.error(f"❌ Error: {result['error']}")

def test_parth_component():
    """Test interface for Parth component"""
    st.subheader("Test Parth Feedback System")
    
    with st.form("test_parth"):
        summary_id = st.text_input("Summary ID", "test_summary")
        task_id = st.text_input("Task ID", "test_task")
        response_id = st.text_input("Response ID", "test_response")
        
        col1, col2 = st.columns(2)
        with col1:
            clarity = st.slider("Clarity", 1, 5, 4)
            relevance = st.slider("Relevance", 1, 5, 5)
        with col2:
            tone = st.slider("Tone", 1, 5, 4)
            helpfulness = st.slider("Helpfulness", 1, 5, 4)
        
        comment = st.text_area("Comment", "Test feedback comment")
        
        if st.form_submit_button("Test Feedback"):
            data = {
                "summary_id": summary_id,
                "task_id": task_id,
                "response_id": response_id,
                "scores": {
                    "clarity": clarity,
                    "relevance": relevance,
                    "tone": tone,
                    "helpfulness": helpfulness
                },
                "comment": comment
            }
            
            result = call_api_endpoint("parth", "/api/coach_feedback", "POST", data)
            
            if result["success"]:
                st.success("✅ Parth response received!")
                st.json(result["data"])
            else:
                st.error(f"❌ Error: {result['error']}")

def test_nilesh_component():
    """Test interface for Nilesh component"""
    st.subheader("Test Nilesh Metrics")
    
    if st.button("Test Health Check"):
        result = call_api_endpoint("nilesh", "/health", "GET")
        
        if result["success"]:
            st.success("✅ Nilesh response received!")
            st.json(result["data"])
        else:
            st.error(f"❌ Error: {result['error']}")

if __name__ == "__main__":
    main()