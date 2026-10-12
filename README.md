# 🤖 AI-Powered Intelligent Automation System

An enterprise-grade, multi-module intelligent automation web application built with **Python**, **Streamlit**, and **Pandas**. Designed specifically for **Internship Evaluation**, this platform integrates data analytics, grounded conversational document assistance, and compliance document classification into a single unified dashboard.

---

## 📌 Executive Summary & Key Highlights

This application is architected into **three distinct modules** accessible through dedicated tabs in a centralized web interface:

| Module | Core Purpose | Technologies & Methods | Key Capabilities |
| :--- | :--- | :--- | :--- |
| **Module 1: Excel Inventory AI Agent** | Inventory data analytics & natural language question answering | Python, Pandas, Altair, OpenPyXL | Grounded Pandas analytics, Executive KPIs, Visual charts, Zero unsafe `eval()`, Supply Chain Knowledge Glossary. |
| **Module 2: Document Support Assistant** | Conversational QA across corporate documents | PyPDF, python-docx, BM25 / TF-IDF Retrieval | Multi-format ingest (PDF, DOCX, TXT), Source citations (file, section, score), Topic shift detection, 10-turn demonstration suite. |
| **Module 3: Identity & Insurance Processor** | Automated classification & extraction for 10 document types | Pytesseract, Pillow, Regex Engine, PII Masking | 10 Document Types, Field confidence scores, Human review flagging, UIDAI/IRDAI PII masking, OCR & Handwriting disclaimer, Strict nulls. |

---

## 🏗️ Architecture & Project Structure

```
Internship_AI_Project/
├── app.py                          # Main Streamlit dashboard entry point (Header, Tabs, Sidebar)
├── requirements.txt                # Pinned production dependencies
├── .gitignore                      # Python, Streamlit, cache, and virtual environment rules
├── README.md                       # Comprehensive project documentation and user manual
│
├── modules/                        # Core application modules
│   ├── __init__.py                 # Module package initialization
│   ├── inventory_agent.py          # Module 1 UI and execution controller
│   ├── document_assistant.py       # Module 2 UI and chat conversation controller
│   └── document_processor.py       # Module 3 UI, 10-doc classifier, and extractor
│
├── utils/                          # Reusable helper utilities
│   ├── __init__.py                 # Utils package initialization
│   ├── data_loader.py              # Safe CSV/Excel loading, column mapping & NLQ query engine
│   ├── doc_reader.py               # Text extraction (PDF, DOCX, TXT), chunking & grounded retrieval
│   ├── ocr_engine.py               # Tesseract OCR engine wrapper & system environment checker
│   ├── pii_protector.py            # PII masking (Aadhaar 12-digit, PAN, Bank A/C, Passport, DL)
│   └── inventory_glossary.py       # Supply chain glossary, formulas & column context inspector
│
├── demo_data/                      # Safe synthetic datasets for evaluation & testing
│   ├── sample_inventory.csv        # Realistic 20-product inventory spreadsheet
│   ├── sample_policy_doc.txt       # Master insurance policy document (Grace period, Claims, Free look)
│   ├── sample_faq_terms.txt        # Customer service FAQs and terms
│   └── synthetic_id_docs/          # Synthetic test files for all 10 document categories
│       ├── sample_aadhaar.txt
│       ├── sample_pan.txt
│       ├── sample_driving_licence.txt
│       ├── sample_passport.txt
│       ├── sample_nach_ecs.txt
│       ├── sample_fatca.txt
│       ├── sample_benefit_illustration.txt
│       ├── sample_moral_hazard.txt
│       ├── sample_multiple_policies.txt
│       └── sample_suitability_profiler.txt
│
└── tests/                          # Automated Unit Test Suite
    ├── test_inventory.py           # Unit tests for Module 1 calculations & NLQ parsing
    ├── test_doc_assistant.py       # Unit tests for Module 2 retrieval & conversation history
    └── test_processor.py           # Unit tests for Module 3 classification, extraction & PII masking
```

---

## 🔍 Module-by-Module Technical Deep Dive

