"""Module 2: Document Support Assistant.

Features:
- Multi-document upload (PDF, DOCX, TXT).
- Grounded semantic retrieval and extractive QA.
- Source attribution (Filename, Section/Page, and confidence score).
- Conversation history maintenance in session state.
- Avoids repeating identical answers unnecessarily.
- Explicit topic change detection and smooth transitions.
- Interactive 10-Turn Conversation Demonstration Scenario.
"""

import os
import streamlit as st

from utils.doc_reader import (
    extract_text_from_file,
    chunk_sections,
    answer_document_query,
)

# 10-turn demonstration scenario data
DEMO_10_TURNS = [
    {
        "turn": 1,
        "role": "user",
        "query": "What is the coverage period and policy term under this agreement?",
        "topic": "Coverage Period",
        "is_shift": False,
        "is_repeat": False
    },
    {
        "turn": 2,
        "role": "user",
        "query": "What is the grace period allowed for overdue premium payments?",
        "topic": "Grace Period",
        "is_shift": True,
        "is_repeat": False
    },
    {
        "turn": 3,
        "role": "user",
        "query": "Does the policy remain in full force during this grace period?",
        "topic": "Grace Period Coverage (Context Retention)",
        "is_shift": False,
        "is_repeat": False
    },
    {
        "turn": 4,
        "role": "user",
        "query": "Can the customer cancel the policy during the free-look period?",
        "topic": "Free-Look Cancellation",
        "is_shift": True,
        "is_repeat": False
    },
    {
        "turn": 5,
        "role": "user",
        "query": "How many calendar days does the customer have to return the policy document?",
        "topic": "Free-Look Duration (Follow-up)",
        "is_shift": False,
        "is_repeat": False
    },
    {
        "turn": 6,
        "role": "user",
        "query": "What documents are required to submit an insurance claim?",
        "topic": "Claim Settlement Checklist",
        "is_shift": True,
        "is_repeat": False
    },
    {
        "turn": 7,
        "role": "user",
        "query": "What is the guaranteed timeline for settlement once claim documents are received?",
        "topic": "Claim Settlement Timeline (Follow-up)",
        "is_shift": False,
        "is_repeat": False
    },
    {
        "turn": 8,
        "role": "user",
        "query": "What documents are required to submit an insurance claim?",
        "topic": "Claim Checklist (Repetition Test)",
        "is_shift": False,
        "is_repeat": True
    },
    {
        "turn": 9,
        "role": "user",
        "query": "Are pre-existing medical conditions covered immediately under this policy?",
        "topic": "Pre-Existing Conditions Exclusion",
        "is_shift": True,
        "is_repeat": False
    },
    {
        "turn": 10,
        "role": "user",
        "query": "What is the waiting period duration before pre-existing conditions become eligible for claims?",
        "topic": "Waiting Period (Follow-up Refinement)",
        "is_shift": False,
        "is_repeat": False
    }
]


def initialize_session_state():
    """Ensures necessary session state variables exist."""
    if "doc_chunks" not in st.session_state:
        st.session_state["doc_chunks"] = []
    if "loaded_doc_names" not in st.session_state:
        st.session_state["loaded_doc_names"] = []
    if "conversation_history" not in st.session_state:
        st.session_state["conversation_history"] = []
    if "demo_turn_index" not in st.session_state:
        st.session_state["demo_turn_index"] = 0


def load_demo_documents():
    """Loads sample policy and guide documents into memory for testing and demonstration."""
    demo_files = [
        ("sample_policy_doc.txt", "demo_data/sample_policy_doc.txt"),
        ("sample_faq_terms.txt", "demo_data/sample_faq_terms.txt")
    ]

    all_sections = []
    loaded_names = []

    for fname, rel_path in demo_files:
        full_path = os.path.join(os.path.dirname(__file__), "..", rel_path)
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                content = f.read()
            sections, err = extract_text_from_file(content, fname)
            if sections:
                all_sections.extend(sections)
                loaded_names.append(fname)

    if all_sections:
        st.session_state["doc_chunks"] = chunk_sections(all_sections)
        st.session_state["loaded_doc_names"] = loaded_names
        return True
    return False


