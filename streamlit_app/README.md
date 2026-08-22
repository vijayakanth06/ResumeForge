# ResumeForge ATS Studio — Streamlit App

A standalone, modern Streamlit web application powered by **OpenRouter AI** (with Groq and custom OpenAI-compatible provider support) and **ResumeForge MCP Tools** for ultra-high-powered ATS resume generation, scoring, and interactive conversational optimization.

## Features

- 🌐 **OpenRouter High-Context Open-Source Models**: Access top-tier free open-source models with generous token contexts (65k–1,000,000 tokens):
  - `nvidia/nemotron-3-ultra-550b-a55b:free` (1M Context)
  - `nvidia/nemotron-3.5-lightning:free` (1M Context)
  - `nvidia/nemotron-3-nano-30b-a3b:free` (256k Context)
  - `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` (256k Context)
  - `nvidia/nemotron-3-super-120b-a12b:free` (262k Context)
  - `nvidia/nemotron-nano-12b-v2-vl:free` (128k Context)
  - `nvidia/nemotron-nano-9b-v2:free` (128k Context)
  - `google/gemma-4-31b-it:free` (262k Context)
  - `google/gemma-4-26b-a4b-it:free` (262k Context)
  - `cohere/north-mini-code:free` (256k Context)
  - `poolside/laguna-s-2.1:free` (262k Context)
  - `poolside/laguna-xs-2.1:free` (262k Context)
  - `z-ai/glm-5.2:free` (256k Context)
  - `dots-studio/dots-3-note-preview:free` (512k Context)
  - `openai/gpt-oss-20b:free` (131k Context)
  - `liquid/lfm-2.5-2.6b:free` (65k Context)
  - `openrouter/free` (200k Context)
- 📂 **Drag & Drop File Ingestion**: Upload Job Descriptions (`.pdf`, `.docx`, `.txt`, `.md`) and candidate documents or use existing `md/` biography data.
- ⚡ **ResumeForge MCP Tool Calling**: Seamlessly executes `tailor_resume_for_job` and candidate profile aggregators.
- 🎯 **High-Powered ATS Prompt & Scoring Engine**: Built-in 95%+ ATS optimization prompt and real-time keyword match analysis (matched vs missing keywords, match score percentage).
- 💬 **Interactive AI Chatbot**: Multi-turn conversational assistant with tool-calling capabilities to refine, customize, and polish your resume in real time.
- 📝 **Live Preview & Editor**: Executive ATS formatted preview, live markdown editor, and one-click export (`.md`, copy, save).

## Quickstart

1. Install requirements:
   ```bash
   pip install -r streamlit_app/requirements.txt
   ```

2. Add your **OpenRouter API Key** to your `.env` file (or enter it in the app sidebar):
   ```env
   OPENROUTER_API_KEY=sk-or-v1-...
   ```

3. Run the Streamlit app:
   ```bash
   streamlit run streamlit_app/app.py
   ```

4. Select your preferred free open-source model from the dropdown, upload a Job Description, and click **⚡ Generate ATS-Optimized Resume**.