### 📊 Module 1: Excel Inventory AI Agent
1. **File Ingestion:** Supports `.xlsx`, `.xls`, and `.csv` files with automatic character encoding handling (UTF-8, Latin-1) and whitespace trimming.
2. **Schema & Column Auto-Detection:** Intelligently maps arbitrary user columns to canonical roles:
   - Product Name, SKU, Stock Quantity, Unit Price, Category, Reorder Level, Supplier.
3. **Executive KPI Dashboard:** Computes real-time inventory statistics:
   - Total catalogued products, Total stock units, Estimated total inventory valuation ($), Low stock count, and Depleted (0-stock) count.
4. **Safe Natural Language Query Engine:**
   - Evaluates questions deterministically using verified Pandas operations.
   - **Zero Arbitrary Code Execution:** Strictly avoids dangerous `eval()` or `exec()` on raw user input.
   - Handles inquiries on total stock, highest/lowest stock, cheapest/priciest items, low stock alerts, category breakdowns, and specific product keyword search.
5. **Supply Chain Knowledge Glossary:**
   - Built-in search engine for 15+ inventory concepts: Safety Stock, Reorder Point (ROP), EOQ, Inventory Turnover Ratio, Days Sales of Inventory (DSI), Dead Stock, Carrying Costs, ABC Analysis, FIFO/LIFO, Shrinkage, etc.
   - Dynamic Column Context Inspector explaining the operational meaning of active columns in the uploaded file.

---

### 📑 Module 2: Document Support Assistant
1. **Multi-Format Ingestion:** Ingests `.pdf` (using `pypdf`), `.docx` (using `python-docx`), and `.txt`/`.md` files.
2. **Grounded Retrieval (RAG):**
   - Segments documents into manageable semantic chunks with page and section tracking.
   - Uses BM25/TF-IDF token matching with sub-linear frequency scaling and exact phrase bonuses.
3. **Source Attribution:** Every response includes transparent citation cards showing:
   - Source document filename, Page number or Section heading, and Match confidence percentage.
4. **Context & History Retention:**
   - Maintains full conversation history in `st.session_state`.
   - Resolves follow-up pronouns ("it", "this", "that") using context from previous questions.
5. **Topic Shift & Repetition Management:**
   - Automatically detects shifts in subject matter and acknowledges the topic change.
   - Detects repeated questions and provides progressive clarification instead of verbatim duplicate responses.
6. **10-Turn Demonstration Suite:**
   - Built-in interactive walkthrough that executes 10 multi-turn conversation steps covering coverage terms, grace periods, free-look cancellations, claims procedures, and medical exclusions.

---

### 🛡️ Module 3: Identity & Insurance Document Processor
1. **Multi-Document Ingest & OCR:** Supports batch uploads of Images (PNG, JPG, JPEG), PDFs, and Text files. Includes Tesseract OCR integration with graceful fallback mode.
2. **Classification for 10 Document Types:**
   1. **Aadhaar Card** (UIDAI keywords, 12-digit format, VID)
   2. **PAN Card** (Income Tax Dept, 10-character alphanumeric PAN)
   3. **Driving Licence** (State transport dept, DL number format, vehicle classes)
   4. **Passport** (Republic of India, Type P, Passport number, nationality)
   5. **NACH / ECS Mandate** (UMRN, Bank, IFSC, maximum limit, frequency)
   6. **FATCA Declaration** (Foreign tax compliance, TIN, country of tax residence)
   7. **Benefit Illustration Declaration** (Sum assured, modal premium, policy term)
   8. **Moral Hazard Questionnaire (MHQ)** (Proposer income, justification, underwriter notes)
   9. **Multiple Policies Consent** (Concurrent insurance numbers, total sum assured)
   10. **Suitability Profiler** (Risk appetite, horizon, income bracket, suitability score)
3. **Field Extraction with Confidence Scoring:**
   - Every extracted field receives a numerical confidence score ($0.00$ to $1.00$).
   - Fields scoring below the configurable threshold (default: $70\%$) are flagged with `Needs Review`.
4. **Strict Null Policy (Anti-Hallucination):**
   - If a field is not present in the document, it is strictly assigned `null` (`None`) with $0.0$ confidence. The system **never invents missing information**.
