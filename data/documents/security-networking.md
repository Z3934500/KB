title: Security And Networking Baseline
department: platform
owner: cloud-security
confidentiality: internal
effective_date: 2026-01-01

# Security And Networking Baseline

The preferred VPC design separates public ingress subnets, private application subnets and private data subnets across at least two availability zones. Public subnets host internet-facing load balancers or NAT gateways. Application services run without public IP addresses.

The lightweight tier does not need a GPU and does not own a vector database. It should use private app subnets, a managed knowledge base, server-side secrets and request logging.

The medium tier can use Aurora PostgreSQL pgvector or OpenSearch Serverless. The vector database should stay private and metadata filters must be enforced by the API, not only by the user interface.

Use an Elastic IP only when a fixed public egress or VM demo endpoint is required. Prefer load balancers, private endpoints and DNS records for production access patterns.
