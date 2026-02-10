# Code Analysis & RAG API (Flask)

## Overview
This is a **Flask-based API** that provides services for:
- Explaining and converting legacy code using **Watsonx**
- Chunking COBOL and Perl files
- Summarising large files
- Storing chunks in **Milvus** for RAG
- Adding retrieval context to prompts

The API supports **streaming responses** and is designed for code understanding and modernization workflows.

---

## Tech Stack
- Flask + Flask-CORS
- IBM Watsonx (LLM inference)
- Milvus (vector database)
- RAG utilities
- Custom chunking for COBOL (`.cbl`) and Perl (`.pl`)

---

## Run the Server

```bash
python app.py
```

# Code Analysis UI (React + Carbon)

## Overview
This is a **React (TypeScript) frontend** built using **Carbon Design System** that interacts with a Flask backend to:
- Upload Perl (`.pl`) files
- Chunk large files
- Explain or convert code using Watsonx (streaming)
- Perform full-file or chunk-level analysis
- Save generated responses

The UI is optimized for **legacy code understanding and modernization** workflows.

---

## Tech Stack
- React + TypeScript
- Carbon Components React
- Axios / Fetch API
- Server-Sent Events (streaming responses)
- FileSaver.js

---

## Features
- File upload (`.pl`)
- Automatic code chunking
- Chunk selector dropdown
- Explain / Java conversion (file or chunk level)
- Streaming LLM output
- Save generated response as `.doc`
- Reset session

---

## Backend Dependency
The app expects a running backend at:
http://127.0.0.1:5000

