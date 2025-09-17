import os
from typing import Any, Dict, Optional

import requests
import streamlit as st

# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(page_title="Assistant Demo", layout="wide")
st.title("Assistant Live Demo 🚀")

# -----------------------------
# Sidebar configuration
# -----------------------------
API_BASE_DEFAULT = os.getenv("API_BASE", "http://127.0.0.1:8000")
st.sidebar.header("Configuration")
api_base = st.sidebar.text_input("API Base URL", value=API_BASE_DEFAULT, help="FastAPI server base URL")

if "last_task_id" not in st.session_state:
    st.session_state.last_task_id = "t123"
if "last_response_id" not in st.session_state:
    st.session_state.last_response_id = None
if "last_summary_id" not in st.session_state:
    st.session_state.last_summary_id = "s1"

# -----------------------------
# Helpers
# -----------------------------

def post_json(path: str, payload: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
    url = f"{api_base}{path}"
    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def get_json(path: str, timeout: int = 10) -> Dict[str, Any]:
    url = f"{api_base}{path}"
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json()

# -----------------------------
# Tabs: Respond, Recall, Feedback, Metrics
# -----------------------------

tab1, tab2, tab3, tab4 = st.tabs(["Respond", "Recall", "Feedback", "Metrics"])

# Respond Tab
with tab1:
    st.header("Respond to Task")
    col_a, col_b = st.columns([2, 1])

    with col_a:
        task_id = st.text_input("Task ID", value=st.session_state.last_task_id)
        user_id = st.text_input("User ID", value="u1")
        if st.button("Send Response", type="primary"):
            with st.spinner("Generating response..."):
                try:
                    data = post_json(
                        "/api/respond",
                        {"task_id": task_id, "user_id": user_id},
                        timeout=15,
                    )
                    st.success("Response generated!")
                    st.session_state.last_task_id = data.get("task_id", task_id)
                    st.session_state.last_response_id = data.get("response_id")

                    st.markdown("### Response")
                    st.code(data, language="json")
                except requests.exceptions.RequestException as e:
                    st.error(f"Request failed: {e}")

    with col_b:
        st.caption("Quick seed for embeddings (optional)")
        with st.form("seed_form"):
            seed_item_type = st.selectbox("Item Type", ["summary", "task"], index=0)
            seed_item_id = st.text_input("Item ID", value="s1")
            seed_text = st.text_area("Text", value="hotel booking confirmation and itinerary")
            submitted = st.form_submit_button("Seed Embedding")
            if submitted:
                try:
                    url = f"{api_base}/api/store_embedding"
                    resp = requests.post(url, params={"item_type": seed_item_type, "item_id": seed_item_id, "text": seed_text}, timeout=10)
                    if resp.status_code == 200 and resp.json().get("stored"):
                        st.success("Embedding stored")
                        st.session_state.last_summary_id = seed_item_id if seed_item_type == "summary" else st.session_state.last_summary_id
                    else:
                        st.warning("Store embedding returned unexpected result")
                except Exception as e:
                    st.error(f"Error seeding embedding: {e}")

# Recall Tab
with tab2:
    st.header("Related Past Context (Recall)")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("By Message Text")
        q_text = st.text_area("Message", value="need help booking a hotel")
        top_k = st.slider("Top K", min_value=1, max_value=10, value=3)
        if st.button("Search by Message"):
            with st.spinner("Searching similar..."):
                try:
                    data = post_json("/api/search_similar", {"message_text": q_text, "top_k": top_k})
                    items = data.get("related", [])
                    if not items:
                        st.info("No related items found.")
                    else:
                        for it in items:
                            st.write(f"- {it['item_type']} {it['item_id']}: score={it['score']:.3f}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Search failed: {e}")

    with col2:
        st.subheader("By Summary ID")
        sid = st.text_input("Summary ID", value=st.session_state.last_summary_id)
        top_k2 = st.slider("Top K (summary)", min_value=1, max_value=10, value=3, key="topk2")
        if st.button("Search by Summary"):
            with st.spinner("Searching similar..."):
                try:
                    data = post_json("/api/search_similar", {"summary_id": sid, "top_k": top_k2})
                    items = data.get("related", [])
                    if not items:
                        st.info("No related items found.")
                    else:
                        for it in items:
                            st.write(f"- {it['item_type']} {it['item_id']}: score={it['score']:.3f}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Search failed: {e}")

# Feedback Tab
with tab3:
    st.header("Coach Feedback")
    with st.form("feedback_form"):
        summary_id = st.text_input("Summary ID", value=st.session_state.last_summary_id)
        task_id_fb = st.text_input("Task ID", value=st.session_state.last_task_id)
        response_id = st.text_input("Response ID", value=st.session_state.last_response_id or "")
        st.markdown("Scores")
        c1, c2, c3 = st.columns(3)
        with c1:
            clarity = st.slider("Clarity", 1, 5, 4)
        with c2:
            relevance = st.slider("Relevance", 1, 5, 5)
        with c3:
            tone = st.slider("Tone", 1, 5, 4)
        comment = st.text_area("Comment", value="good")
        submitted_fb = st.form_submit_button("Submit Feedback")
        if submitted_fb:
            payload = {
                "summary_id": summary_id,
                "task_id": task_id_fb,
                "response_id": response_id,
                "scores": {"clarity": clarity, "relevance": relevance, "tone": tone},
                "comment": comment,
            }
            with st.spinner("Submitting feedback..."):
                try:
                    data = post_json("/api/coach_feedback", payload)
                    st.success(f"Saved feedback {data.get('feedback_id')} with score {data.get('score')}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Feedback failed: {e}")

# Metrics Tab
with tab4:
    st.header("Metrics")
    if st.button("Refresh Metrics"):
        st.experimental_rerun()

    try:
        metrics = get_json("/api/metrics")
        colm1, colm2, colm3, colm4 = st.columns(4)
        with colm1:
            st.metric("Total API Calls", metrics.get("api_metrics", {}).get("total_calls", 0))
        with colm2:
            st.metric("Avg Latency (ms)", f"{metrics.get('avg_latency_ms', 0.0):.1f}")
        with colm3:
            st.metric("Error Rate", f"{metrics.get('error_rate', 0.0)*100:.2f}%")
        with colm4:
            st.metric("Total Responses", metrics.get("total_responses", 0))

        st.subheader("Endpoint Stats")
        es = metrics.get("endpoint_stats", [])
        if es:
            import pandas as pd

            df = pd.DataFrame(es)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No endpoint metrics yet. Generate some traffic using the tabs above.")
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load metrics: {e}")
