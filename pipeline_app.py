import os
import sys
import json
import glob
import sqlite3
import platform
from pathlib import Path

import streamlit as st

# App configuration
st.set_page_config(
    page_title="AI Assistant Pipeline",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent


def path_exists(rel_path: str) -> bool:
    return (BASE_DIR / rel_path).exists()


def code_block(cmd: str):
    st.code(cmd, language="bash")


def show_overview():
    st.title("AI Assistant Pipeline")
    st.write(
        """
        This Streamlit app acts as a simple control panel for the projects in this repository.
        
        Use the sidebar to navigate:
        - Overview: Quick start and repository layout
        - Subprojects: Discover runnable components and commands
        - DB Inspector: Peek into local SQLite databases if present
        - Diagnostics: Environment checks and helpful info
        """
    )

    st.subheader("Quick start")
    st.write("Run from the repository root:")
    code_block("streamlit run pipeline_app.py")

    st.subheader("Repository layout (top-level excerpt)")
    entries = sorted([p.name + ("/" if p.is_dir() else "") for p in BASE_DIR.iterdir() if not p.name.startswith('.')])
    cols = st.columns(3)
    for i, entry in enumerate(entries):
        with cols[i % 3]:
            st.write(f"- {entry}")


def show_subprojects():
    st.header("Subprojects and launch commands")

    # Assistant Live-Bridge
    alb_dir = BASE_DIR / "Assistant-Live-Demo-main 2" / "Assistant-Live-Bridge"
    alb_exists = alb_dir.exists()

    with st.expander("Assistant-Live-Bridge (Streamlit + FastAPI)", expanded=True):
        if alb_exists:
            st.success(f"Found: {alb_dir}")
            req = alb_dir / "requirements.txt"
            demo_app = alb_dir / "demo_streamlit_app.py"
            api_entry = alb_dir / "main.py"
            env_example = alb_dir / ".env.example"

            st.write("Install dependencies (recommended in a virtualenv):")
            if req.exists():
                code_block(f"pip install -r '{req.relative_to(BASE_DIR)}'")
            else:
                st.warning("requirements.txt not found in Assistant-Live-Bridge")

            st.write("Run the API server:")
            if api_entry.exists():
                code_block(f"python '{api_entry.relative_to(BASE_DIR)}'")
            else:
                st.info("API entrypoint not found (main.py)")

            st.write("Run the Streamlit dashboard:")
            if demo_app.exists():
                code_block(f"streamlit run '{demo_app.relative_to(BASE_DIR)}'")
            else:
                st.info("Demo Streamlit app not found (demo_streamlit_app.py)")

            if env_example.exists():
                st.write("Copy config template if needed:")
                code_block(f"cp '{env_example.relative_to(BASE_DIR)}' '{(alb_dir / '.env').relative_to(BASE_DIR)}'")
        else:
            st.warning("Assistant-Live-Bridge not found. Skipping.")

    # Assistant Live Demo (standalone)
    ald_dir = BASE_DIR / "assistant-live-demo"
    if ald_dir.exists():
        with st.expander("Assistant Live Demo (standalone)"):
            req = ald_dir / "requirements.txt"
            st.write("Install:")
            if req.exists():
                code_block(f"pip install -r '{req.relative_to(BASE_DIR)}'")
            else:
                st.info("requirements.txt not found here")
            demo = ald_dir / "streamlit" / "demo_streamlit.py"
            if demo.exists():
                st.write("Run demo:")
                code_block(f"streamlit run '{demo.relative_to(BASE_DIR)}'")
            else:
                st.info("No Streamlit demo file found")

    # Noopurr demo
    noop_dir = BASE_DIR / "noopurr"
    if noop_dir.exists():
        with st.expander("Noopurr Demo"):
            demo = noop_dir / "streamlit" / "demo_streamlit.py"
            req = noop_dir / "requirements.txt"
            if req.exists():
                st.write("Install:")
                code_block(f"pip install -r '{req.relative_to(BASE_DIR)}'")
            else:
                st.info("No requirements.txt found; try installing minimal dependencies manually.")
            if demo.exists():
                st.write("Run demo:")
                code_block(f"streamlit run '{demo.relative_to(BASE_DIR)}'")
            else:
                st.info("Streamlit demo not found for Noopurr")

    st.caption("Note: Use quotes around paths with spaces when running shell commands.")


def show_db_inspector():
    st.header("SQLite DB Inspector")
    db_candidates = [
        BASE_DIR / "assistant_demo.db",
        BASE_DIR / "assistant-live-demo" / "assistant_demo.db",
        BASE_DIR / "chandresh" / "assistant_demo.db",
        BASE_DIR / "nil-main" / "assistant_demo.db",
    ]

    existing = [p for p in db_candidates if p.exists()]
    if not existing:
        st.info("No known SQLite database files found. Place a .db file in the project root to inspect.")
        return

    db_path = st.selectbox("Select a database to inspect", existing, format_func=lambda p: str(p.relative_to(BASE_DIR)))
    if not db_path:
        return

    try:
        with sqlite3.connect(str(db_path)) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
            tables = [r[0] for r in cur.fetchall()]
            if not tables:
                st.warning("No tables found in this database.")
                return

            st.write(f"Tables in {db_path.name}:")
            st.write(tables)

            table = st.selectbox("Preview table", tables)
            limit = st.slider("Rows to preview", 1, 100, 10)
            q = f"SELECT * FROM {table} LIMIT {limit};"
            try:
                rows = conn.execute(q).fetchall()
                cols = [d[1] for d in conn.execute(f"PRAGMA table_info({table});").fetchall()]
                st.write(f"Previewing {len(rows)} rows from '{table}':")
                st.dataframe(rows, use_container_width=True)
                with st.expander("Columns"):
                    st.write(cols)
            except Exception as e:
                st.error(f"Failed to preview: {e}")
    except Exception as e:
        st.error(f"Could not open database: {e}")


def show_diagnostics():
    st.header("Diagnostics")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Environment")
        st.write({
            "python": sys.version.split(" (")[0],
            "platform": platform.platform(),
            "executable": sys.executable,
            "cwd": str(BASE_DIR),
            "streamlit": st.__version__,
        })

        # Optional: check presence of common packages
        status = {}
        for pkg in ["pandas", "numpy", "requests", "pydantic", "fastapi"]:
            try:
                __import__(pkg)
                status[pkg] = "OK"
            except Exception as e:
                status[pkg] = f"missing ({e.__class__.__name__})"
        st.write({"packages": status})

    with col2:
        st.subheader("Project sanity checks")
        checks = {
            "Assistant-Live-Bridge dir": path_exists("Assistant-Live-Demo-main 2/Assistant-Live-Bridge"),
            "pipeline_app.py exists": (BASE_DIR / "pipeline_app.py").exists(),
            "Root DB exists": (BASE_DIR / "assistant_demo.db").exists(),
        }
        st.write(checks)

        st.subheader("Useful commands")
        code_block("streamlit run pipeline_app.py --server.address 127.0.0.1 --server.port 8501")
        code_block("pip install -r 'Assistant-Live-Demo-main 2/Assistant-Live-Bridge/requirements.txt'")


# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Overview",
        "Subprojects",
        "DB Inspector",
        "Diagnostics",
    ],
)

if page == "Overview":
    show_overview()
elif page == "Subprojects":
    show_subprojects()
elif page == "DB Inspector":
    show_db_inspector()
elif page == "Diagnostics":
    show_diagnostics()

st.sidebar.markdown("---")
st.sidebar.caption("Tip: If you see a blank page, clear browser cache or do a hard refresh (Cmd+Shift+R/Ctrl+F5).")
