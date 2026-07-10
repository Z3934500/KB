title: Private Inference And GPU Decision
department: ai-platform
owner: ml-platform
confidentiality: restricted
effective_date: 2026-01-01

# Private Inference And GPU Decision

The heavy tier keeps model serving behind a private endpoint. It combines vector retrieval with a CPU or GPU model endpoint and a release gate for prompt, model and retrieval evaluation.

GPU is not required for MVP1. GPU should be considered only when private inference is mandatory, interactive latency is strict, or sustained request volume justifies the always-on cost. Candidate shapes include managed model endpoints or GPU-backed Kubernetes node groups.

CPU inference is acceptable for low-QPS fallback, batch summarization, offline evaluation and small reranking models. If CPU generation is too slow for an interactive journey, route the critical path to a managed model API or a GPU endpoint.

The fallback path should return a deterministic answer from retrieval or rules when the private model endpoint is slow or unavailable.
