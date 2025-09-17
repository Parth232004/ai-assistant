#!/usr/bin/env python3
"""
Streamlit Metrics Dashboard - Nilesh's UI Component

This dashboard provides:
1. Real-time metrics visualization
2. Performance monitoring charts
3. API call logs and analysis
4. Service health monitoring
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json

# Page configuration
st.set_page_config(
    page_title="AI Assistant Metrics Dashboard",
    page_icon="📊",
    layout="wide"
)

# API Configuration
METRICS_API_BASE = "http://localhost:8001"  # Nilesh's metrics API
CHANDRESH_API_BASE = "http://localhost:8000"  # Chandresh's API for integration

def fetch_metrics(hours=24):
    """Fetch metrics from Nilesh's API."""
    try:
        response = requests.get(f"{METRICS_API_BASE}/api/metrics?hours={hours}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch metrics: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to metrics API. Make sure the server is running.")
        return None
    except Exception as e:
        st.error(f"Error fetching metrics: {e}")
        return None

def fetch_recent_calls(limit=50):
    """Fetch recent API calls."""
    try:
        response = requests.get(f"{METRICS_API_BASE}/api/metrics/recent?limit={limit}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def fetch_trends(hours=24):
    """Fetch performance trends."""
    try:
        response = requests.get(f"{METRICS_API_BASE}/api/metrics/trends?hours={hours}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def main():
    """Main Streamlit dashboard."""
    
    st.title("🚀 AI Assistant Metrics Dashboard")
    st.markdown("*Nilesh's Metrics, Logging & Execution Tracking*")
    
    # Sidebar controls
    st.sidebar.header("⚙️ Dashboard Controls")
    
    # Time window selection
    time_window = st.sidebar.selectbox(
        "Time Window",
        options=[1, 6, 12, 24, 48, 168],  # 1h, 6h, 12h, 1d, 2d, 1w
        index=3,  # Default to 24h
        format_func=lambda x: f"{x} hour{'s' if x != 1 else ''}" if x < 24 else f"{x//24} day{'s' if x//24 != 1 else ''}"
    )
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    
    if auto_refresh:
        time.sleep(30)
        st.experimental_rerun()
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.experimental_rerun()
    
    # Fetch data
    with st.spinner("Loading metrics..."):
        metrics_data = fetch_metrics(hours=time_window)
        recent_calls = fetch_recent_calls(limit=100)
        trends_data = fetch_trends(hours=time_window)
    
    if not metrics_data:
        st.error("Unable to load metrics data. Please check if the metrics API is running.")
        st.info("Start the metrics API with: `uvicorn api_nilesh:app --reload --port 8001`")
        return
    
    # Main metrics overview
    st.header("📊 Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total API Calls",
            value=metrics_data.get("api_metrics", {}).get("total_calls", 0),
            delta=None
        )
    
    with col2:
        avg_latency = metrics_data.get("avg_latency_ms", 0)
        st.metric(
            label="Avg Latency",
            value=f"{avg_latency:.1f} ms",
            delta=None,
            delta_color="inverse"
        )
    
    with col3:
        error_rate = metrics_data.get("error_rate", 0) * 100
        st.metric(
            label="Error Rate",
            value=f"{error_rate:.2f}%",
            delta=None,
            delta_color="inverse"
        )
    
    with col4:
        status = metrics_data.get("service_status", "unknown")
        status_color = "🟢" if status == "active" else "🔴"
        st.metric(
            label="Service Status",
            value=f"{status_color} {status.title()}"
        )
    
    # Pipeline metrics
    st.header("🔄 Pipeline Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📝 Content Pipeline")
        st.metric("Messages", metrics_data.get("total_messages", 0))
        st.metric("Summaries", metrics_data.get("total_summaries", 0))
        st.metric("Tasks", metrics_data.get("total_tasks", 0))
    
    with col2:
        st.subheader("🤖 AI Pipeline")
        st.metric("Responses", metrics_data.get("total_responses", 0))
        st.metric("Embeddings", metrics_data.get("total_embeddings", 0))
        st.metric("Feedback", metrics_data.get("total_feedback", 0))
    
    with col3:
        st.subheader("📈 Pipeline Health")
        total_messages = metrics_data.get("total_messages", 0)
        total_responses = metrics_data.get("total_responses", 0)
        
        if total_messages > 0:
            completion_rate = (total_responses / total_messages) * 100
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        else:
            st.metric("Completion Rate", "N/A")
        
        # Pipeline efficiency
        if total_messages > 0:
            efficiency = (metrics_data.get("total_embeddings", 0) / total_messages) * 100
            st.metric("Embedding Rate", f"{efficiency:.1f}%")
        else:
            st.metric("Embedding Rate", "N/A")
    
    # API Endpoint Statistics
    st.header("🔌 API Endpoint Statistics")
    
    endpoint_stats = metrics_data.get("endpoint_stats", [])
    if endpoint_stats:
        df_endpoints = pd.DataFrame(endpoint_stats)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Calls by endpoint
            fig = px.bar(
                df_endpoints, 
                x='endpoint', 
                y='calls',
                title="API Calls by Endpoint",
                color='calls',
                color_continuous_scale='viridis'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Average latency by endpoint
            fig = px.bar(
                df_endpoints,
                x='endpoint',
                y='avg_latency_ms', 
                title="Average Latency by Endpoint",
                color='avg_latency_ms',
                color_continuous_scale='reds'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed endpoint table
        st.subheader("📋 Endpoint Details")
        st.dataframe(df_endpoints, use_container_width=True)
    else:
        st.info("No endpoint statistics available yet.")
    
    # Performance Trends
    if trends_data and trends_data.get("hourly_trends"):
        st.header("📈 Performance Trends")
        
        trends = trends_data["hourly_trends"]
        df_trends = pd.DataFrame(trends)
        df_trends['hour'] = pd.to_datetime(df_trends['hour'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Calls over time
            fig = px.line(
                df_trends,
                x='hour',
                y='calls',
                title="API Calls Over Time"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Latency over time
            fig = px.line(
                df_trends,
                x='hour',
                y='avg_latency_ms',
                title="Average Latency Over Time",
                color_discrete_sequence=['red']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Error rate over time
        if any(df_trends['errors'] > 0):
            fig = px.line(
                df_trends,
                x='hour',
                y='error_rate',
                title="Error Rate Over Time",
                color_discrete_sequence=['orange']
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent API Calls
    st.header("📝 Recent API Calls")
    
    if recent_calls and recent_calls.get("recent_calls"):
        calls = recent_calls["recent_calls"]
        df_calls = pd.DataFrame(calls)
        
        # Status code color mapping
        def get_status_color(status_code):
            if status_code < 300:
                return "🟢"
            elif status_code < 400:
                return "🟡"
            else:
                return "🔴"
        
        df_calls['status_indicator'] = df_calls['status_code'].apply(get_status_color)
        df_calls['latency_ms'] = df_calls['latency_ms'].round(2)
        
        # Show recent calls
        st.dataframe(
            df_calls[['timestamp', 'endpoint', 'status_indicator', 'status_code', 'latency_ms']],
            use_container_width=True,
            column_config={
                "timestamp": "Time",
                "endpoint": "Endpoint",
                "status_indicator": "Status",
                "status_code": "Code",
                "latency_ms": "Latency (ms)"
            }
        )
        
        # Call distribution
        if len(df_calls) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                status_dist = df_calls['status_code'].value_counts()
                fig = px.pie(
                    values=status_dist.values,
                    names=status_dist.index,
                    title="Status Code Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                endpoint_dist = df_calls['endpoint'].value_counts().head(10)
                fig = px.pie(
                    values=endpoint_dist.values,
                    names=endpoint_dist.index,
                    title="Top Endpoints (Recent Calls)"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("No recent API calls data available.")
    
    # Service Integration Status
    st.header("🔗 Service Integration Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🧠 Chandresh's Embedding Service")
        try:
            response = requests.get(f"{CHANDRESH_API_BASE}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ Embedding Service Online")
                health_data = response.json()
                st.json(health_data)
            else:
                st.error("❌ Embedding Service Error")
        except:
            st.error("❌ Embedding Service Offline")
    
    with col2:
        st.subheader("📊 Nilesh's Metrics Service")
        try:
            response = requests.get(f"{METRICS_API_BASE}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ Metrics Service Online")
                health_data = response.json()
                st.json(health_data)
            else:
                st.error("❌ Metrics Service Error")
        except:
            st.error("❌ Metrics Service Offline")
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"**Dashboard Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"**Data Window:** {time_window} hours | "
        f"**Owner:** Nilesh (Metrics, Logging & Execution Tracking)"
    )

if __name__ == "__main__":
    main()