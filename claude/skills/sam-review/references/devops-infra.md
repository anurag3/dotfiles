# DevOps / Infra Traps

Domain-specific bullets to layer onto the core Pain Points / Architectural
checklist when the diff touches Terraform, Helm, Kubernetes manifests, CI/CD
pipeline config, or cloud provisioning.

## Pain Points

- **Terraform state traps** *(🔴 Blocker)*: no remote state locking (concurrent applies can corrupt state), state backend unencrypted, module/provider versions unpinned (`~>` ranges or no version at all) making applies non-reproducible
- **Terraform config traps** *(🟡 Major)*: hardcoded account IDs, ARNs, or environment values instead of variables, no `plan` review step before `apply` in CI, secrets committed in `.tfvars` or default values instead of a secrets manager reference
- **Helm/K8s traps** *(🟡 Major)*: `latest` or floating image tags (non-reproducible, unrollback-able deploys), no resource `requests`/`limits` (noisy-neighbor risk or OOM-kill), missing `livenessProbe`/`readinessProbe` on a service expected to self-heal
- **CI/CD traps** *(🟡 Major)*: pipeline change that skips a required check (tests, lint, security scan) to unblock a merge, deploy step with no rollback path if the new version fails health checks

## Architectural Issues

- **Blast radius** *(🔴 Blocker if prod-wide)*: change to a shared module, shared state file, or cluster-wide policy with no scoping to test the impact before it hits every consumer
- **Stateful resource protection** *(🔴 Blocker)*: `prevent_destroy` / deletion protection missing on databases, persistent volumes, or buckets holding data that can't be regenerated — a `terraform destroy`/`apply` typo becomes unrecoverable
- **IAM/permission scope** *(🟡 Major)*: wildcard actions/resources (`*:*`, `Resource: "*"`) granted where a scoped policy would do, service account or role reused across environments instead of least-privilege per-env
- **Availability during change** *(🟡 Major)*: rolling update strategy or `PodDisruptionBudget` missing on a service that can't tolerate simultaneous replica loss, no health-check gate between deploy stages
- **Config drift** *(🟡 Major)*: values hardcoded per-environment in the chart/module instead of templated via `values.yaml`/tfvars, making environments silently diverge over time
- **Network exposure** *(🔴 Blocker if public)*: security group, ingress, or network policy change that widens access (0.0.0.0/0, public ALB/LB) without a stated reason
