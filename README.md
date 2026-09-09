# NoticeSense

NoticeSense is an Agentic AI System designed for understanding and tracking official notices and circulars. It utilizes OCR to extract text from documents (PDF, JPG, PNG) and leverages a multi-agent AI pipeline to parse intents, extract deadlines, summarize actionable steps, and allow you to chat interactively with the notice context.

Phase 3 introduces a robust decoupled architecture: a **FastAPI backend** handling inference, and a clean **vanilla HTML/CSS/JS Single-Page Application (SPA)** frontend.

## Features
- **Upload Any Notice**: Supports `.pdf`, `.png`, `.jpg`, and `.jpeg`. Multi-page PDFs are automatically converted.
- **OCR Text Extraction**: Powered by Tesseract OCR with built-in noise-filtering.
- **3-Agent AI Pipeline**:
  - **Intent Agent**: Categorizes the notice (e.g., Compliance, Legal, General) and writes a concise summary.
  - **Deadline Agent**: Scans for exact dates/deadlines and calculates "Days Remaining."
  - **Action Agent**: Extracts a bulleted list of precise steps you need to take.
- **Interactive Chat**: Ask the AI questions about the uploaded notice. It will strictly answer based only on the document.
- **Flexible LLM Backend**: Choose your AI engine. Run entirely locally using **Ollama** (e.g., Gemma 3, Llama 3) for absolute privacy, or use **Google Gemini** for high-speed cloud inference.

## Folder Structure
```text
NoticeSense/
├── backend/                  # Core backend logic
│   ├── api/                  # FastAPI app and REST routes
│   │   ├── app.py            # Main API entry point (serves static files & API)
│   │   └── routes/           # /api/upload and /api/chat logic
│   ├── core/                 # App settings & LLM configuration (Pydantic setup)
│   ├── router/               # Agent orchestration (AgentRouter)
│   ├── services/             # OCR, text cleaning, text parsing logic
│   └── agents.py             # IntentAgent, DeadlineAgent, ActionAgent logic
├── data/
│   └── uploads/              # Temporary storage for uploaded user files
├── static/                   # Decoupled Single Page Application (SPA)
│   ├── index.html            # Main UI shell
│   ├── css/style.css         # UI Design System (cards, animations, colors)
│   └── js/app.js             # Client-side routing, DOM manipulation, API calls
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
└── README.md                 # Project setup and documentation
```

## System Prerequisites (Windows)

Before running the Python application, you **must** install the system-level dependencies for OCR.

1. **Install Tesseract OCR**:
   - Download the Windows installer from [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
   - Install it, usually to `C:\Program Files\Tesseract-OCR\`.
   - The path is configured in `backend/core/config.py`. Update `TESSERACT_CMD` if installed elsewhere.

2. **Install Poppler** (Required for PDF processing):
   - Download the latest Poppler Windows binary from [Release poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases/).
   - Extract the `.zip` file to a folder like `C:\poppler\poppler-23.11.0\`.
   - Update `POPPLER_PATH` in `backend/core/config.py` to point to the `Library\bin` folder.

3. **Optional: Install Ollama** (If running locally):
   - Download from [Ollama](https://ollama.com).
   - Run `ollama run gemma3:4b` to pull and test the model.

## Setup Instructions

1. **Create and Activate a Virtual Environment**
   Open your terminal (Command Prompt/PowerShell) in the `NoticeSense` folder and run:
   ```bash
   python -m venv venv
   
   # Activate on Windows:
   venv\Scripts\activate
   ```

2. **Install Python Dependencies**
   Run the following command to install required libraries:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment variables**
   Create a `.env` file in the root directory.
   
   If using Google Gemini (Cloud):
   ```env
   LLM_BACKEND=gemini
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

   If using Ollama (Local/Private):
   ```env
   LLM_BACKEND=ollama
   OLLAMA_MODEL=gemma3:4b
   OLLAMA_BASE_URL=http://localhost:11434
   ```

4. **Verify Configuration Paths**
   Open `backend/core/config.py` and ensure the OCR paths match your system installation:
   ```python
   TESSERACT_CMD: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
   POPPLER_PATH: str = r"C:\poppler\poppler-xx.xx.x\Library\bin"
   ```

5. **Run the Application**
   Start the FastAPI server (which also serves the frontend):
   ```bash
   uvicorn backend.api.app:app --host 0.0.0.0 --port 8000 --reload
   ```
   
   The application will be accessible at `http://localhost:8000`.

## Architectural Shift
NoticeSense has migrated from a monolithic Streamlit application (Phase 1/2) to a robust decoupled structure (Phase 3). 
- **FastAPI** handles complex asynchronous routing and document parsing securely in the background.
- A **Vanilla HTML/JS SPA** provides a fast, professional, lightweight user interface.
- Session state is maintained in-memory on the backend using unique `session_id` mapping linked temporarily with browser `sessionStorage`.
