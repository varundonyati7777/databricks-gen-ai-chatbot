# 📄 PDF Chatbot with LangChain, FAISS, and HuggingFace Models

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-Framework-orange)](https://www.langchain.com/)
[![HuggingFace](https://img.shields.io/badge/🤗-Transformers-yellow)](https://huggingface.co/transformers/)
[![FAISS](https://img.shields.io/badge/FAISS-VectorDB-green)](https://github.com/facebookresearch/faiss)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

An interactive **RAG-based (Retrieval-Augmented Generation) chatbot** built in Python that lets you **chat with your PDF files**.  

This project uses:
- **LangChain** for document loading and chunking  
- **FAISS** for vector search  
- **SentenceTransformers** for embeddings  
- **Hugging Face pipelines** for **Question Answering** and **Summarization**  
- **ipywidgets** for a simple **notebook-based chat UI**  

---

## ✨ Features

- 📥 **PDF ingestion** with metadata (filename preserved as `source`)  
- ✂️ **Recursive text splitting** for better semantic chunking  
- 🔎 **FAISS vector store** for efficient similarity search  
- 🧠 **Dual response modes**:
  - **Extractive QA** (precise answers to factual queries)  
  - **Summarization** (when user asks for "summary", "overview", or when QA is insufficient)  
- 💬 **Notebook UI** with chat-like interaction powered by `ipywidgets`  
- 📚 **Citations included** in answers (lists source PDFs used)  

---

## 🏗️ Project Structure

```
├── notebook.ipynb        # Main notebook with all cells (install → load → query → chat UI)
├── /Volumes/workspace/default/ieee/
│   ├── file1.pdf
│   ├── file2.pdf
│   └── ...
└── README.md             # You are here 🚀
```

---

## ⚙️ Setup Instructions

### 1. Clone the repo
```bash
git clone https://github.com/your-username/pdf-chatbot.git
cd pdf-chatbot
```

### 2. Install dependencies
Run inside your notebook (or terminal if adapting):
```bash
%pip install --quiet sentence-transformers transformers "langchain>=0.0.200" langchain-community faiss-cpu ipywidgets pypdf
```

> ⚠️ Restart the Python kernel after installation (in notebooks).  

### 3. Add your PDFs
Place your PDFs inside the folder specified in the code:  
```python
PDF_FOLDER = "/Volumes/workspace/default/ieee"
```

---

## 🚀 Usage

### 1. Load and preprocess PDFs
- Loads all PDFs from the folder  
- Splits into 1000-character overlapping chunks  
- Builds FAISS vector index  

### 2. Embeddings & Models
- **Embeddings:** `all-MiniLM-L6-v2`  
- **QA Model:** `deepset/roberta-base-squad2`  
- **Summarizer:** `sshleifer/distilbart-cnn-12-6`  

*(You can swap models — see comments in code.)*

### 3. Run Chatbot
After running all cells, an **interactive widget UI** appears:

```
📄 PDF Chatbot (Notebook UI)

[ Query box: "Ask a question..." ] [ Ask ] [ Clear ]
---------------------------------------------------
Q1: What is IEEE about?
A1: IEEE is the world’s largest technical professional organization...
(Sources: ieee_overview.pdf)
```

---

## 💡 Query Examples

- **Factual Q&A**
  ```
  Q: Who is eligible for IEEE membership?
  A: IEEE membership is open to engineers, scientists...
  (Sources: membership.pdf)
  ```

- **Summarization**
  ```
  Q: Summarize the benefits of IEEE membership
  A: Members gain access to publications, conferences...
  (Sources: membership.pdf)
  ```

---

## 🛠️ Customization

- Change embedding model:
  ```python
  EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
  ```
- Use larger summarizer:
  ```python
  SUMMARIZER_MODEL_NAME = "facebook/bart-large-cnn"
  ```
- Adjust chunk size/overlap:
  ```python
  RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
  ```

---

## 📊 Tech Stack

- **Python 3.9+**
- **LangChain** — PDF loading, chunking, and retriever abstraction  
- **SentenceTransformers** — Dense embeddings  
- **FAISS** — High-performance similarity search  
- **Hugging Face Transformers** — QA & Summarization  
- **ipywidgets** — Notebook-based chat UI  

---

## 📌 Notes

- Runs on **CPU** by default (suitable for notebooks like Databricks CE, Colab, Jupyter).  
- For faster inference, switch to GPU (set `device=0` in Hugging Face pipelines).  
- Works best with **text-based PDFs** (scanned PDFs require OCR first).  

---

## 📜 License

This project is released under the **MIT License**.  
Feel free to use, modify, and distribute.  

---

## 🙌 Acknowledgements

- [LangChain](https://www.langchain.com/)  
- [SentenceTransformers](https://www.sbert.net/)  
- [FAISS](https://github.com/facebookresearch/faiss)  
- [Hugging Face Transformers](https://huggingface.co/transformers/)  
