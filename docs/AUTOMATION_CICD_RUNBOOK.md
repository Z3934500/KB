# Automation, CI/CD And Deployment Runbook

This runbook explains how the corporate knowledge-base PoC should be automated and how Jenkins or GitLab can fit into the deployment model.

## What Gets Automated

| Automation | Trigger | Output |
| --- | --- | --- |
| Document intake | S3 upload, scheduled scan or approved merge | Parsed documents and index sync |
| Knowledge-base sync | S3 event, manual release or nightly job | New chunk/index version |
| RAG evaluation | Pull request, prompt change, index change | Pass/fail quality gate |
| Infrastructure deployment | Terraform change | VPC, IAM, buckets, endpoints, API runtime |
| Application deployment | API code or prompt template change | Versioned Lambda/ECS/EKS deployment |
| Model release | Fine-tuned model candidate | Evaluation record and promoted model alias |
| Observability | Every request | Latency, cost, retrieved sources, feedback |

The business message is simple: automation turns an internal document library into an operated knowledge product instead of another manually maintained folder.

## Jenkins vs GitLab

| Choice | Strength | Trade-off | Best use |
| --- | --- | --- | --- |
| Jenkins | Flexible, familiar in many enterprises, strong plugin ecosystem | Controller and plugin lifecycle need care | Existing Jenkins estate or complex enterprise integrations |
| GitLab CI | Integrated repo, CI, registry and approvals | Best when source code already lives in GitLab | Cleaner end-to-end platform if GitLab is the standard |
| GitHub Actions | Simple for this repo shape | May not match enterprise standard | Lightweight personal or demo pipeline |

Either Jenkins or GitLab is fine. The important design point is separating CI control from production runtime and using short-lived credentials.

## CI/CD Tool Trade-Off Matrix

| Tool | Role | Strength | Trade-off | Best fit in this PoC |
| --- | --- | --- | --- | --- |
| GitHub Actions | CI/CD platform | Fast setup, good for repo demos and simple Docker/test workflows | Private VPC access needs self-hosted runners or extra networking | MVP1 and personal demo delivery |
| GitLab CI | CI/CD platform | Integrated repo, runners, registry, environments and approvals | Runner placement and secrets management need design | MVP2 platform delivery and private runner flow |
| Jenkins | CI/CD orchestrator | Enterprise plugin ecosystem and legacy integration | Controller/plugin lifecycle and security hardening are operational overhead | Existing enterprise Jenkins estate |
| Maven | Java build tool | Standard Java/Spring Boot test/package lifecycle | Not a deployment platform by itself | Use only if the API/orchestrator is Java |
| Azure DevOps | CI/CD + planning platform | Strong Azure identity, boards, repos and pipeline integration | Less natural if source and registry are standardized elsewhere | Azure-first enterprise delivery |
| Databricks Asset Bundles (DAB) | Databricks deployment packaging | Versioned jobs, workflows, notebooks and ML assets | Complements app/IaC CI, does not replace it | Data/MLOps extension or KB evaluation jobs in Databricks |
| Ansible | Configuration automation | Simple VM bootstrap for Nginx, systemd and packages | Can drift if inventory and idempotency are weak | VM-based demo, hybrid/on-prem runner setup |

Recommended split:

```text
Terraform = VPC, subnets, security groups, managed services, IAM
Ansible   = VM bootstrap when a VM exists
Maven     = Java build only
DAB       = Databricks jobs/workflows only
CI/CD     = GitHub Actions, GitLab CI, Jenkins or Azure DevOps orchestrates the gates
```
## Runner Placement Trade-Off

| Placement | Pros | Cons | Recommendation |
| --- | --- | --- | --- |
| Local VM or on-prem runner | Easy access to internal repos, VPN and legacy document sources | Can become a snowflake server; harder to scale and isolate | Good when source documents remain inside the corporate network |
| Runner inside EKS | Ephemeral build pods, scalable, close to Kubernetes deployment target | Cluster outage can block deployments; requires RBAC and network policy design | Good for mature platform teams; prefer separate CI namespace or separate CI cluster |
| Separate CI cluster | Keeps build workload away from production | More infrastructure to manage | Best production pattern for regulated workloads |
| Managed GitLab/Jenkins/Azure DevOps controller with ephemeral agents | Stable control plane plus disposable workers | Requires setup discipline | Recommended target model for MVP2 and beyond |