def render_document_assistant_tab():
    """Streamlit UI renderer for Module 2."""
    initialize_session_state()

    st.markdown("## 📑 Document Support Assistant")
    st.markdown(
        "Upload corporate documents, contracts, or policies in **PDF, DOCX, or TXT** format. "
        "The assistant answers inquiries with exact source attribution, maintains conversation context, "
        "adapts to topic shifts, and avoids redundant answers."
    )

    # File Upload & Demo Loader Controls
    col_u1, col_u2 = st.columns([3, 1])
    with col_u1:
        uploaded_files = st.file_uploader(
            "Upload Documents (PDF, DOCX, TXT):",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=True,
            key="doc_assistant_uploader"
        )
    with col_u2:
        st.write("")
        st.write("")
        if st.button("📁 Load Demo Policy Docs", use_container_width=True):
            if load_demo_documents():
                st.success("Loaded demo policy documents successfully!")
                st.rerun()

    # Process newly uploaded user files
    if uploaded_files:
        new_sections = []
        new_names = []
        for uf in uploaded_files:
            bytes_data = uf.read()
            sections, err = extract_text_from_file(bytes_data, uf.name)
            if sections:
                new_sections.extend(sections)
                new_names.append(uf.name)
            elif err:
                st.error(f"Error parsing '{uf.name}': {err}")

        if new_sections:
            st.session_state["doc_chunks"] = chunk_sections(new_sections)
            st.session_state["loaded_doc_names"] = new_names
            st.success(f"Indexed {len(new_names)} document(s) into {len(st.session_state['doc_chunks'])} searchable chunks.")

    # Status Bar
    active_docs = st.session_state.get("loaded_doc_names", [])
    chunks = st.session_state.get("doc_chunks", [])

    if not chunks:
        # Automatically load demo documents if nothing is loaded yet so user immediately has a functional assistant!
        load_demo_documents()
        chunks = st.session_state.get("doc_chunks", [])
        active_docs = st.session_state.get("loaded_doc_names", [])

    st.markdown(
        f"**Active Knowledge Base:** {len(active_docs)} document(s) loaded "
        f"(`{', '.join(active_docs)}`) | **Searchable Segments:** `{len(chunks)} chunks`"
    )

    # 10-TURN DEMO ACCORDION / WALKTHROUGH
    with st.expander("🎬 10-Turn Conversation Demonstration Walkthrough", expanded=False):
        st.markdown(
            "This demonstration illustrates **10 realistic conversation turns** covering context retention, "
            "follow-up pronoun resolution, explicit topic changes, source citations, and repetition avoidance."
        )

        col_d1, col_d2, col_d3 = st.columns([1, 1, 1])
        if col_d1.button("▶️ Execute Full 10-Turn Demonstration", use_container_width=True):
            # Clear existing and run all 10 turns
            st.session_state["conversation_history"] = []
            with st.spinner("Executing 10-turn interactive demonstration..."):
                for turn_item in DEMO_10_TURNS:
                    q = turn_item["query"]
                    ans_data = answer_document_query(q, chunks, st.session_state["conversation_history"])
                    st.session_state["conversation_history"].append({"role": "user", "content": q})
                    st.session_state["conversation_history"].append({
                        "role": "assistant",
                        "content": ans_data["answer"],
                        "sources": ans_data["sources"],
                        "topic_shifted": ans_data["topic_shifted"],
                        "repeated_query": ans_data["repeated_query"],
                        "confidence": ans_data["confidence"]
                    })
            st.success("Successfully loaded all 10 demonstration conversation turns below!")
            st.rerun()

        if col_d2.button("⏩ Step Forward 1 Turn", use_container_width=True):
            curr_idx = st.session_state.get("demo_turn_index", 0)
            if curr_idx < len(DEMO_10_TURNS):
                turn_item = DEMO_10_TURNS[curr_idx]
                q = turn_item["query"]
                ans_data = answer_document_query(q, chunks, st.session_state["conversation_history"])
                st.session_state["conversation_history"].append({"role": "user", "content": q})
                st.session_state["conversation_history"].append({
                    "role": "assistant",
                    "content": ans_data["answer"],
                    "sources": ans_data["sources"],
                    "topic_shifted": ans_data["topic_shifted"],
                    "repeated_query": ans_data["repeated_query"],
                    "confidence": ans_data["confidence"]
                })
                st.session_state["demo_turn_index"] = curr_idx + 1
                st.rerun()
            else:
                st.info("Completed all 10 demonstration turns.")

        if col_d3.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state["conversation_history"] = []
            st.session_state["demo_turn_index"] = 0
            st.rerun()

    # Chat Conversation Interface
    st.markdown("### Conversation History")
    history = st.session_state.get("conversation_history", [])

    if not history:
        st.info("No messages yet. Ask a question below or trigger the **10-Turn Demonstration** above!")
    else:
        for idx, msg in enumerate(history):
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(f"**You:** {msg['content']}")
            else:
                with st.chat_message("assistant"):
                    # Check metadata flags
                    if msg.get("topic_shifted"):
                        st.caption("🔄 *Topic change acknowledged*")
                    if msg.get("repeated_query"):
                        st.caption("ℹ️ *Duplicate query handled with targeted synthesis*")

                    st.markdown(msg["content"])

                    # Render source citations
                    sources = msg.get("sources", [])
                    if sources:
                        with st.expander(f"📚 View Source Evidence ({len(sources)} cited segments)", expanded=False):
                            for s_idx, src in enumerate(sources):
                                st.markdown(
                                    f"**Source {s_idx + 1}:** `{src['filename']}` — **{src['section']}** "
                                    f"(Match Confidence: `{int(src.get('confidence', 0.8) * 100)}%`)"
                                )
                                st.caption(f"\"{src.get('snippet', '')}\"")

    # User Input Field
    st.markdown("---")
    user_query = st.chat_input("Ask a question about the uploaded documents...")

    if user_query:
        # Add user query to conversation
        st.session_state["conversation_history"].append({"role": "user", "content": user_query})

        # Answer using document chunks and past history
        with st.spinner("Searching documents and formulating response..."):
            ans_data = answer_document_query(user_query, chunks, st.session_state["conversation_history"])

        # Add assistant response to conversation
        st.session_state["conversation_history"].append({
            "role": "assistant",
            "content": ans_data["answer"],
            "sources": ans_data["sources"],
            "topic_shifted": ans_data["topic_shifted"],
            "repeated_query": ans_data["repeated_query"],
            "confidence": ans_data["confidence"]
        })
        st.rerun()
