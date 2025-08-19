# HAIR – Human AI Resources

**HAIR** (Human AI Resources) is an AI-powered recruitment platform designed to modernize and streamline the hiring process.  
It combines **large language models, semantic search, structured parsing, and multi-agent AI systems** to reduce manual effort, improve candidate-job matching, and enable data-driven hiring decisions.  

This project was developed as a **Final Year Project** for the Lebanese University – Faculty of Engineering.

---

## 🚀 Key Features

### 🤖 AI-Powered Components
- **Resume Parsing Engine**  
  Converts resumes (PDF, text, scanned) into structured JSON using LLMs + OCR.  
  Ensures validated and reusable candidate data across the platform.

- **AI Job Description Generator**  
  Given a short input (e.g., “We need a senior Python developer”), the system generates a full job description including responsibilities, required skills, and constraints.

- **Semantic Candidate Matching**  
  Uses **sentence-transformers embeddings** and **fuzzy logic (GLiNER + JobBERT-v2)** to match candidates to jobs.  
  Provides a breakdown of matched/missing skills and a global similarity score.

- **Conversational AI Assistant**  
  Built with **Model Context Protocol (MCP)** and **Gemini API**, allowing HR managers to chat with their recruitment data.  
  Example: _“How many applicants with Python applied this week?”_ → returns instant structured results.

- **AI Interviewer (Multi-Agent System)**  
  An autonomous agent conducts **real-time pre-screening interviews** with candidates.  
  - WebSocket-powered live interview interface  
  - Tailored technical/behavioral questions  
  - Automated evaluation report (scores, transcript, strengths & weaknesses)

---

### 🖥 Platform Features
- **Job Creation & Management** – Easily create and publish jobs with AI-assisted descriptions.  
- **Application Tracking** – Manage candidate submissions with structured parsing and custom form keys.  
- **Interview Scheduling** – Schedule human or AI-led interviews with automatic notifications.  
- **Analytics Dashboard** – Real-time metrics on applications, matches, interviews, and hire rate.  
- **Role-Based Access** – HR managers, interviewers, and candidates each have tailored views.  

---

## 🛠 Tech Stack
- **Frontend**: React + TypeScript *(entirely Cursor-generated)*  
- **Backend**: FastAPI + SQLModel + Pydantic  
- **Database**: PostgreSQL  
- **AI**:  
  - PydanticAI (structured agents & schemas)  
  - Ollama (on-prem LLM inference, Qwen3:8b)  
  - Gemini API (cloud AI for NLP & interviews)  
  - Hugging Face Sentence-Transformers (semantic embeddings)  
- **Deployment**: Docker Compose (with isolated containers for frontend, backend, AI services, PostgreSQL, Nginx)  

---

## 📊 System Architecture
- **Frontend Container** – User interface (React + TS).  
- **Backend Container** – REST API, authentication, and orchestration.  
- **AI Service Container** – Handles parsing, matching, chat, and interviews.  
- **Ollama Container** – Local LLM inference.  
- **PostgreSQL Container** – Candidate, jobs, and analytics storage.  
- **External Gemini API** – Cloud AI services integration.  

---

## 📈 Future Work
- Behavioral AI analysis (voice & facial cues).  
- Multilingual AI interviews.  
- Predictive analytics for workforce planning.  
- Advanced fairness and bias mitigation.  
- Scenario-based adaptive interviews.  

---

## 📜 License
MIT License – free to use, modify, and distribute.  

---

## 🙏 Acknowledgements
Developed as part of my Final Year Project at the **Lebanese University – Faculty of Engineering**.  
Special thanks to my supervisors, jury, and the **EuriskoAI** team for their support.
