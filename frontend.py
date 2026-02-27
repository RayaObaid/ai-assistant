import streamlit as st
import requests
import hashlib

import os
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="AI Chatbot", page_icon="💬", layout="centered")

# -------------------- CSS (ChatGPT-ish) --------------------
st.markdown("""
<style>
/* Page */
.stApp {
  background: #f7f7f8;
}
.block-container {
  padding-top: 2.5rem;
  padding-bottom: 6rem;
  max-width: 760px;
}

/* Header */
.app-header {
  position: fixed;
  top: 0; left: 0; right: 0;
  background: rgba(247,247,248,0.85);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #e5e7eb;
  z-index: 999;
}
.header-inner {
  max-width: 760px;
  margin: 0 auto;
  padding: 14px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.brand {
  display: flex;
  gap: 10px;
  align-items: center;
  font-weight: 700;
  color: #111827;
  font-size: 16px;
}
.badge {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 999px;
  background: #eef2ff;
  color: #3730a3;
  border: 1px solid #e0e7ff;
}

/* Top spacing below fixed header */
.spacer { height: 62px; }

/* Upload card */
.upload-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 14px 14px 6px 14px;
  box-shadow: 0 8px 22px rgba(17,24,39,0.06);
  margin-bottom: 16px;
}
.upload-title {
  font-weight: 650;
  color: #111827;
  margin-bottom: 8px;
}
.upload-hint {
  color: #6b7280;
  font-size: 13px;
  margin-top: -4px;
  margin-bottom: 8px;
}

/* Chat message bubbles */
div[data-testid="stChatMessage"] {
  border-radius: 14px;
  border: 1px solid #e5e7eb;
  padding: 12px 14px;
  margin-bottom: 12px;
  box-shadow: 0 6px 18px rgba(17,24,39,0.05);
}

/* Make user/assistant look different */
div[data-testid="stChatMessage"][aria-label="Chat message from user"]{
  background: #ffffff;
}
div[data-testid="stChatMessage"][aria-label="Chat message from assistant"]{
  background: #fbfbff;
  border-color: #e8e8ff;
}

/* Input box styling */
div[data-testid="stChatInput"] textarea {
  border-radius: 14px !important;
}

/* Buttons */
.stButton > button {
  border-radius: 12px !important;
  padding: 0.55rem 0.8rem !important;
  border: 1px solid #e5e7eb !important;
  background: #ffffff !important;
}
.stButton > button:hover {
  border-color: #d1d5db !important;
}
.small-note {
  color: #6b7280;
  font-size: 12px;
  margin-top: 6px;
}
</style>
""", unsafe_allow_html=True)

# -------------------- Fixed Header --------------------
st.markdown("""
<div class="app-header">
  <div class="header-inner">
    <div class="brand">💬 AI Chatbot <span class="badge">PDF Q&A</span></div>
  </div>
</div>
<div class="spacer"></div>
""", unsafe_allow_html=True)

# -------------------- Session State --------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_fingerprint" not in st.session_state:
    st.session_state.uploaded_fingerprint = None

if "pdf_ready" not in st.session_state:
    st.session_state.pdf_ready = False


def file_fingerprint(file) -> str:
    return hashlib.md5(file.getvalue()).hexdigest()


# -------------------- Upload Card --------------------
st.markdown('<div class="upload-card">', unsafe_allow_html=True)
st.markdown('<div class="upload-title">Upload a PDF</div>', unsafe_allow_html=True)
st.markdown('<div class="upload-hint">Ask questions and get answers from your document.</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    " ",
    type=["pdf"],
    label_visibility="collapsed"
)

colA, colB = st.columns([1, 1])
with colB:
    if st.button("🗑 Clear chat"):
        st.session_state.messages = []
        st.rerun()

# upload logic (only once per file)
if uploaded_file is not None:
    fp = file_fingerprint(uploaded_file)

    if st.session_state.uploaded_fingerprint != fp:
        st.session_state.pdf_ready = False
        with st.spinner("Indexing your PDF (one-time)..."):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/upload",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
                    timeout=300
                )
                if resp.status_code == 200:
                    st.session_state.uploaded_fingerprint = fp
                    st.session_state.pdf_ready = True
                    st.success("✅ PDF is ready. Ask your questions below.")
                else:
                    st.error("❌ Failed to process the PDF.")
            except Exception:
                st.error("⚠️ Cannot connect to backend. Start FastAPI first.")
    else:
        st.session_state.pdf_ready = True
        st.info("✅ This PDF is already indexed. Ask your questions below.")

st.markdown('<div class="small-note">Tip: Upload a different PDF to re-index automatically.</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# -------------------- Chat History --------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------------------- Chat Input --------------------
prompt = st.chat_input("Message AI Chatbot…")

if prompt:
    if not st.session_state.pdf_ready:
        st.warning("📌 Upload a PDF first (or wait until indexing finishes).")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/chat",
                        json={"message": prompt},
                        timeout=120
                    )
                    if resp.status_code == 200:
                        answer = resp.json().get("response", "⚠️ Unexpected backend response.")
                    else:
                        answer = "⚠️ Backend returned an error."
                except Exception:
                    answer = "⚠️ Cannot connect to backend."
                st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})