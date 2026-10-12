"""AI-Powered Intelligent Automation System.

Main Application Entrypoint.
Internship Evaluation Project.

Architecture:
- Tab 1: Excel Inventory AI Agent (Pandas, Safe NLQ Engine, Glossary Tool)
- Tab 2: Document Support Assistant (PDF/DOCX/TXT Retrieval, 10-Turn Demo, Topic Switching)
- Tab 3: Identity & Insurance Document Processor (10 Document Types, OCR, Confidence Scoring, PII Masking)
"""

import streamlit as st

# Configure page layout and visual branding
st.set_page_config(
    page_title="AI-Powered Intelligent Automation System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for a polished, modern, professional look
st.markdown("""
<style>
    /* Metric Card Styling */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E88E5;
    }
    /* Tab Styling */
    button[data-baseweb="tab"] {
        font-size: 1.05rem;
        font-weight: 600;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    /* Header Container */
    .app-header {
        background: linear-gradient(135deg, #0d47a1 0%, #1976d2 50%, #42a5f5 100%);
        padding: 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .app-header h1 {
        color: white !important;
        margin: 0;
        font-size: 2.1rem;
        font-weight: 700;
    }
    .app-header p {
        color: #e3f2fd !important;
        margin-top: 6px;
        margin-bottom: 0;
        font-size: 1.05rem;
    }
    /* Card badge */
    .badge-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 16px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Import module renderers
from modules.inventory_agent import render_inventory_agent_tab
from modules.document_assistant import render_document_assistant_tab
from modules.document_processor import render_document_processor_tab
from utils.ocr_engine import is_tesseract_available


def main():
    # Application Header Banner
    st.markdown("""
    <div class="app-header">
        <h1>🤖 AI-Powered Intelligent Automation System</h1>
        <p>Enterprise Automation Platform for Inventory Intelligence, Document QA, and Insurance Document Processing</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar Navigation & System Diagnostics
    with st.sidebar:
        st.markdown("### 📌 System Overview")
        st.markdown(
            "This multi-module automation system was built for **Internship Evaluation** "
            "implementing end-to-end data processing, grounded document retrieval, and compliance document classification."
        )

        st.markdown("---")
        st.markdown("### 🛠️ Modules Directory")
        st.markdown("""
        1. **📊 Module 1: Excel Inventory Agent**
           - Safe Natural Language Query Engine
           - Inventory Health & Valuation KPIs
           - Supply Chain Glossary Search
        2. **📑 Module 2: Document Support Assistant**
           - Multi-Format RAG (PDF, DOCX, TXT)
           - Context-Aware Multi-Turn History
           - 10-Turn Demonstration Suite
        3. **🛡️ Module 3: Identity & Insurance Processor**
           - 10 Document Types Classifier
           - Field Extraction with Confidence Scores
           - PII Masking & Human Review Flagging
        """)

        st.markdown("---")
        st.markdown("### 🔍 System Environment")
        tess_ok, tess_msg = is_tesseract_available()
        if tess_ok:
            st.success("OCR Engine: Tesseract Active ✅")
        else:
            st.info("OCR Engine: Fallback Mode Active ℹ️\n\n(Standard text documents work out-of-the-box)")

        st.markdown("---")
        st.caption("Internship Evaluation Project | Python 3.14 + Streamlit")

    # Main Application Tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Module 1: Excel Inventory AI Agent",
        "📑 Module 2: Document Support Assistant",
        "🛡️ Module 3: Identity & Insurance Document Processor"
    ])

    with tab1:
        render_inventory_agent_tab()

    with tab2:
        render_document_assistant_tab()

    with tab3:
        render_document_processor_tab()


if __name__ == "__main__":
    main()
