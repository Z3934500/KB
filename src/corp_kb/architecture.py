from __future__ import annotations


def tier_catalog() -> list[dict[str, object]]:
    return [
        {
            "tier": "lightweight",
            "label": "Managed KB / Bedrock-style RAG",
            "implementation": "Local managed-KB adapter over files; production maps to S3 + Bedrock Knowledge Bases.",
            "best_for": "One department, a few thousand documents, fastest business validation.",
            "runtime": "Lambda or ECS/Fargate; no vector DB owned by the team; no GPU.",
        },
        {
            "tier": "medium",
            "label": "Explicit vector DB RAG",
            "implementation": "SQLite vector store locally; production maps to Aurora pgvector or OpenSearch Serverless.",
            "best_for": "Metadata filters, hybrid retrieval, index versioning and multi-department governance.",
            "runtime": "ECS/EKS retrieval API plus ingestion worker; no GPU by default.",
        },
        {
            "tier": "heavy",
            "label": "Private endpoint + governed vector RAG",
            "implementation": "Vector retrieval plus private endpoint orchestration and CPU/GPU policy switch.",
            "best_for": "Strict data policy, private inference, custom output behavior and high-control releases.",
            "runtime": "EKS/ECS/SageMaker endpoint; GPU only when latency or private throughput requires it.",
        },
    ]


def cicd_tool_tradeoffs() -> list[dict[str, str]]:
    return [
        {
            "tool": "GitHub Actions",
            "strength": "Fast setup, great for public/demo repos and simple container/test workflows.",
            "trade_off": "Enterprise network integration and approval controls may be weaker than internal platforms.",
            "best_fit": "MVP1 or personal website demo.",
        },
        {
            "tool": "GitLab CI",
            "strength": "Integrated repo, runners, registry, environments and approvals.",
            "trade_off": "Runner placement and network access need design in regulated environments.",
            "best_fit": "MVP2 platform delivery with Terraform, image build and RAG evaluation gates.",
        },
        {
            "tool": "Jenkins",
            "strength": "Very flexible and common in enterprises with complex legacy integrations.",
            "trade_off": "Controller/plugin lifecycle and security hardening require ownership.",
            "best_fit": "Existing enterprise Jenkins estate or hybrid on-prem/cloud delivery.",
        },
        {
            "tool": "Azure DevOps",
            "strength": "Strong boards/repos/pipelines integration and good Azure-native identity story.",
            "trade_off": "Less natural if source and registry standards are already GitHub/GitLab.",
            "best_fit": "Azure-first organizations or teams already using Azure Boards/Releases.",
        },
        {
            "tool": "Maven",
            "strength": "Standard Java build, dependency and test lifecycle.",
            "trade_off": "Not a CI/CD platform by itself; only needed when the service is Java/Spring Boot.",
            "best_fit": "Enterprise Java API/orchestrator option.",
        },
        {
            "tool": "Databricks Asset Bundles (DAB)",
            "strength": "Versioned Databricks jobs, notebooks, workflows and ML assets as deployable bundles.",
            "trade_off": "Best for Databricks workloads, not a replacement for app/IaC pipelines.",
            "best_fit": "MLOps or data-pipeline extension when KB ingestion/evaluation runs in Databricks.",
        },
        {
            "tool": "Ansible",
            "strength": "Simple VM configuration, systemd, Nginx and package installation automation.",
            "trade_off": "Imperative configuration can drift without inventory and idempotency discipline.",
            "best_fit": "Cloud VM bootstrap before moving to images or Kubernetes.",
        },
    ]


def runner_placement_tradeoffs() -> list[dict[str, str]]:
    return [
        {
            "placement": "Cloud-hosted managed runner",
            "pros": "Low setup effort and easy MVP start.",
            "cons": "May not reach private VPC resources without extra networking.",
            "recommendation": "Good for MVP1 tests, linting, container build and docs.",
        },
        {
            "placement": "Self-hosted runner on cloud VM",
            "pros": "Can reach VPC endpoints, private registries and test environments.",
            "cons": "Runner patching, secrets and isolation become your responsibility.",
            "recommendation": "Good for MVP2 when private vector DB or EKS access is required.",
        },
        {
            "placement": "Runner inside Kubernetes",
            "pros": "Ephemeral build pods, scalable capacity and close to deployment target.",
            "cons": "Needs RBAC, network policy, cache strategy and cluster isolation.",
            "recommendation": "Use a separate CI namespace or CI cluster, not the production app namespace.",
        },
        {
            "placement": "On-prem runner",
            "pros": "Can access internal document sources and legacy systems.",
            "cons": "VPN/proxy reliability and cloud deployment credentials must be controlled.",
            "recommendation": "Use when ingestion depends on private legacy content.",
        },
    ]



