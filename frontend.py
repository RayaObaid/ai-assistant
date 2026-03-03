import streamlit as st
import requests
import hashlib
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="AI Chatbot", page_icon="💬", layout="centered")

st.markdown("""
<style>
.stApp { background: #F5EBDD; }
.block-container {
  padding-top: 4.6rem;
  padding-bottom: 6rem;
  max-width: 820px;
}
.app-header{
  position: fixed;
  top: 0; left: 0; right: 0;
  background: rgba(245,235,221,0.92);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(17,24,39,0.08);
  z-index: 999;
}
.header-inner{
  max-width: 820px;
  margin: 0 auto;
  padding: 14px 18px;
  display:flex;
  align-items:center;
  justify-content: space-between;
}
.brand{
  display:flex;
  align-items:center;
  gap:10px;
  font-weight:800;
  color:#1f2937;
  font-size:18px;
  letter-spacing: 0.2px;
}
.badge{
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.65);
  color: #374151;
  border: 1px solid rgba(17,24,39,0.10);
}
.stButton > button{
  border-radius: 12px !important;
  padding: 0.55rem 0.9rem !important;
  border: 1px solid rgba(17,24,39,0.12) !important;
  background: rgba(255,255,255,0.75) !important;
  color: #111827 !important;
  font-weight: 600 !important;
}
.stButton > button:hover{
  border-color: rgba(17,24,39,0.22) !important;
  background: rgba(255,255,255,0.92) !important;
}
.upload-card{
  background: rgba(255,255,255,0.78);
  border: 1px solid rgba(17,24,39,0.10);
  border-radius: 16px;
  padding: 14px 14px 10px 14px;
  box-shadow: 0 10px 26px rgba(17,24,39,0.08);
  margin-bottom: 16px;
}
.upload-title{
  font-weight: 800;
  color: #111827;
  margin-bottom: 2px;
  font-size: 15px;
}
.upload-hint{
  color: #6b7280;
  font-size: 13px;
  margin-bottom: 10px;
}
div[data-testid="stFileUploader"]{
  background: rgba(255,255,255,0.60);
  border: 1px dashed rgba(17,24,39,0.18);
  border-radius: 14px;
  padding: 10px 12px;
}
div[data-testid="stFileUploader"] section{
  padding: 0 !important;
}
div[data-testid="stFileUploader"] button{
  border-radius: 12px !important;
}
div[data-testid="stChatMessage"]{
  border-radius: 16px;
  border: 1px solid rgba(17,24,39,0.10);
  padding: 12px 14px;
  margin-bottom: 12px;
  box-shadow: 0 10px 24px rgba(17,24,39,0.07);
}
div[data-testid="stChatMessage"][aria-label="Chat message from user"]{
  background: rgba(255,255,255,0.88);
}
div[data-testid="stChatMessage"][aria-label="Chat message from assistant"]{
  background: rgba(255,255,255,0.70);
}
div[data-testid="stChatInput"] textarea{
  border-radius: 16px !important;
}
.small-note{
  color: #6b7280;
  font-size: 12px;
  margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
  <div class="header-inner">
    <div class="brand">💬 AI Chatbot <span class="badge">Study PDF Q&A</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_fingerprint" not in st.session_state:
    st.session_state.uploaded_fingerprint = None

if "pdf_ready" not in st.session_state:
    st.session_state.pdf_ready = False

def file_fingerprint(file) -> str:
    return hashlib.md5(file.getvalue()).hexdigest()

st.markdown('<div class="upload-card">', unsafe_allow_html=True)
st.markdown('<div class="upload-title">Upload PDF</div>', unsafe_allow_html=True)
st.markdown('<div class="upload-hint">Choose a PDF and it will be processed automatically.</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col2:
    if st.button("🗑️ Clear messages"):
        st.session_state.messages = []
        st.rerun()

uploaded_file = st.file_uploader(" ", type=["pdf"], label_visibility="collapsed")

if uploaded_file is not None:
    fp = file_fingerprint(uploaded_file)
    if st.session_state.uploaded_fingerprint != fp:
        st.session_state.pdf_ready = False
        with st.spinner("Indexing your PDF (one-time)…"):
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
                    st.error("❌Failed to process the PDF.")
            except Exception:
                st.error("⚠️ Cannot connect to backend. Make sure FastAPI/Render backend is running.")
    else:
        st.session_state.pdf_ready = True
        st.info("✅ This PDF is already indexed. Ask your questions below.")

st.markdown('</div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Message AI Chatbot…")

if prompt:
    if not st.session_state.pdf_ready:
        st.warning("📌 Upload a PDF first.")
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