5. **Handwriting & OCR Disclaimer:**
   - Explicit disclaimers warn that handwritten extractions are prone to variance and require secondary human verification.
6. **PII Protection & Redaction:**
   - Built-in toggle to mask sensitive identity and banking data:
     - Aadhaar: Masks first 8 digits (`XXXX-XXXX-9542`) adhering to UIDAI guidelines.
     - PAN: Masks first 5 characters (`XXXXX4829D`).
     - Bank Account: Masks all except last 4 digits (`XXXXXXXXXX9104`).
     - Passport: Masks inner digits (`Z****104`).
     - Driving Licence: Masks inner characters (`HR-XXXX-XXXX-9281`).
7. **Structured JSON Export:** Downloadable structured JSON for individual files or batch packages.

---

## 💻 Installation & Running Guide (Windows PowerShell)

Follow these exact commands to install dependencies and run the application locally on Windows.

### Step 1: Open Windows Terminal / PowerShell
Navigate to the project directory:
```powershell
cd "C:\Users\kanis\OneDrive\Desktop\Internship_AI_Project"
```

### Step 2: (Optional but Recommended) Create & Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> **Note on OCR (Optional):**
> For physical scanned image OCR (Module 3), ensure Tesseract-OCR is installed. You can install it on Windows via winget:
> ```powershell
> winget install UB-Mannheim.TesseractOCR
> ```
> *(Text-based PDFs and TXT files work 100% out-of-the-box without Tesseract).*

### Step 4: Run the Automated Unit Test Suite
Verify that all modules, calculations, and extraction routines pass tests:
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

### Step 5: Launch the Streamlit Web Application
```powershell
python -m streamlit run app.py
```

The application will start and open automatically in your default browser at:
`http://localhost:8501`

---

## 🧪 Testing with Synthetic Demo Data

The repository includes ready-to-use synthetic demo data so you can test every feature immediately without uploading proprietary files:

1. **Testing Module 1:**
   - Click **"Load Demo Inventory Data"** to load `demo_data/sample_inventory.csv`.
   - Ask: *"What is the total stock?"*, *"Show low stock items"*, or *"Which item is most expensive?"*.
2. **Testing Module 2:**
   - Click **"Load Demo Policy Docs"** to index `sample_policy_doc.txt` and `sample_faq_terms.txt`.
   - Click **"Execute Full 10-Turn Demonstration"** under the demo accordion to inspect the 10-turn multi-topic scenario.
3. **Testing Module 3:**
   - Click **"Load Synthetic Demo Package (All 10 Document Types)"**.
   - Inspect classification, confidence scores, human review flagging, PII masking, and JSON output for each document.

---

## 🔒 Security, Compliance & Ethical AI Principles

1. **Safe Deterministic Execution:** The natural language agent uses controlled, parsed Pandas aggregations. Arbitrary Python code execution via `eval()` or `exec()` is strictly forbidden.
2. **Zero Hallucination Guarantee:** Extraction routines return `null` when data is missing rather than generating synthetic or assumed values.
3. **PII Masking & Data Privacy:** Identity and financial records are masked before display and export to comply with UIDAI and privacy standards.
4. **Synthetic Data Transparency:** All demo files utilize fictional names and synthetic identifiers. No confidential company data was utilized or exposed.

---

## 📋 Evaluation Verification Checklist

- [x] **Single web application** with clean dashboard layout.
- [x] **Three separate module tabs** (Inventory Agent, Document Assistant, Document Processor).
- [x] **Module 1:** Excel/CSV upload, Pandas analysis, Plain English query answering, KPI cards, Supply chain glossary search, Safe execution.
- [x] **Module 2:** PDF/DOCX/TXT upload, Grounded QA, Source filename & section citations, Multi-turn context retention, Topic shift handling, Anti-repetition, 10-turn interactive demo.
- [x] **Module 3:** Multi-doc upload, 10 Document Type classifications, Required field extraction, Individual confidence scores, Low-confidence human review flagging, OCR support, Handwriting disclaimer, Strict null handling, PII masking, Structured JSON export.
- [x] **Code Quality:** Beginner-friendly, thoroughly commented, organized directory structure, `.gitignore`, `requirements.txt`, automated unit tests.
