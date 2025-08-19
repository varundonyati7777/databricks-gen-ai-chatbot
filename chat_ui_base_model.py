# ============================
# CELL 0 — install deps (run once)
# ============================
# In CE you may need to install packages in the notebook environment.
# Run this cell first (it may take several minutes).
#%pip install --quiet sentence-transformers transformers "langchain>=0.0.200" langchain-community faiss-cpu ipywidgets
%pip install pypdf
# After install, restart the Python kernel if prompted by the environment.

# ============================
# CELL 1 — imports & settings
# ============================
import os, sys, time
from IPython.display import display, clear_output
import ipywidgets as widgets

# change this if your PDFs live elsewhere
PDF_FOLDER = "/Volumes/workspace/default/ieee"

# Safety knobs
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"            # sentence-transformers
QA_MODEL_NAME = "deepset/roberta-base-squad2"        # extractive QA
SUMMARIZER_MODEL_NAME = "sshleifer/distilbart-cnn-12-6"  # smaller summarizer alternative
# If you prefer bigger summarizer, swap to "facebook/bart-large-cnn" but it's heavier.

# ============================
# CELL 2 — load PDFs
# ============================
from langchain_community.document_loaders import PyPDFLoader

documents = []
if not os.path.isdir(PDF_FOLDER):
    raise FileNotFoundError(f"PDF folder not found: {PDF_FOLDER}")

for fname in sorted(os.listdir(PDF_FOLDER)):
    if fname.lower().endswith(".pdf"):
        path = os.path.join(PDF_FOLDER, fname)
        try:
            loader = PyPDFLoader(path)
            pages = loader.load()
            # attach filename metadata so answers can cite source if needed
            for p in pages:
                if p.metadata is None:
                    p.metadata = {}
                p.metadata["source"] = fname
            documents.extend(pages)
            print(f"Loaded {len(pages)} pages from {fname}")
        except Exception as e:
            print(f"Failed to load {fname}: {e}")

print(f"Total pages loaded: {len(documents)}")
if len(documents) == 0:
    raise RuntimeError("No PDF pages loaded — check the PDF_FOLDER path and files.")
# ============================
# CELL 3 — text splitting
# ============================
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
docs = splitter.split_documents(documents)
print(f"Split into {len(docs)} chunks")
# ============================
# CELL 4 — embeddings wrapper + FAISS
# ============================
from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings
from langchain_community.vectorstores import FAISS

print("Loading embedding model:", EMBEDDING_MODEL_NAME)
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

class LocalEmbeddings(Embeddings):
    def embed_documents(self, texts):
        # returns list[list[float]]
        vecs = embedding_model.encode(texts, show_progress_bar=True)
        # ensure python lists (not numpy) for langchain compatibility
        return [v.tolist() if hasattr(v, "tolist") else list(v) for v in vecs]

    def embed_query(self, text):
        v = embedding_model.encode([text], show_progress_bar=False)[0]
        return v.tolist() if hasattr(v, "tolist") else list(v)

local_embeddings = LocalEmbeddings()

# Build FAISS vectorstore from chunk texts and keep metadata
texts = [d.page_content for d in docs]
metadatas = [d.metadata for d in docs]
print("Building FAISS vector store (may take a moment)...")
vectorstore = FAISS.from_texts(texts, local_embeddings, metadatas=metadatas)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
print("FAISS vectorstore ready.")
# ============================
# CELL 5 — load HF pipelines (QA + summarizer)
# ============================
from transformers import pipeline

print("Loading extractive QA model:", QA_MODEL_NAME)
qa_pipeline = pipeline("question-answering", model=QA_MODEL_NAME, device=-1)  # CPU in CE

print("Loading summarizer model:", SUMMARIZER_MODEL_NAME)
summarizer = pipeline("summarization", model=SUMMARIZER_MODEL_NAME, device=-1)
print("Models loaded.")
# ============================
# CELL 6 — core RAG + answer function
# ============================
from typing import List