def sizing_thresholds() -> list[dict[str, object]]:
    return [
        {
            "tier": "lightweight",
            "decision": "S3 + Bedrock Knowledge Bases is enough",
            "documents": "1-3,000 approved documents",
            "pages": "up to about 10,000 pages",
            "chunks": "up to about 50,000 chunks",
            "departments": "1-3 departments",
            "queries_per_day": "up to about 1,000 internal questions/day",
            "weekly_document_changes": "up to about 500 changed documents/week",
            "duplicate_rate": "below 10% after basic cleanup",
            "metadata_complexity": "simple filters such as department, owner, effective_date and confidentiality",
            "move_up_when": "retrieval quality needs custom chunking, hybrid search, reranking or index version rollback",
        },
        {
            "tier": "medium",
            "decision": "Use an explicit vector DB",
            "documents": "3,000-30,000 documents",
            "pages": "10,000-150,000 pages",
            "chunks": "50,000-500,000 chunks",
            "departments": "3-20 departments",
            "queries_per_day": "1,000-20,000 questions/day",
            "weekly_document_changes": "500-5,000 changed documents/week",
            "duplicate_rate": "10-30%, or any corpus where canonical-source review is needed",
            "metadata_complexity": "multi-field filters, ACL-aware retrieval, hybrid search and reindex tracking",
            "move_up_when": "private inference, strict latency, very large corpus or complex governance is required",
        },
        {
            "tier": "heavy",
            "decision": "Use vector DB plus private endpoint/governed model path",
            "documents": "30,000+ documents",
            "pages": "150,000+ pages",
            "chunks": "500,000+ chunks",
            "departments": "20+ departments or cross-entity enterprise search",
            "queries_per_day": "20,000+ questions/day or strict p95 latency target",
            "weekly_document_changes": "5,000+ changed documents/week or near-real-time ingestion",
            "duplicate_rate": "30%+ or conflicting source-of-truth ownership",
            "metadata_complexity": "document-level ACL, region/legal rules, private inference and release gates",
            "move_up_when": "GPU/private model endpoint is justified by security, latency or throughput",
        },
    ]


def document_cleaning_rules() -> list[dict[str, str]]:
    return [
        {
            "step": "1. Inventory",
            "rule": "Capture document_id, title, owner, department, confidentiality, effective_date, version and source_uri before indexing.",
        },
        {
            "step": "2. Exact duplicate removal",
            "rule": "Hash normalized text; if content is identical, keep the newest approved source and mark others as aliases/superseded.",
        },
        {
            "step": "3. Near-duplicate review",
            "rule": "Use token similarity; if similarity is 0.82+ in this PoC, require owner review before indexing both documents.",
        },
        {
            "step": "4. Canonical source selection",
            "rule": "When the same policy appears in multiple files, prefer the document with active effective_date, approved owner and highest version.",
        },
        {
            "step": "5. Conflict handling",
            "rule": "If two active documents disagree, do not hide the conflict; return both citations and route to the owner for resolution.",
        },
        {
            "step": "6. Chunk hygiene",
            "rule": "Remove boilerplate headers/footers, split tables carefully, keep chunk size stable and retain source page/section metadata.",
        },
    ]

def deployment_architecture() -> dict[str, object]:
    return {
        "mvp1": {
            "network": "Two private app subnets across two AZs; S3 and Bedrock managed outside subnets.",
            "ingress": "CloudFront/API Gateway/ALB or Cloudflare Tunnel; EIP only for bastion-like VM demos.",
            "runtime": "Lambda or ECS/Fargate; no GPU; no self-managed vector DB.",
            "automation": "Terraform for cloud resources; Ansible only for VM bootstrap if a VM is used.",
        },
        "mvp2": {
            "network": "Public ingress subnets, private app subnets and private data subnets across two or three AZs.",
            "ingress": "ALB with WAF; optional EIP for NAT Gateway or fixed egress.",
            "runtime": "ECS/EKS API, ingestion worker, Aurora pgvector or OpenSearch Serverless.",
            "automation": "Terraform + GitLab/GitHub/Jenkins pipeline; Ansible for VM-only components.",
        },
        "heavy": {
            "network": "Private endpoint subnets, model endpoint security group and vector DB private access.",
            "ingress": "API Gateway/ALB routes to orchestrator; model endpoint stays private.",
            "runtime": "Private CPU/GPU endpoint on EKS/ECS/SageMaker plus vector retrieval.",
            "automation": "Terraform + image pipeline + model release gate + RAG evaluation gate.",
        },
    }


def gpu_tradeoffs() -> dict[str, object]:
    return {
        "default": "Do not add GPU for MVP1. Keep Bedrock or managed LLM on the critical path.",
        "use_gpu_when": [
            "Data policy requires private inference.",
            "Interactive latency is strict and CPU generation is too slow.",
            "Sustained request volume justifies always-on GPU cost.",
            "GPU-backed model serving is required for a private low-latency demo.",
            "A smaller self-hosted model is accepted by stakeholders after evaluation.",
        ],
        "avoid_gpu_when": [
            "The corpus quality and retrieval quality are not proven yet.",
            "Traffic is low or bursty.",
            "The team does not have model-serving operations ownership.",
            "A managed API meets security and latency requirements.",
        ],
        "cpu_fit": "Low-QPS fallback, batch summarization, reranking with small models and offline evaluation.",
        "gpu_fit": "Private low-latency generation, high-QPS assistant workflows and controlled model-serving demos.",
    }
