# LangGraph Resume Analyzer

A Streamlit application that accepts one PDF, DOCX, or TXT resume and uses a LangGraph workflow with Groq to produce an overall assessment, resume score, evidence-based pros and cons, prioritized improvements, and a candidate snapshot.

## Architecture

```text
Upload resume
    ↓
Extract and validate text
    ↓
LangGraph: analyze_resume
    ↓
LangGraph: validate_analysis
    ↓
Display the structured report in Streamlit
```

## How the application works

1. The user opens the Streamlit application and uploads one PDF, DOCX, or TXT resume.
2. `app.py` checks the file type and size, then sends the uploaded bytes to `document_loader.py`.
3. `document_loader.py` selects the appropriate reader, extracts the text, removes unnecessary whitespace, and checks that enough readable text was found.
4. When the user clicks **Analyze resume**, `app.py` passes the extracted text to `analyze_resume()` in `resume_graph.py`.
5. LangGraph places the resume text in its shared state and runs the `analyze_resume` node.
6. The analysis node sends the resume and review instructions to the Groq model. Pydantic requires a structured response containing a summary, score, pros, cons, improvements, and candidate snapshot.
7. The `validate_analysis` node checks that the important feedback sections are present.
8. The completed analysis returns to Streamlit, which displays each section in a separate tab.

The Groq API is called only after the user clicks **Analyze resume**. The application does not permanently save the uploaded resume.

## Project files

- `app.py` — Streamlit interface and result display.
- `document_loader.py` — PDF, DOCX, and TXT text extraction.
- `resume_graph.py` — Groq model, response structure, prompt, and LangGraph workflow.
- `requirements.txt` — required Python packages.
- `.env.example` — example Groq API-key configuration.

## Prerequisites

- Python 3.10 or 3.11 is recommended.
- A Groq API key.
- An internet connection for Groq API requests.

## Run on macOS

Open Terminal, move into the project folder, and run:

```bash
cd /path/to/resume_analyzer_agent
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and replace the placeholder with your Groq API key:

```text
GROQ_API_KEY=your_actual_groq_api_key
```

Start the application:

```bash
streamlit run app.py
```

## Run on Windows

Open Command Prompt, move into the project folder, and run:

```bat
cd C:\path\to\resume_analyzer_agent
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
copy .env.example .env
```

Open `.env` in Notepad and replace the placeholder:

```text
GROQ_API_KEY=your_actual_groq_api_key
```

Start the application:

```bat
streamlit run app.py
```

Streamlit normally opens `http://localhost:8501` automatically. If it does not, copy that address into a browser. Press `Ctrl+C` in the terminal to stop the application. Never commit `.env` or share your API key.

## Using the application

1. Upload one text-based PDF, DOCX, or TXT resume.
2. Review the extracted text shown by the application.
3. Click **Analyze resume**.
4. Wait for the Groq-powered LangGraph workflow to finish.
5. Review the overall assessment, score, pros, cons, improvements, and candidate snapshot.

## Limitations

- Scanned PDFs require OCR and are not supported in this first version.
- The review is based only on the uploaded resume, without a job description.
- The generated score describes resume quality; it is not a hiring decision.
- AI-generated feedback should be reviewed by a person.
