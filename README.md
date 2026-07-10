# Corporate Knowledge Base Automation PoC

This PoC describes an enterprise knowledge-base automation platform for a department-scale document set. The primary goal is not only to connect documents to an LLM. The goal is to automate repeatable knowledge work: document intake, indexing, retrieval, answer generation, source citation, evaluation, release control and operations monitoring.

## Delivery Positioning

This PoC belongs to the **Automation** direction of the portfolio, aligned with `your-own-domain.example`. It packages cloud-native delivery, CI/CD, GenAI and knowledge operations into a business-facing delivery note. The existing OLTP/OLAP, OEE and CCE projects remain the **Data** direction.

```text
Portfolio
  -> Data: OLTP, OLAP, governance, feature platform, MLOps
  -> Automation: enterprise knowledge base, AI workflow, CI/CD, platform delivery
```

The recommended business framing is:

```text
Internal knowledge is already available, but it is expensive to find, verify and reuse.
This PoC automates the knowledge-to-answer lifecycle with governed documents, citations,
evaluation, CI/CD and cloud deployment patterns.
```

## Business Value

| Automation area | Manual work reduced | Business value |
| --- | --- | --- |
| Document intake and indexing | Manually reading shared folders, PDFs and Word files | New knowledge becomes searchable quickly after upload |
| Question answering | Repeated SME, support and operations questions | Faster first response and fewer interruptions to specialists |
| Source-grounded answers | Manual copy/paste from multiple documents | Answers include traceable sources and reduce policy mismatch |
| Change management | Untracked document versions and stale answers | Versioned S3 objects, index versions and evaluation gates |
| Evaluation | Ad-hoc spot checks before demos | Regression question sets catch broken retrieval before release |
| Deployment | Manual server setup and script execution | CI/CD promotes tested app, infrastructure and prompt changes |

The automation story is important for a business PoC: the platform should show reduced turnaround time, fewer repeated questions, better answer consistency and measurable usage/quality signals.

## Feasibility And SWOT

| Area | Assessment |
| --- | --- |
| Technical feasibility | High for MVP1 because S3 + Bedrock Knowledge Bases avoids a self-managed vector DB. Medium for MVP2 because explicit vector DB, hybrid retrieval and private inference add operating complexity. |
| Business feasibility | High when the target department has repeated policy, process, product, delivery or support questions. Benefits are easiest to prove with before/after response-time and SME-deflection metrics. |
| Market capacity | Internal demand can be estimated as `departments x knowledge workers x repeated questions/month x average handling time`. External enterprise RAG demand is broad, but the PoC should prove one department workflow first. |
| Delivery feasibility | High if document owners, security reviewers and platform owners agree on scope. Risk increases when document ownership, access policy or source-of-truth status is unclear. |

| SWOT | Notes |
| --- | --- |
| Strengths | Fast MVP, cloud-managed RAG, source citations, clear automation story, strong fit with DevOps/platform delivery background. |
| Weaknesses | Answer quality depends on document quality, chunking, access metadata and user feedback loops. Fine-tuning does not solve stale or conflicting knowledge. |
| Opportunities | Department knowledge assistant, delivery-note assistant, operations Q&A, policy search, onboarding, support deflection, sales/pre-sales knowledge reuse. |
| Threats | Data leakage concern, unclear document ownership, stakeholder disagreement, high expectation for perfect answers, cost surprises from heavy usage or private GPU inference. |

## Recommended Tiers

| Tier | Best fit | Main AWS services | Vector DB ownership | Latency profile | Recommendation |
| --- | --- | --- | --- | --- | --- |
| 1. Lightweight managed RAG | One department, a few thousand documents, fast PoC | S3, Bedrock Knowledge Bases, Lambda or ECS/Fargate, API Gateway, Cognito/IAM | Hidden/managed by Bedrock | Lowest build effort; LLM dominates response time | Start here |
| 2. Medium RAG with explicit vector DB | More filters, multiple departments, custom retrieval, hybrid search | S3, Bedrock embeddings/LLM, OpenSearch Serverless or Aurora PostgreSQL pgvector, Step Functions, ECS/EKS | Team owns schema, index and refresh | Retrieval can be tuned; more ops responsibility | Use when managed KB is too limiting |
| 3. Medium+ RAG plus model tuning | Stable answer format, domain tone, classifier/extractor behavior, private inference needs | S3, vector DB, Bedrock or SageMaker fine-tuning, EKS/ECS CPU/GPU endpoint where needed | Team owns retrieval and model release gates | Fine-tuned model can reduce prompt size; CPU generation adds latency | Use after RAG quality is proven |

