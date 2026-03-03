from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
from utils import load_pdf, chunk_text, build_faiss_index, search_index
import tempfile

load_dotenv()

app = FastAPI()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

index = None
chunks = None


class ChatRequest(BaseModel):
    message: str


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global index, chunks

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    pdf_text = load_pdf(tmp_path)
    chunks = chunk_text(pdf_text)
    index, _ = build_faiss_index(chunks)

    return {"message": "PDF processed successfully."}


@app.post("/chat")
def chat(request: ChatRequest):
    global index, chunks

    if index is None:
        return {"response": "⚠️ Please upload a PDF first."}

    relevant_chunks = search_index(request.message, index, chunks)
    context = "\n".join(relevant_chunks)

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful study assistant. Answer using ONLY the provided context."
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion:\n{request.message}"
                }
            ]
        }
    )

    data = response.json()
    answer = data["choices"][0]["message"]["content"]

    return {"response": answer}