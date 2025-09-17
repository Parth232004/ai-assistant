import os
from typing import Any, Dict

import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Page configuration
st.set_page_config(page_title="Assistant Demo", layout="wide")
st.title("Assistant Live Demo 🚀")

# -----------------------------
# Configuration & Constants
# -----------------------------

def get_config_value(key: str, default: str) -> str:
    # Prefer environment variable; fall back to Streamlit secrets if available.
    env_val = os.getenv(key)
    if env_val:
        return env_val
    try:
        # Accessing st.secrets can raise if no secrets.toml is configured.
        secrets = st.secrets  # type: ignore[attr-defined]
        if key in secrets:
            return str(secrets[key])
    except Exception:
        pass
    return default

DEFAULT_API_URL = get_config_value("API_URL", "http://127.0.0.1:8000/api/respond")
DEFAULT_TASK_ID = os.getenv("DEFAULT_TASK_ID", "t123")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))

# -----------------------------
# HTTP Session with Retries
# -----------------------------
session = requests.Session()

# Configure robust retries for transient errors
try:
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods={"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"},
        raise_on_status=False,
    )
except TypeError:
    # Fallback for older urllib3 versions using method_whitelist
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist={"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"},
        raise_on_status=False,
    )

adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)


# -----------------------------
# API Call Logic
# -----------------------------
def send_response(task_id: str, api_url: str, timeout: int = REQUEST_TIMEOUT_SECONDS) -> Dict[str, Any]:
    """Send the response request to the backend API and return parsed JSON.

    Raises:
        requests.exceptions.HTTPError: For non-2xx responses.
        requests.exceptions.RequestException: For network/connection errors.
        ValueError: If the response is not JSON or JSON decoding fails.
    """
    resp = session.post(api_url, json={"task_id": task_id}, timeout=timeout)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")
    if "application/json" not in content_type.lower():
        # Not JSON – provide clear message for the UI to surface
        raise ValueError(f"Unexpected Content-Type: {content_type}")

    try:
        return resp.json()
    except ValueError as e:
        raise ValueError("Failed to decode JSON response") from e


# -----------------------------
# UI Controls
# -----------------------------
st.sidebar.header("Configuration")
api_url_input = st.sidebar.text_input("API URL", value=DEFAULT_API_URL)

st.header("Task")
task_id = st.text_input("Task ID", value=DEFAULT_TASK_ID)
st.write(f"Current Task ID: {task_id}")

# -----------------------------
# Response Section
# -----------------------------
st.header("Response")
if st.button("Send Response"):
    with st.spinner("Contacting API and generating response…"):
        try:
            data = send_response(task_id, api_url_input)
        except requests.exceptions.HTTPError as http_err:
            status_code = getattr(http_err.response, "status_code", None)
            st.error(f"Request failed with HTTP status: {status_code if status_code else 'Unknown'}")
            with st.expander("Error details", expanded=False):
                st.text(str(http_err))
                try:
                    if http_err.response is not None and http_err.response.text:
                        st.code(http_err.response.text, language="json")
                except Exception:
                    pass
        except requests.exceptions.RequestException as req_err:
            st.error("Network error while contacting the API.")
            with st.expander("Error details", expanded=False):
                st.text(str(req_err))
        except ValueError as val_err:
            st.error(str(val_err))
        else:
            # Safely extract fields from payload
            status = data.get("status", "unknown")
            response_text = data.get("response_text", "")
            tone = data.get("tone", "unknown")
            timestamp = data.get("timestamp", "")
            flag_reason = data.get("flag_reason")

            if status == "flagged":
                st.warning("⚠️ This response was flagged by the safety filter.")
                if flag_reason:
                    st.caption(f"Reason: {flag_reason}")
            else:
                st.success("Response generated successfully!")

            st.markdown("**Response Text:**")
            st.text(response_text or "(empty)")

            st.markdown(f"**Tone:** {tone}")
            st.markdown(f"**Status:** {status}")
            if timestamp:
                st.caption(f"Timestamp: {timestamp}")

            with st.expander("Raw API response", expanded=False):
                try:
                    st.json(data)
                except Exception:
                    st.text(str(data))