## Sizing Decision Rules

These are PoC planning thresholds, not cloud-provider hard limits. They are meant to answer: when is S3 + Bedrock Knowledge Bases enough, and when should the team own a vector database?

| Signal | Lightweight: S3 + Bedrock KB is enough | Medium: explicit vector DB | Heavy: vector DB + private endpoint/governed model path |
| --- | --- | --- | --- |
| Document count | 1-3,000 approved documents | 3,000-30,000 documents | 30,000+ documents |
| Estimated pages | Up to about 10,000 pages | 10,000-150,000 pages | 150,000+ pages |
| Estimated chunks | Up to about 50,000 chunks | 50,000-500,000 chunks | 500,000+ chunks |
| Departments | 1-3 departments | 3-20 departments | 20+ departments or enterprise-wide search |
| Daily questions | Up to about 1,000 internal questions/day | 1,000-20,000 questions/day | 20,000+ questions/day or strict p95 latency target |
| Weekly document changes | Up to about 500 changed docs/week | 500-5,000 changed docs/week | 5,000+ changed docs/week or near-real-time ingestion |
| Duplicate / near-duplicate rate | Below 10% after cleanup | 10-30%, needs canonical-source workflow | 30%+, source-of-truth conflict becomes a platform risk |
| Metadata filters | Simple filters: department, owner, effective date, confidentiality | Multi-field filters, ACL-aware retrieval, index versioning | Document-level ACL, region/legal rules, private inference, release gates |
| Recommendation | Start here; fastest business validation | Move here when retrieval quality and governance need control | Move here when scale, security, latency or private model ops justify it |

Quick rule of thumb:

```text
<= 3K docs / <= 10K pages / <= 50K chunks / duplicate rate < 10%
  -> S3 + Bedrock Knowledge Bases is enough for MVP1.

3K-30K docs / 10K-150K pages / 50K-500K chunks / duplicate rate 10-30%
  -> Use explicit vector DB: pgvector or OpenSearch.

> 30K docs / > 150K pages / > 500K chunks / duplicate rate > 30%
  -> Treat as governed platform: vector DB, private endpoint option, release gates.
```

Document count alone is not enough. A 500-document corpus with 80% duplicated policy PDFs can perform worse than a clean 5,000-document corpus. The real driver is usually **approved chunk count + duplicate/conflict rate + metadata/ACL complexity**.

## Duplicate And Document Cleaning Rules

| Step | Rule | Why it matters |
| --- | --- | --- |
| Inventory | Require `document_id`, title, owner, department, confidentiality, effective date, version and source URI before indexing | Without ownership, wrong answers cannot be fixed |
| Exact duplicate removal | Hash normalized text; keep the newest approved source and mark others as aliases/superseded | Prevents the retriever from returning the same answer multiple times |
| Near-duplicate review | Use token similarity; this PoC flags documents at Jaccard similarity `0.82+` | Catches same content copied into different templates |
| Canonical source selection | Prefer active effective date, approved owner and highest version | Avoids old policy docs beating the current policy |
| Conflict handling | If two active documents disagree, return both citations and route to owner | Hiding conflicts creates governance risk |
| Chunk hygiene | Remove boilerplate headers/footers, split tables carefully, keep source page/section metadata | Cleaner chunks improve citation quality and reduce hallucination risk |

The runnable code exposes this through:

```text
GET /api/corpus/profile
GET /api/architecture
```
## Runnable Code Implementation

This folder now includes a runnable three-tier implementation that mirrors the architecture discussion:

| Tier | Local implementation | Production mapping |
| --- | --- | --- |
| Lightweight | `LightweightManagedKbEngine` reads approved documents and simulates a managed `RetrieveAndGenerate` path | S3 + Bedrock Knowledge Bases + Lambda/ECS API wrapper |
| Medium | `MediumVectorDbEngine` chunks documents, creates deterministic embeddings and stores vectors in SQLite | Aurora PostgreSQL pgvector or OpenSearch Serverless with ingestion workers |
| Heavy | `HeavyPrivateRagEngine` reuses vector retrieval and routes answer generation through a private CPU/GPU endpoint simulator | Private model endpoint on EKS/ECS/SageMaker with fallback and release gates |

