title: CI CD Tooling Decision
department: platform
owner: devops
confidentiality: internal
effective_date: 2026-01-01

# CI CD Tooling Decision

GitHub Actions is the fastest path for a demo repository and simple tests. GitLab CI is a stronger fit for enterprise platform delivery when approvals, private runners, environments and a container registry are needed.

Jenkins is useful when an organization already has complex plugins and legacy integration. The trade-off is controller maintenance, plugin lifecycle and security hardening.

Azure DevOps fits Azure-first teams that already use Azure Boards, Repos and Pipelines. Maven is not a CI platform; it is the Java build lifecycle and should be used only when the API or orchestrator is implemented as a Java or Spring Boot service.

Databricks Asset Bundles are useful for deploying Databricks jobs, workflows and ML assets. They complement application CI/CD and infrastructure pipelines rather than replacing them.

Runner placement matters. Managed cloud runners are easy for MVP1. Self-hosted cloud runners can access private VPC resources. Kubernetes runners should run in a separate CI namespace or CI cluster, not in the production application namespace.
