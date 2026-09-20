# LangGraph Resume Analyzer

A Streamlit application with three LangGraph-powered features:

1. Analyze a resume and identify its pros, cons, score, and improvements.
2. Compare a resume with a job description and calculate an explainable match score.
3. Reassemble a truthful job-targeted resume using existing content, compare it with the original, and download a clean DOCX or TXT version.

## Architecture

```text
Upload and extract resume -> extract_resume_text()
    |
    +--> Tab 1: analyze_resume()
    |      resume_graph -> _analyze_node() -> _validate_analysis_node()
    |
    +--> Tab 2: match_resume_to_job()
    |      match_graph -> _match_node() -> _validate_match_node()
    |
    +--> Tab 3: tailor_resume_to_job()
           tailor_graph -> _tailor_node() -> _validate_tailor_node()
                    |
                    +--> build_comparison_html()
                    +--> create_resume_docx()
```

## How the application works

1. The user selects one of the three feature tabs and uploads a PDF, DOCX, or TXT resume.
2. `app.py` validates the file and calls `extract_resume_text()` in `document_loader.py`.
3. For resume analysis, `analyze_resume()` runs the review graph and returns structured pros, cons, scoring, and improvements.
4. For job matching, the user also supplies a job description. `match_resume_to_job()` returns a score, matched requirements, missing evidence, keyword gaps, and recommendations.
5. For resume updating, `tailor_resume_to_job()` calls deterministic Python code that reorders existing skills and bullet points by job relevance. This feature makes no Groq API call and creates no new candidate claims.
6. `build_comparison_html()` shows the original and updated resumes side by side. Removed or replaced text is red, while updated wording is green.
7. `create_resume_docx()` produces a clean downloadable Word document without comparison colors or highlights. A clean TXT download is also available.
8. Input fingerprints stored in Streamlit session state prevent an earlier result from being displayed for a different resume or job description.

The Groq API is called only after the user clicks **Analyze resume**. The application does not permanently save the uploaded resume.

## Project files

- `app.py` — Streamlit interface and result display.
- `document_loader.py` — PDF, DOCX, and TXT text extraction.
- `resume_graph.py` — three LangGraph workflows, prompts, and structured response models.
- `resume_export.py` — highlighted comparison and clean DOCX generation.
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

1. Select **Resume analysis**, **Job match**, or **Update resume**.
2. Upload one text-based PDF, DOCX, or TXT resume.
3. In the second or third tab, paste a complete job description.
4. Click the action button and wait for the selected LangGraph workflow.
5. Review the AI output carefully. In the third tab, inspect highlighted changes before downloading the clean DOCX or TXT resume.

## Limitations

- Scanned PDFs require OCR and are not supported in this first version.
- Matching scores measure document alignment and are not hiring recommendations.
- The tailored resume must be manually reviewed for factual accuracy.
- The generated score describes resume quality; it is not a hiring decision.
- AI-generated feedback should be reviewed by a person.
