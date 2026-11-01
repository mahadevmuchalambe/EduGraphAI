# EduGraphAI – DBATU ScholarAI

### AI-Powered Academic Question Answering System Using RAG and Knowledge Graphs

EduGraphAI is a local AI-powered academic assistant designed to help students understand their subjects using study materials uploaded by professors.

Professors can upload PDF notes, and students can ask questions through an AI chatbot. The system retrieves relevant information from uploaded study materials and generates answers with source PDF and page references.

## 🚀 Key Features

- **Professor Dashboard:** Allows professors to upload academic PDF materials.
- **Student Dashboard:** Provides students with access to available study materials and the AI chatbot.
- **PDF Processing:** Extracts text from uploaded PDF documents.
- **Retrieval-Augmented Generation (RAG):** Retrieves relevant information from professor-uploaded notes to generate answers.
- **Knowledge Graph:** Extracts and stores concepts and relationships from study materials.
- **AI Chatbot:** Answers academic questions using a locally running language model.
- **Source References:** Displays relevant PDF names and page references with answers.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| SQLite | Database |
| Ollama | Local LLM execution |
| Llama 3.2 (3B) | AI language model |
| Sentence Transformers | Text embeddings |
| PyMuPDF | PDF text extraction |
| HTML, CSS | User interface |
| RAG | Context-based answer generation |
| Knowledge Graph | Concept and relationship representation |

## ⚙️ System Requirements

- Windows 10/11 or compatible operating system
- Python
- Git
- Ollama
- 8 GB RAM minimum recommended; 16 GB recommended

## 💻 Installation and Setup

**1. Clone the repository**

```bash
git clone https://github.com/mahadevmuchalambe/EduGraphAI.git
```

**2. Open the project folder**

```bash
cd EduGraphAI
```

**3. Create a virtual environment**

```bash
python -m venv venv
```

**4. Activate the virtual environment**

Windows:

```bash
venv\Scripts\activate
```

**5. Install dependencies**

```bash
pip install -r requirements.txt
```

**6. Install and run the Ollama model**

```bash
ollama pull llama3.2:3b
```

Make sure Ollama is running.

**7. Run the application**

```bash
python app.py
```

Open the local URL displayed in your terminal.

## 🧠 How It Works

1. Professor uploads PDF study materials.
2. The system extracts text from PDF documents.
3. Extracted text is divided into smaller chunks.
4. Sentence Transformers generates text embeddings.
5. Relevant chunks are retrieved when a student asks a question.
6. Ollama's Llama 3.2 model generates an answer using the retrieved context.
7. The system provides relevant source PDF and page references.
8. Knowledge Graph modules extract and store concepts and relationships.

## 📂 Project Structure

```text
EduGraphAI/
│
├── app.py
├── rag_engine.py
├── graph_engine.py
├── text_extract.py
├── check_graph.py
├── requirements.txt
├── README.md
│
├── static/
│   ├── DBATU Logo.png
│   └── campus.png
│
├── uploads/
└── edugraph.db
```

*Note: The database and uploaded PDF files are kept locally and should not be committed to the public repository.*

## 🎯 Project Objective

The main objective of EduGraphAI is to provide students with an AI-based academic learning assistant that generates context-aware answers from professor-provided study materials.

## 🔮 Future Scope

- Support for additional document formats.
- Improved knowledge graph-based question answering.
- Multilingual academic support.
- Advanced search and analytics.
- Cloud deployment for wider accessibility.

## 👨‍💻 Developer

**Mahadev Muchalambe**

B.Tech – Computer Engineering  
Dr. Babasaheb Ambedkar Technological University (DBATU), Lonere, Maharashtra, India.

---

*EduGraphAI is an academic student project and is not an official DBATU university service.*