Avoid running the Jenkins controller inside the production application namespace. If Kubernetes is used, prefer ephemeral agents in a controlled namespace or a separate CI cluster.

## Deployment Pattern By Tier

| Tier | Runtime | CI/CD shape |
| --- | --- | --- |
| Lightweight Bedrock KB | Lambda or ECS/Fargate, no cluster required | Terraform deploys S3/IAM/API; pipeline packages API; KB sync job runs after document release |
| Medium vector DB | ECS/Fargate or EKS | Pipeline builds ingestion/retrieval images, applies DB migrations, deploys API, triggers reindex |
| Fine-tuning | Bedrock or SageMaker managed training/endpoint | Pipeline validates training data, starts tuning job, runs eval, promotes model alias |
| CPU private inference | ECS/EKS service or SageMaker endpoint | Pipeline builds model image, runs latency test, canary deploys endpoint |

## GitLab + Maven Delivery Shape

Maven is only required when the API/orchestrator is implemented as Java/Spring Boot. If the PoC uses Python/FastAPI or Lambda-only code, replace Maven with the relevant Python test/package stage. Keeping Maven in the delivery note is useful because many enterprise teams standardize Java service delivery.

```text
GitLab merge request
  -> validate document metadata
  -> run unit tests
  -> Maven package for Java service, if used
  -> build container image
  -> scan image and dependencies
  -> terraform plan
  -> deploy dev
  -> sync Bedrock KB or reindex vector DB
  -> run RAG golden-question evaluation
  -> approval
  -> deploy prod
```

Example GitLab stages:

```text
stages:
  - validate
  - test
  - package
  - image
  - infra-plan
  - deploy-dev
  - rag-eval
  - approval
  - deploy-prod
```

Maven stage example:

```text
mvn -B clean test package
```

## Example Pipeline Stages

```text
1. lint-doc-metadata
2. unit-test-api
3. maven-package-if-java-service
4. build-container-or-lambda-package
5. terraform-plan
6. security-scan
7. deploy-dev
8. sync-knowledge-base-or-reindex-vector-db
9. run-rag-evaluation
10. approval-gate
11. deploy-prod
12. smoke-test-and-dashboard-check
```

## Lightweight Tier Runbook

1. Upload approved department documents to the S3 prefix.
2. Trigger Bedrock Knowledge Base sync.
3. Run golden questions against `RetrieveAndGenerate`.
4. Check citations and answer quality.
5. Promote the app or prompt version.
6. Monitor latency, errors and feedback.

```text
Document release
  -> S3 upload
  -> Bedrock KB sync
  -> RAG eval
  -> API deployment
  -> user feedback loop
```

## Medium Vector DB Runbook

1. Store raw documents in S3.
2. Parse and normalize content.
3. Split into chunks with stable `document_id`, `chunk_id`, `version` and metadata.
4. Generate embeddings.
5. Upsert chunks and vectors into the vector DB.
6. Run top-k retrieval tests.
7. Deploy retrieval API.
8. Run end-to-end answer tests.

Vector index release should be versioned separately from application release. If a new index performs poorly, the API should be able to route back to the previous index version.

## Fine-Tuning Runbook

1. Curate approved Q/A, classification or extraction examples.
2. Redact sensitive data and tag dataset version.
3. Run training job through Bedrock or SageMaker.
4. Evaluate against golden questions and safety checks.
5. Compare cost, latency and accuracy with baseline RAG.
6. Promote only if the tuned model improves a measured behavior.

Fine-tuning is a release-management problem, not only a data-science task.

## Minimum Repository Layout

```text
corporate-knowledge-base-poc/
  README.md
  docs/
    ARCHITECTURE_AND_VPC.md
    AUTOMATION_CICD_RUNBOOK.md
  infra/
    terraform/
  app/
    api/
  eval/
    golden_questions.csv
```

This repository currently documents the PoC architecture. Implementation folders can be added when the target cloud account, authentication method and document source are fixed.