Code map:

```text
src/corp_kb/documents.py      document loading, metadata parsing and chunking
src/corp_kb/embeddings.py     deterministic local hashing embeddings
src/corp_kb/vector_store.py   SQLite vector index for the medium tier
src/corp_kb/engines.py        lightweight, medium and heavy RAG engines
src/corp_kb/app.py            FastAPI endpoints
src/corp_kb/cli.py            local CLI for ingest/query/tradeoffs
src/corp_kb/architecture.py   CI/CD, VPC, runner and GPU trade-off payloads
deploy/ci/                  GitHub, GitLab, Jenkins and Azure DevOps examples
deploy/ansible/             VM bootstrap example for Nginx/systemd hosts
deploy/databricks/          DAB-style evaluation job skeleton
```

Local run:

```powershell
cd pocs\corporate-knowledge-base-poc
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
python -m corp_kb.cli ingest --tier medium
python -m corp_kb.cli query --tier lightweight "What should MVP1 use?"
python -m corp_kb.cli query --tier medium "Where should metadata filters be enforced?" --department platform
python -m corp_kb.cli query --tier heavy "When should GPU be used?" --gpu
```

API run:

```powershell
python -m uvicorn corp_kb.app:app --host 127.0.0.1 --port 8090
```

Useful APIs:

```text
GET  /api/health
GET  /api/tiers
POST /api/ingest
POST /api/query
GET  /api/cicd/tradeoffs
GET  /api/corpus/profile
GET  /api/architecture
```

Example query payload:

```json
{
  "tier": "medium",
  "question": "Where should metadata filters be enforced?",
  "department": "platform",
  "top_k": 4
}
```
## Tier 1: Lightweight Bedrock Knowledge Base

Use this when the document set is a few thousand files for one department and the first objective is a credible automation demo.

```text
Department documents
  -> S3 raw document bucket
  -> Bedrock Knowledge Base sync
  -> RetrieveAndGenerate API
  -> Knowledge API / chatbot / workflow integration
  -> Answer with citations
```

Why this is a good first PoC:

- No self-managed vector database is required.
- S3 remains the durable document landing zone.
- Bedrock handles parsing, chunking, embedding, retrieval and answer generation behind one service boundary.
- The team can focus on access control, prompt policy, citations, evaluation and business workflow integration.

Minimum build:

| Component | Scope |
| --- | --- |
| S3 buckets | `raw-documents`, optional `processed-documents`, lifecycle policy, KMS encryption |
| Bedrock Knowledge Base | S3 data source, embedding model, sync schedule or manual sync |
| API layer | Lambda or small FastAPI service wrapping `RetrieveAndGenerate` |
| Auth | Corporate SSO/Cognito/IAM authorizer depending on environment |
| Observability | CloudWatch logs, request IDs, latency, error rate, answer feedback |
| Evaluation | Golden questions, expected source documents, groundedness checks |

## Tier 2: Medium RAG With Vector DB

Move to an explicit vector DB when the PoC needs custom retrieval behavior:

- Metadata filters by department, product, policy type, country, effective date or confidentiality level.
- Hybrid retrieval: vector similarity plus keyword/BM25.
- Custom chunking, table extraction, reranking or query rewriting.
- Index freshness dashboards and controlled reindexing.
- Reuse of embeddings across more than one AI workflow.

```text
S3 documents
  -> ingestion workflow
  -> parse / clean / chunk
  -> embedding model
  -> vector DB with metadata filters
  -> retrieval API
  -> Bedrock LLM
  -> answer, citation and audit log
```

Vector DB options:

| Option | Best fit | Trade-off |
| --- | --- | --- |
| Aurora PostgreSQL pgvector | Medium corpus, relational metadata, SQL-friendly team | Simple operating model, but not the strongest full-text search engine |
| OpenSearch Serverless vector engine | Hybrid search, larger corpus, search-heavy use cases | More search/index tuning concepts |
| Milvus on EKS | Self-hosted vector specialization | Higher Kubernetes and storage operations load |
| Bedrock Knowledge Bases | Lightweight managed path | Least custom control, fastest PoC |

## Tier 3: Fine-Tuning And Private/CPU/GPU Runtime

Fine-tuning should not be used as the primary knowledge store. RAG remains the source of truth for changing documents. Fine-tuning is useful for stable behavior:

- Answer format, tone and structured JSON output.
- Department-specific classification or extraction.
- Routing questions to the right workflow.
- Reducing prompt length for repeated, stable patterns.

CPU deployment is possible for low-concurrency or highly private use cases, especially with small quantized models. GPU is only justified when private inference must be interactive or high-throughput. A practical split is:

| Runtime | Best use |
| --- | --- |
| Bedrock hosted model | Main interactive PoC path |
| SageMaker or Bedrock fine-tuned model | Managed model release and evaluation |
| CPU endpoint on ECS/EKS | Low-QPS private fallback, batch summarization or non-critical latency path |
| GPU endpoint on G5/SageMaker | Low-latency private generation at higher QPS |

## MVP Roadmap

### MVP1: Department Knowledge Assistant

| Dimension | Plan |
| --- | --- |
| Business goal | Prove that a few thousand department documents can answer repeated questions with citations and reduce manual SME routing. |
| Scope | One department, approved documents, top 30-50 questions, web/API interface, answer feedback, basic evaluation. |
| Implementation | S3 document bucket, Bedrock Knowledge Bases, Lambda or ECS/Fargate API, API Gateway or ALB, Cognito/IAM, CloudWatch, Terraform, GitLab CI or GitHub Actions. |
| Not included | Custom vector DB, fine-tuning, GPU private inference, multi-department row-level security. |
| Estimated effort | 18-28 person-days: discovery 3, cloud/IAM/VPC 4, API/UI 5, KB setup 3, eval 4, CI/CD 3, demo/runbook 3. |
| Estimated cloud cost | Directional low PoC cost, usually driven by Bedrock model tokens, Knowledge Base retrieval/API usage, S3 storage, Lambda/ECS runtime and logs. For light internal usage this is usually a small experiment budget, but final numbers must be validated with AWS Pricing Calculator and the chosen model. |

MVP1 implementation steps:

```text
1. Confirm use case and stakeholders.
2. Inventory documents, owners, confidentiality and source-of-truth rules.
3. Upload approved files to S3 with metadata.
4. Create Bedrock Knowledge Base and run initial sync.
5. Build Knowledge API wrapper and optional simple web entry point.
6. Add SSO/IAM, request logging and answer feedback.
7. Run golden questions and citation review.
8. Package demo, cost view and operating runbook.
```

MVP1 key risks:

| Risk | Mitigation |
| --- | --- |
| Documents are stale or duplicated | Add owner, version, effective date and source-of-truth metadata before indexing. |
| Stakeholders disagree on the correct answer | Use citations and approval workflow; flag conflicting documents instead of hiding them. |
| Users expect perfect answers | Position as assisted search with cited evidence; include fallback to human owner. |
| Sensitive data exposure | Start with one department and approved corpus; enforce server-side access controls. |
| Cost uncertainty | Cap usage, log token volume, run daily cost checks and keep model choice explicit. |

### MVP2: Governed Multi-Department RAG Platform

| Dimension | Plan |
| --- | --- |
| Business goal | Move from a single assistant to a governed reusable automation platform for multiple teams and delivery-note workflows. |
| Scope | Multi-department metadata filters, explicit vector DB, hybrid search, reindex workflow, GitLab pipeline, Maven-compatible Java service option, dashboard, richer evaluation. |
| Implementation | S3, Step Functions or Airflow/MWAA, parser/chunker workers on ECS/EKS, Bedrock embeddings/LLM, Aurora PostgreSQL pgvector or OpenSearch Serverless, GitLab CI, Terraform, optional Java/Spring Boot + Maven API service. |
| GPU/private inference | Optional. Prefer Bedrock first. Use GPU only when data policy or latency/throughput justifies private inference. Candidate shape: G5 family with NVIDIA A10G GPU for low-latency private model serving; CPU endpoints are better for low-QPS fallback or batch jobs. |
| Estimated effort | 35-60 person-days: architecture/security 6, ingestion workflow 8, vector schema/index 8, retrieval API 8, GitLab/Maven/Terraform pipeline 6, evaluation 6, observability 5, migration/demo 5. |
| Estimated cloud cost | Medium PoC cost. Main drivers are vector DB baseline, ingestion/indexing compute, Bedrock token usage, NAT/endpoints/logs and optional always-on API/runtime. OpenSearch Serverless cost depends on OCU-hours and storage; Aurora Serverless depends on ACU usage and storage. GPU private inference can dominate cost if kept online. |