def retrieve_context(query: str, k: int = 4) -> List[dict]:
    """
    Returns top-k chunks as a list of dicts: {'text':..., 'source':...}
    """
    # Use retriever.invoke per new LangChain API (works with our retriever)
    results = retriever.invoke(query) if hasattr(retriever, "invoke") else retriever.get_relevant_documents(query)
    out = []
    for r in results:
        src = r.metadata.get("source", "") if getattr(r, "metadata", None) else ""
        out.append({"text": r.page_content, "source": src})
    return out

def answer_with_qa(query: str) -> str:
    """
    Use an extractive QA model to answer using retrieved context.
    """
    ctx_chunks = retrieve_context(query)
    if not ctx_chunks:
        return "No relevant passages found in the PDFs."
    context = " ".join([c["text"] for c in ctx_chunks])
    try:
        res = qa_pipeline(question=query, context=context)
        answer = res.get("answer") or res.get("score") or str(res)
        # add short citation list
        sources = ", ".join(sorted({c["source"] for c in ctx_chunks if c["source"]}))
        if sources:
            answer = f"{answer}\n\n(Sources: {sources})"
        return answer
    except Exception as e:
        return f"QA model error: {e}"

def answer_with_summary(query: str) -> str:
    """
    Use the summarizer to summarize the retrieved context.
    """
    ctx_chunks = retrieve_context(query, k=6)
    if not ctx_chunks:
        return "No relevant passages found in the PDFs."
    context = " ".join([c["text"] for c in ctx_chunks])
    try:
        out = summarizer(context, max_length=160, min_length=30, do_sample=False)
        summary = out[0]["summary_text"]
        sources = ", ".join(sorted({c["source"] for c in ctx_chunks if c["source"]}))
        if sources:
            summary = f"{summary}\n\n(Sources: {sources})"
        return summary
    except Exception as e:
        return f"Summarizer error: {e}"

def chatbot_answer(query: str) -> str:
    """
    Router: if user asks for 'summarize' or 'summary' or 'explain' -> use summarizer,
    otherwise prefer extractive QA for factual queries.
    """
    qlow = query.strip().lower()
    if any(tok in qlow for tok in ["summarize", "summary", "summarise", "give a summary", "explain", "overview"]):
        return answer_with_summary(query)
    else:
        # Try QA first
        qa_ans = answer_with_qa(query)
        # If QA seems unhelpful (very short or contains 'unanswerable'), fallback to summary
        if qa_ans.strip().lower().startswith(("i do not know", "no relevant", "unanswerable")) or len(qa_ans) < 20:
            return answer_with_summary(query)
        return qa_ans
# ============================
# CELL 7 — Notebook widget UI (chat-like)
# ============================
# Small chat widget using ipywidgets. Type query and press Enter.
query_box = widgets.Text(
    placeholder="Ask a question about the PDFs and press Enter...",
    description="Query:",
    layout=widgets.Layout(width="85%"),
)

send_btn = widgets.Button(description="Ask", button_style="primary")
clear_btn = widgets.Button(description="Clear", button_style="warning")
output_box = widgets.Output(layout=widgets.Layout(border="1px solid #ddd", padding="8px", width="85%"))

chat_history = []  # list of (question, answer)

def update_display():
    with output_box:
        clear_output()
        for i, (q, a) in enumerate(chat_history[-20:]):  # show last 20
            print(f"Q{i+1}: {q}\nA{i+1}: {a}\n{'-'*60}")

def process_query(_=None):
    q = query_box.value.strip()
    if not q:
        return
    # show immediate feedback
    with output_box:
        print(f"Q (processing): {q}\n")
    # call our RAG function
    a = chatbot_answer(q)
    chat_history.append((q, a))
    query_box.value = ""  # clear input
    update_display()

def on_clear(_):
    chat_history.clear()
    update_display()

send_btn.on_click(process_query)
clear_btn.on_click(on_clear)
query_box.on_submit(lambda _: process_query())

ui = widgets.VBox([
    widgets.HTML(value="<h3>📄 PDF Chatbot (Notebook UI)</h3>"),
    query_box,
    widgets.HBox([send_btn, clear_btn]),
    output_box
])

display(ui)
print("Type a question in the box above and press Enter or click Ask.")
