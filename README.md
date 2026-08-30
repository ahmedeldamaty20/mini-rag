# Mini-RAG: Production-Grade Asynchronous Retrieval-Augmented Generation Architecture

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-5.4+-37B24D.svg)](https://docs.celeryq.dev/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)](https://www.docker.com/)
[![Notion Learning Notes](https://img.shields.io/badge/Notion-Learning%20Notes-000000?style=for-the-badge&logo=notion)](https://app.notion.com/p/mini-rag-notes-3c98ceeb768e80c1b536df7970d4c5dd?source=copy_link)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> 📝 **Developer Learning Notes & Insights**:
> Explore the author's personal Notion notes containing key engineering learnings, trade-offs, and architectural takeaways acquired while building Mini-RAG:
>
> 🚀 👉 [**Read Mini-RAG Learning Notes on Notion**](https://app.notion.com/p/mini-rag-notes-3c98ceeb768e80c1b536df7970d4c5dd?source=copy_link)

---

> This `README.md` provides a high-level, production-oriented overview of Mini-RAG.
> 
> 📖 **Deep Technical Architecture**: For route-by-route deep dives, exact class relationships, internal data flows, and database schema mappings, see:
> [**PROJECT_ARCHITECTURE.md**](https://github.com/ahmedeldamaty20/mini-rag/blob/main/PROJECT_ARCHITECTURE.md)

---

**Mini-RAG** is a scalable, resilient, production-ready Retrieval-Augmented Generation (RAG) framework designed for asynchronous document processing, vector search indexing, and LLM-powered context retrieval.

Built with **FastAPI**, **Celery**, **RabbitMQ**, **Redis**, **PostgreSQL / PgVector**, **Qdrant**, **Prometheus**, and **Grafana**, Mini-RAG handles long-running ETL and embedding workloads asynchronously while providing custom SHA-256 idempotency protection, worker crash recovery, and multi-vendor provider abstraction.

---

## Table of Contents

- [1. Developer Learning Notes (Notion)](#1-developer-learning-notes-notion)
- [2. Project Overview](#2-project-overview)
- [3. Architecture Overview](#3-architecture-overview)
- [4. Request / Data Flow](#4-request--data-flow)
- [5. Asynchronous Processing](#5-asynchronous-processing)
- [6. Redis Integration](#6-redis-integration)
- [7. Idempotency & Task Deduplication](#7-idempotency--task-deduplication)
- [8. RAG Pipeline](#8-rag-pipeline)
- [9. Vector Database & Semantic Search](#9-vector-database--semantic-search)
- [10. LLM & Embedding Provider Architecture](#10-llm--embedding-provider-architecture)
- [11. Services Overview](#11-services-overview)
- [12. Project Structure](#12-project-structure)
- [13. API Reference](#13-api-reference)
- [14. Observability & Monitoring](#14-observability--monitoring)
- [15. Production Reliability & Fault Tolerance](#15-production-reliability--fault-tolerance)
- [16. Running the Project](#16-running-the-project)
- [17. Configuration](#17-configuration)
- [18. Deep Architecture Documentation](#18-deep-architecture-documentation)

---

## 1. Developer Learning Notes (Notion)

Beyond system design and production code, building Mini-RAG involved key trade-offs, performance tuning, and architectural insights around asynchronous queues, idempotency, vector databases, and LLM integrations.

Access the complete developer learning notes, key takeaways, and design rationale on Notion:

[![Notion Notes](https://img.shields.io/badge/Notion-Mini--RAG%20Learning%20Notes-000000?style=for-the-badge&logo=notion)](https://app.notion.com/p/mini-rag-notes-3c98ceeb768e80c1b536df7970d4c5dd?source=copy_link)

👉 📝 [**Read Mini-RAG Learning Notes on Notion**](https://app.notion.com/p/mini-rag-notes-3c98ceeb768e80c1b536df7970d4c5dd?source=copy_link)

---

## 2. Project Overview

### What Mini-RAG Is
Mini-RAG is an enterprise-grade backend system designed to ingest text and PDF documents, chunk them dynamically, extract vector embeddings, store them in high-performance vector databases, and synthesize contextual answers using Large Language Models (LLMs).

### The Problem It Solves
Traditional RAG backends suffer from critical operational bottlenecks when processing documents:
1. **Synchronous Ingestion Bottlenecks**: Blocking HTTP request handlers while parsing large PDFs or fetching embeddings leads to client timeouts and thread pool exhaustion.
2. **Duplicate Ingestion Risks**: Worker restarts or transient API failures cause repetitive, costly embedding generation and database duplication.
3. **Vendor Lock-in**: Tight coupling to single vector databases or LLM APIs prevents seamless infrastructure migration.

Mini-RAG resolves these issues by decoupling HTTP request handling from background processing, enforcing strict SHA-256 task idempotency, and providing abstract factory interfaces for vector databases and LLM backends.

### Key Features
- **Asynchronous Task Queue**: Offloads text extraction, chunking, and embedding generation to distributed Celery workers backed by RabbitMQ.
- **SHA-256 Idempotency Engine**: `IdempotencyManager` hashes task signatures to prevent duplicate task execution and redundant vendor API costs.
- **Pluggable Vector DB Factory**: Seamless switching between **Qdrant** and **PgVector** via configuration.
- **Pluggable LLM/Embedding Factory**: Unified interfaces for **OpenAI** and **Cohere** for generation and vector embeddings.
- **Multi-Lingual Template Engine**: Localization-aware RAG prompt templates (supporting English and Arabic).
- **Full Observability Stack**: Built-in Prometheus metrics middleware, Grafana dashboards, Node Exporter, Postgres Exporter, and Celery Flower monitoring.

### Main Technologies Used
- **Core App**: Python 3.12+, FastAPI, Pydantic V2
- **Database & ORM**: PostgreSQL, PgVector, SQLAlchemy 2.0 (Async), Alembic
- **Task Queue & Caching**: Celery, RabbitMQ (AMQP Broker), Redis (Result Backend & Caching)
- **Vector Engine**: Qdrant, PgVector
- **LLM / Embedding Providers**: OpenAI API, Cohere API
- **Monitoring & Metrics**: Prometheus, Grafana, Flower, Node Exporter, Postgres Exporter
- **Web Server & Containerization**: Nginx, Docker, Docker Compose, `uv`

---

## 3. Architecture Overview

Mini-RAG uses a decoupled multi-layer architecture split into HTTP Routing, Controller Orchestration, Asynchronous Task Execution, Data & Vector Storage, AI Providers, and Infrastructure Monitoring.

```mermaid
graph TD

    User([HTTP Client / Frontend]) -->|HTTP| Nginx[Nginx Reverse Proxy]

    Nginx -->|Proxy :8000| FastAPI[FastAPI Web Server]

    subgraph Application["Application Core"]
        FastAPI --> Routes[API Routes]
        Routes --> Controllers[Controllers]
        Controllers --> Idempotency[IdempotencyManager]
    end

    subgraph Async["Asynchronous Workflow"]
        Controllers -->|Dispatch Tasks| Celery[Celery App]
        Celery -->|AMQP| RabbitMQ[RabbitMQ Broker]
        RabbitMQ --> Worker[Celery Worker]
        Worker -->|Task Results| Redis[(Redis)]
        Worker -->|Execution Status| Idempotency
    end

    subgraph Storage["Data & Vector Storage"]
        Controllers -->|Queries| PostgreSQL[(PostgreSQL + pgvector)]
        Worker -->|Write Data| PostgreSQL
        Worker -->|Store Embeddings| Qdrant[(Qdrant)]
        Controllers -->|Vector Search| Qdrant
    end

    subgraph AI["AI Providers"]
        Controllers --> ProviderFactory[LLM Provider Factory]
        Worker --> ProviderFactory
        ProviderFactory --> OpenAI[OpenAI API]
        ProviderFactory --> Cohere[Cohere API]
    end

    subgraph Observability["Observability"]
        FastAPI -.->|Metrics| Prometheus[Prometheus]
        NodeExporter[Node Exporter] --> Prometheus
        PostgresExporter[Postgres Exporter] --> Prometheus
        Prometheus --> Grafana[Grafana]
        Worker -.-> Flower[Celery Flower]
        RabbitMQ -.-> Flower
    end
```

---

## 4. Request / Data Flow

Mini-RAG segregates requests into **Synchronous Query Workflows** (instant vector search and response generation) and **Asynchronous ETL Workflows** (file ingestion, chunking, and embedding generation).

### Synchronous RAG Search & Generation Flow

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as FastAPI Router
    participant NLP as NLPController
    participant LLM as LLMProviderFactory
    participant VDB as VectorDBProviderFactory
    participant DB as PostgreSQL

    Client->>API: POST /api/v1/nlp/index/answer/{project_id}
    API->>NLP: answer_project_question(project_id, search_request)
    NLP->>DB: Fetch Project Metadata
    NLP->>LLM: Generate Embedding for Query String
    LLM-->>NLP: Query Vector Array
    NLP->>VDB: Search Top-K Vector Distance (Cosine / Dot / Euclidean)
    VDB-->>NLP: Relevant Document Chunks + Similarity Scores
    NLP->>LLM: Render Template & Call Chat Completion API
    LLM-->>NLP: Synthesized Answer Text
    NLP-->>API: Response Model (answer, prompt, retrieved_chunks)
    API-->>Client: HTTP 200 OK Response
```

### Asynchronous Data Ingestion & Processing Flow

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as FastAPI Router
    participant Controller as DataController / ProcessController
    participant Idem as IdempotencyManager
    participant Celery as Celery Producer
    participant Broker as RabbitMQ Broker
    participant Worker as Celery Worker
    participant DB as PostgreSQL / Vector DB

    Client->>API: POST /api/v1/data/process/{project_id}
    API->>Controller: process_project_files(project_id)
    Controller->>Idem: create_task_record("process_project_files", args)
    Idem->>DB: Insert CeleryTaskExecution (Status: PENDING)
    Controller->>Celery: dispatch_task.delay(project_id)
    Celery->>Broker: Publish AMQP Message to file_processing_queue
    Controller-->>API: Task Submission Accepted
    API-->>Client: HTTP 200 OK (task_id, execution_id)
    
    Broker->>Worker: Deliver Task Message
    Worker->>Idem: should_execute_task(task_name, args_hash)
    Worker->>Worker: Parse Files -> Extract Text -> Split Chunks -> Embed
    Worker->>DB: Save Data Chunks & Vector Embeddings
    Worker->>Idem: update_task_record(execution_id, status="SUCCESS")
```

---

## 5. Asynchronous Processing

### Why Celery is Used
Document ETL operations (parsing large PDF files, clean text extraction, text chunking, and network calls to external embedding APIs) are resource-intensive and unpredictable in latency. Running these directly within FastAPI request threads causes HTTP timeouts, blocks worker loops, and degrades user experience. Celery offloads these heavy computational loads to background worker processes.

### Message Broker (RabbitMQ)
**RabbitMQ** serves as the primary AMQP message broker. It receives task payloads from FastAPI producers and routes them into durable AMQP queues. 

Dedicated queue routing configured in `celery_app.py`:
- `file_processing_queue`: Handles document parsing, file reads, and content extraction (`process_project_files`, `process_and_push_data_to_vector_db`).
- `data_indexing_queue`: Handles chunking and embedding push tasks (`index_data_content`).
- `default`: Handles general background and beat maintenance tasks (`clean_celery_executions_table`).

### Task Chains & Workflows
Mini-RAG uses Celery signatures and chains to coordinate multi-stage background processes. In `ProcessController.py`, file processing and vector database indexing are chained sequentially:

```python
# Task Chain: Process Files -> Push Embeddings to Vector DB
task_chain = chain(
    process_project_files.s(project_id=project_id),
    process_and_push_data_to_vector_db.s(project_id=project_id)
)
```

### Worker Acknowledgements (`acks_late`)
To prevent data loss during worker failures, Mini-RAG enforces late task acknowledgements:
```python
task_acks_late = True
```
Under `task_acks_late`, a worker acknowledges a message back to RabbitMQ **only after** the task execution finishes. If a worker process crashes or loses connection mid-execution, RabbitMQ detects the channel closure and re-queues the message for another worker.

### Celery Processing Architecture Diagram

```mermaid
flowchart LR
    Client([HTTP Client]) -->|Submit Processing Request| FastAPI[FastAPI App]
    FastAPI -->|1. Register Task Record| Idem[(Idempotency DB)]
    FastAPI -->|2. Dispatch Task| CeleryClient[Celery Producer]
    CeleryClient -->|3. Publish AMQP Message| RabbitMQ{RabbitMQ Broker}
    
    subgraph RabbitMQ Queues
        RabbitMQ --> Queue1[file_processing_queue]
        RabbitMQ --> Queue2[data_indexing_queue]
        RabbitMQ --> Queue3[default]
    end
    
    Queue1 -->|Consume| Worker1[Celery Worker Node 1]
    Queue2 -->|Consume| Worker2[Celery Worker Node 2]
    
    Worker1 -->|4. Verify Execution & Hash| Idem
    Worker1 -->|5. Store Task Results| Redis[(Redis Result Backend)]
    Worker1 -->|6. Persist Chunks & Vectors| VectorDB[(PgVector / Qdrant)]
```

---

## 6. Redis Integration

### Role of Redis in Mini-RAG
**Redis** is configured as the **Celery Result Backend** (`CELERY_RESULT_BACKEND`). It provides high-speed in-memory state tracking for task statuses and execution return values.

### Key Redis Responsibilities
1. **Result Storage**: Stores return values and exception backtraces of Celery tasks.
2. **Result Expiration**: Task results automatically expire after 1 hour (`result_expires = 3600`) to prevent memory leaks.
3. **Health Checking**: Probed via `redis-cli ping` health checks in Docker Compose.

```mermaid
graph TD
    Worker[Celery Worker] -->|Set Task Result / State| Redis[(Redis Key-Value Store)]
    FastAPI[FastAPI Controller] -->|Fetch Task Status by ID| Redis
    RedisBeat[Celery Beat Schedule] -->|Track Periodic Schedules| Redis
```

---

## 7. Idempotency & Task Deduplication

### Why Idempotency is Crucial
In distributed asynchronous systems, client retries, network blips, or worker restarts can cause the same task payload to be enqueued multiple times. Executing document chunking or vector embedding generation twice causes:
- Duplicate chunk records in PostgreSQL/PgVector.
- Duplicate vector points in Qdrant.
- Unnecessary financial costs from repeated LLM embedding API calls.

### How `IdempotencyManager` Works
Mini-RAG implements a custom database-backed `IdempotencyManager` (`src/utils/IdempotencyManager.py`).

1. **SHA-256 Task Argument Hashing**: Task arguments and the task name are combined into a canonical JSON object with sorted keys and hashed via SHA-256 (`create_args_hash`).
2. **Database Tracking (`CeleryTaskExecution`)**: Each task execution corresponds to a row in PostgreSQL storing `task_name`, `celery_task_id`, `status`, `task_args`, `task_args_hash`, `started_at`, `ended_at`, and `result`.
3. **Pre-Execution Check (`should_execute_task`)**: Before executing business logic, the worker checks `CeleryTaskExecution`:
   - If status is `SUCCESS`: Skip execution completely and return cached results.
   - If status is `PENDING` or `STARTED` (and within time limit `600s + 60s` gap): Skip duplicate execution.
   - If status is `FAILURE` or lock expired: Re-execute task.

### Task Lifecycle Flowchart

```mermaid
flowchart TD
    Start([Task Execution Request]) --> Hash[Generate SHA-256 Hash of task_name + task_args]
    Hash --> QueryDB[Query CeleryTaskExecution Table]
    QueryDB --> RecordExists{Record Exists?}
    
    RecordExists -- No --> CreateRec[Create Record: PENDING]
    CreateRec --> RunTask[Execute Worker Logic]
    
    RecordExists -- Yes --> CheckStatus{Check Task Status}
    CheckStatus -- SUCCESS --> Reuse[Skip Execution & Return Existing Record]
    CheckStatus -- PENDING / STARTED --> CheckTime{Time Elapsed < Time Limit?}
    CheckTime -- Yes --> Skip[Skip Execution - Task Currently Running]
    CheckTime -- No --> RunTask
    CheckStatus -- FAILURE --> RunTask
    
    RunTask --> TaskResult{Task Succeeded?}
    TaskResult -- Yes --> MarkSuccess[Update Status: SUCCESS + ended_at]
    TaskResult -- No --> MarkFail[Update Status: FAILURE + error log]
    MarkSuccess --> End([Finished])
    MarkFail --> End
```

---

## 8. RAG Pipeline

Mini-RAG implements an end-to-end Retrieval-Augmented Generation lifecycle.

```mermaid
flowchart TD
    Doc[Document Upload: PDF / TXT] -->|Extract Raw Text| Extract[Text Extraction Engine]
    Extract -->|Character / Token Splitting| Chunk[Text Chunking & Cleaning]
    Chunk -->|Generate Vector Representation| Embed[LLM Embedding Client: OpenAI / Cohere]
    Embed -->|Store Vectors & Metadata| VDB[(Vector Database: Qdrant / PgVector)]
    
    UserQuery([User Question]) -->|Generate Query Vector| EmbedQuery[LLM Embedding Client]
    EmbedQuery -->|Cosine / Dot / Euclidean Search| VDB
    VDB -->|Retrieve Top-K Context Chunks| Context[Context Aggregator]
    
    Context -->|Parse Localization Template| Template[TemplateParser en/ar]
    Template -->|Augmented System Prompt| LLM[LLM Generation Client: OpenAI / Cohere]
    LLM -->|Synthesized Contextual Response| Answer([Final Answer to Client])
```

---

## 9. Vector Database & Semantic Search

### Vector DB Abstraction Layer
Mini-RAG abstracts vector database operations via `VectorDBInterface` and instantiates them via `VectorDBProviderFactory` (`src/stores/vectordb/VectorDBProviderFactory.py`).

### Supported Vector Databases
1. **Qdrant (`QdrantDBProvider`)**: Local or distributed vector database utilizing HNSW indexes and payload filtering.
2. **PgVector (`PgVectorProvider`)**: PostgreSQL extension storing embeddings directly alongside metadata tables in relational schemas.

### Key Capabilities
- **Distance Metrics**: Supports `COSINE`, `DOT`, and `EUCLIDEAN` vector metrics.
- **Collection Management**: Automatic collection creation based on embedding vector dimensions (`EMBEDDING_MODEL_SIZE`).
- **PgVector Index Threshold**: Configurable threshold (`VECTOR_DB_PGVECTOR_INDEX_THREADHOLD`) to automatically create HNSW vector indexes when chunk count exceeds thresholds.

---

## 10. LLM & Embedding Provider Architecture

Mini-RAG decouples AI provider logic using the Abstract Factory Pattern (`src/stores/llm/LLMProviderFactory.py`).

### Supported Providers
- **OpenAI (`OpenAIProvider`)**: Generates text responses (e.g., `gpt-4o-mini`) and vector embeddings (e.g., `text-embedding-3-small`).
- **Cohere (`CohereProvider`)**: Generates text responses (e.g., `command-r-plus`) and embeddings (e.g., `embed-multilingual-v3.0`).

### Multi-Lingual Template Engine
RAG prompt generation uses a `TemplateParser` configured for default and primary languages (`en` and `ar`). System prompts are rendered dynamically with context snippets and project metadata.

```mermaid
classDiagram
    class LLMInterface {
        <<interface>>
        +set_generation_model(model_name)
        +set_embedding_model(model_name, size)
        +generate_text(prompt, chat_history)
        +embed_text(text)
        +embed_batch(texts)
    }

    class OpenAIProvider {
        +api_key: str
        +api_url: str
        +generate_text(...)
        +embed_text(...)
    }

    class CohereProvider {
        +api_key: str
        +generate_text(...)
        +embed_text(...)
    }

    class LLMProviderFactory {
        +config: Settings
        +get_provider(provider_name) LLMInterface
    }

    LLMInterface <|.. OpenAIProvider
    LLMInterface <|.. CohereProvider
    LLMProviderFactory ..> LLMInterface
```

---

## 11. Services Overview

| Service Name | Technology / Image | Port(s) | Responsibility | Communication Protocol |
| :--- | :--- | :--- | :--- | :--- |
| **FastAPI** | `minirag:latest` | `8000` | Core HTTP REST API server for projects, file upload, and RAG search | HTTP / REST |
| **Celery Worker** | `minirag:latest` | N/A | Distributed background worker executing processing and indexing tasks | AMQP (RabbitMQ) / Redis / SQL |
| **Celery Beat** | `minirag:latest` | N/A | Scheduler for periodic background maintenance tasks | AMQP (RabbitMQ) |
| **Celery Flower** | `minirag:latest` | `5555` | Web dashboard for real-time Celery worker monitoring | HTTP |
| **Nginx** | `nginx:1.30.4` | `80` | Reverse proxy and load balancer routing requests to FastAPI | HTTP Proxy |
| **PostgreSQL / PgVector** | `pgvector:0.8.6-pg17` | `5432` | Primary relational store for metadata, assets, chunks, task executions, and vectors | PostgreSQL Async Wire Protocol |
| **Qdrant** | `qdrant/qdrant:v1.19.0` | `6333`, `6334` | High-performance vector database storing document embeddings | REST / gRPC |
| **Redis** | `redis:8.8` | `6379` | In-memory store acting as Celery Result Backend and caching tier | Redis RESP Protocol |
| **RabbitMQ** | `rabbitmq:3.13-management` | `5672`, `15672` | AMQP message broker managing Celery queues and worker routing | AMQP 0-9-1 / HTTP UI |
| **Prometheus** | `prom/prometheus:v3.14.0` | `9090` | Time-series metrics collector pulling system and application metrics | HTTP Scraping |
| **Grafana** | `grafana/grafana:13.1.4` | `3000` | Visualization dashboard for metrics and observability alerts | HTTP |
| **Node Exporter** | `prom/node-exporter:v1.12.1` | `9100` | Host hardware and OS metrics collector for Prometheus | HTTP Scraping |
| **Postgres Exporter** | `postgres-exporter:v0.20.1` | `9187` | PostgreSQL database performance metrics exporter | HTTP Scraping |

---

## 12. Project Structure

```
mini-rag/
├── docker/                             # Docker Compose & service configurations
│   ├── docker-compose.yml              # Multi-container orchestration
│   ├── minirag/                        # Application Dockerfile & entrypoint
│   ├── nginx/                          # Nginx reverse proxy configuration
│   ├── prometheus/                     # Prometheus scraping rules
│   └── rabbitmq/                       # RabbitMQ broker settings
├── docs/                               # Developer manuals & architecture roadmaps
├── src/                                # Source code directory
│   ├── assets/                         # Local asset storage & database files
│   ├── controllers/                    # Business logic controllers
│   │   ├── BaseController.py           # File & path helper utilities
│   │   ├── DataController.py           # File upload & asset management
│   │   ├── NLPController.py            # RAG search & LLM prompt synthesis
│   │   ├── ProcessController.py        # Asynchronous ETL task dispatching
│   │   └── ProjectController.py        # Project CRUD logic
│   ├── helpers/                        # Configuration & environment loader
│   │   └── config.py                   # Pydantic Settings management
│   ├── mini_rag/                       # Application initializers
│   │   ├── main.py                     # FastAPI application factory & router mounting
│   │   └── celery_app.py               # Celery app instance & queue configurations
│   ├── models/                         # Database ORM models & Pydantic schemas
│   │   ├── db_schemas/minirag/         # SQLAlchemy models & Alembic migrations
│   │   └── enums/                      # Application state enums
│   ├── routes/                         # FastAPI HTTP endpoint definitions
│   │   ├── base.py                     # Health check & welcome endpoints
│   │   ├── data.py                     # Upload & process routes
│   │   └── nlp.py                      # Push index, search, and answer routes
│   ├── stores/                         # External provider abstraction layer
│   │   ├── llm/                        # LLM provider implementations (OpenAI, Cohere)
│   │   └── vectordb/                   # Vector DB implementations (Qdrant, PgVector)
│   ├── tasks/                          # Celery task definitions
│   │   ├── file_processing.py          # Document parsing & text extraction
│   │   ├── data_indexing.py            # Embedding generation & vector storage
│   │   ├── process_workflow.py         # Task chain orchestrator
│   │   └── mainteinance.py             # Idempotency table cleanup beat task
│   └── utils/                          # Core system utilities
│       ├── IdempotencyManager.py       # SHA-256 task deduplication engine
│       └── metrics.py                  # Prometheus HTTP middleware
├── flowerconfig.py                     # Celery Flower configuration
├── pyproject.toml                      # Project dependencies & metadata (uv)
├── PROJECT_ARCHITECTURE.md              # In-depth internal technical documentation
└── README.md                           # Main GitHub documentation
```

---

## 13. API Reference

High-level summary of primary REST API endpoints available under `/api/v1`:

| Endpoint | Method | Responsibility | Parameters / Body |
| :--- | :--- | :--- | :--- |
| `/api/v1/welcome` | `GET` | API Health Check and welcome message | None |
| `/api/v1/data/upload/{project_id}` | `POST` | Upload text or PDF files for a project | `project_id` (Path), `file` (Form Upload) |
| `/api/v1/data/process/{project_id}` | `POST` | Trigger asynchronous file extraction and indexing task chain | `project_id` (Path), `process_request` (Body) |
| `/api/v1/nlp/index/push/{project_id}` | `POST` | Manually push embeddings to the vector database | `project_id` (Path), `push_request` (Body) |
| `/api/v1/nlp/index/info/{project_id}` | `GET` | Fetch vector database collection info and point counts | `project_id` (Path) |
| `/api/v1/nlp/index/search/{project_id}` | `POST` | Execute vector similarity search without LLM generation | `project_id` (Path), `search_request` (Body) |
| `/api/v1/nlp/index/answer/{project_id}` | `POST` | Execute full RAG pipeline (search context + synthesize LLM answer) | `project_id` (Path), `answer_request` (Body) |

> 💡 For comprehensive parameter definitions, Pydantic schemas, and example response payloads, refer to [**PROJECT_ARCHITECTURE.md**](PROJECT_ARCHITECTURE.md#3-route-by-route-deep-dive).

---

## 14. Observability & Monitoring

Mini-RAG includes a production monitoring stack built into its architecture.

### Prometheus Metrics
FastAPI registers Prometheus metrics middleware (`src/utils/metrics.py`) exposed at `/metrics`:
- `http_requests_total`: Counter tracking total HTTP requests partitioned by `method`, `endpoint`, and `http_status`.
- `http_request_latency_seconds`: Histogram measuring HTTP request processing latency.

### Dashboards & Exporters
- **Grafana (`:3000`)**: Pre-configured visualization dashboards pulling metrics from Prometheus.
- **Node Exporter (`:9100`)**: Provides host CPU, memory, network, and disk metrics.
- **Postgres Exporter (`:9187`)**: Monitors PostgreSQL connection pools, transaction throughput, and disk footprint.
- **Flower (`:5555`)**: Celery web interface monitoring real-time queue lengths, task latency, worker health, and task failures.

---

## 15. Production Reliability & Fault Tolerance

Mini-RAG enforces production resilience through several architectural guarantees:

1. **Decoupled Asynchronous Processing**: Offloads heavy workloads to Celery, maintaining responsive FastAPI HTTP response times.
2. **Late Task Acknowledgements (`task_acks_late=True`)**: Unacknowledged messages are automatically re-routed by RabbitMQ if a worker container abruptly crashes.
3. **SHA-256 Idempotency Engine**: Deduplicates repetitive task calls to protect data integrity and avoid duplicate vendor API costs.
4. **Task Time Limits**: Enforces hard execution timeouts (`600s`) to terminate hung threads.
5. **Durable Persistence**: All databases (PostgreSQL, Qdrant, Redis, RabbitMQ) map to named Docker volume mounts to prevent data loss across container restarts.
6. **Container Health Checks**: Services use health check criteria (`pg_isready`, `redis-cli ping`, `rabbitmq-diagnostics ping`) before launching dependent application services.

---

## 16. Running the Project

### Prerequisites
- **Docker** & **Docker Compose** installed on host machine.
- **Python 3.12+** & [**`uv`**](https://github.com/astral-sh/uv) (for local CLI development).

### 1. Environment Setup
Copy `.env.example` to `.env` and fill in necessary secrets:
```bash
cp .env.example .env
```

### 2. Launch Services with Docker Compose
To start the entire Mini-RAG container stack (FastAPI, Celery Worker, Celery Beat, Flower, Nginx, PostgreSQL, Qdrant, Redis, RabbitMQ, Prometheus, Grafana, Exporters):

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

### 3. Apply Database Migrations
Run Alembic migrations to construct database tables in PostgreSQL:

```bash
docker compose -f docker/docker-compose.yml exec fastapi uv run alembic upgrade head
```

### 4. Access Service Dashboards

- **FastAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Nginx Reverse Proxy**: [http://localhost:80](http://localhost:80)
- **Celery Flower Dashboard**: [http://localhost:5555](http://localhost:5555)
- **RabbitMQ Management UI**: [http://localhost:15672](http://localhost:15672)
- **Prometheus Metrics**: [http://localhost:9090](http://localhost:9090)
- **Grafana Dashboards**: [http://localhost:3000](http://localhost:3000)
- **Qdrant Vector Web UI**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

---

## 17. Configuration

Mini-RAG uses Pydantic Settings (`src/helpers/config.py`) to parse environment variables from `.env`.

### Key Configuration Categories

```env
# Application Settings
APP_NAME="mini-RAG"
APP_VERSION="0.1.0"
PRIMARY_LANGUAGE="en"

# PostgreSQL Configuration
POSTGRES_USERNAME="postgres"
POSTGRES_PASSWORD="secretpassword"
POSTGRES_HOST="pgvector"
POSTGRES_PORT=5432
POSTGRES_MAIN_DATABASE="minirag"

# Celery & Message Queue
CELERY_BROKER_URL="amqp://guest:guest@rabbitmq:5672//"
CELERY_RESULT_BACKEND="redis://:secretpassword@redis:6379/0"
CELERY_ACKS_LATE=True
CELERY_TASK_TIME_LIMIT=600

# Vector Database Selection (qdrant | pgvector)
VECTOR_DB_BACKEND="qdrant"
VECTOR_DB_DISTANCE_METHOD="cosine"

# LLM & Embedding Backends (openai | cohere)
GENERATION_BACKEND="openai"
GENERATION_MODEL_ID="gpt-4o-mini"
EMBEDDING_BACKEND="openai"
EMBEDDING_MODEL_ID="text-embedding-3-small"
EMBEDDING_MODEL_SIZE=1536
```

---

## 18. Deep Architecture Documentation

For in-depth implementation technical documentation, refer to:

👉 [**`PROJECT_ARCHITECTURE.md`**](PROJECT_ARCHITECTURE.md)

### `PROJECT_ARCHITECTURE.md` Contents
- **Deep Layered Architecture**: Component interactions and software boundaries.
- **Project Structure & Dependency Mapping**: Exhaustive analysis of module imports and file dependencies.
- **Route-by-Route Deep Dive**: Detailed query parameters, headers, payload models, and response structures for all API endpoints.
- **Function & Class Relationships**: Method signatures and class interaction diagrams.
- **Database Schema Architecture**: Relational design of `projects`, `assets`, `datachunks`, and `celery_task_executions`.
- **Developer Navigation Guide**: Step-by-step instructions for adding new routes, custom vector DB providers, or additional LLM backends.