MVP2 implementation steps:

```text
1. Define department metadata model and access policy.
2. Build ingestion workflow: parse, clean, chunk, embed, upsert.
3. Choose vector DB: pgvector for SQL-friendly metadata, OpenSearch for hybrid search and larger retrieval.
4. Build Retrieval API with server-side filters and prompt assembly.
5. Add GitLab CI stages: test, Maven build if Java service is used, container build, Terraform plan/apply, RAG evaluation, approval.
6. Add dashboard: index freshness, answer feedback, failed ingestion, cost and latency.
7. Run canary with two departments and compare quality/cost with MVP1.
```

MVP2 key risks:

| Risk | Mitigation |
| --- | --- |
| Legacy source coupling | Add an anti-corruption ingestion layer; avoid direct runtime dependency on shared folders or legacy databases. |
| Poor data quality | Use maturity checks: freshness, duplicate detection, owner review, rejected-document queue and evaluation failures. |
| Access-control complexity | Make metadata filtering mandatory in the API, not optional UI behavior. |
| Stakeholder alignment | Establish document owner, approver, security reviewer and product owner before adding departments. |
| Vector DB cost | Start with pgvector or dev-test OpenSearch, set max OCU/ACU budgets, avoid always-on GPU unless justified. |
| Fine-tuning misuse | Keep RAG as source of truth; fine-tune only format, tone, extraction or routing behavior. |

## Instance, Zone And VPC Selection

| Layer | MVP1 choice | MVP2 choice |
| --- | --- | --- |
| Region / AZ | One AWS Region, two private subnets across two AZs for app runtime, S3/Bedrock managed outside subnets | Two or three AZs depending HA target; private app and data subnets separated |
| API runtime | Lambda or ECS/Fargate, no GPU | ECS/Fargate or EKS; Java/Spring Boot service can be built by Maven and deployed as a container |
| Vector DB | Bedrock-managed storage path | Aurora PostgreSQL pgvector for SQL metadata or OpenSearch Serverless for hybrid search |
| GPU | Not needed | Optional G5/A10G or managed SageMaker endpoint only for private low-latency inference |
| CI/CD | GitLab CI or GitHub Actions | GitLab CI with Maven build stage, container scan, Terraform plan/apply and RAG eval gate |
| Networking | Private app subnets, S3 endpoint, controlled Bedrock egress/endpoint where available | Add data subnets, OpenSearch/Aurora private endpoint, stricter security groups and network policies |

## Cost Drivers And Pricing References

Cost should be estimated from actual document pages, query volume, selected model and runtime hours. The current cost model should reference:

- Amazon Bedrock pricing for model tokens, Knowledge Bases, evaluation and Data Automation: https://aws.amazon.com/bedrock/pricing/
- OpenSearch Service pricing for OpenSearch Serverless OCU-hours and storage: https://aws.amazon.com/opensearch-service/pricing/
- Amazon Aurora pricing for ACU-hours/storage if MVP2 uses Aurora PostgreSQL pgvector: https://aws.amazon.com/rds/aurora/pricing/
- Amazon EC2 G5 instance-family details if private GPU inference is selected: https://aws.amazon.com/ec2/instance-types/g5/

## Success Metrics

| Metric | Target for PoC |
| --- | --- |
| Answer source coverage | Most accepted answers include citations |
| SME deflection | Track repeated questions answered without manual routing |
| Retrieval quality | Golden questions retrieve the expected source in top-k |
| Freshness | New or changed documents are searchable after the sync window |
| Latency | Interactive enough for internal workflow use |
| Cost visibility | Cost per 100 questions and cost per document sync are visible |
| Delivery readiness | CI/CD, runbook, rollback and ownership are clear enough for a second team pilot |

## Architecture Documents

Detailed diagrams and deployment notes:

```text
docs/ARCHITECTURE_AND_VPC.md
docs/AUTOMATION_CICD_RUNBOOK.md
```

## Relation To CCE / MLOps PoC

This PoC covers the corporate document knowledge-base scenario. The existing `cce-feature-platform` can also be extended with a vector DB for AI-assisted best-offer, customer segmentation and feature-context retrieval. See:

```text
../cce-feature-platform/docs/AI_VECTOR_DB_EXTENSION.md
```