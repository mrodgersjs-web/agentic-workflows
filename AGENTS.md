# agentic-workflows — agent guide

Deployment definitions and run proofs for six self-hosted agentic designers.

## Constraints

- Nothing in this repo may contain a literal secret, tailnet IP, or keychain
  value: `$RIG_HOST` stands for the fleet host, `${VAR}` stands for every key.
  Grep before every commit: `grep -rE "ghp_|sk-[A-Za-z0-9]{20,}|100\\.[0-9]+\\."`.
- `results/` files are evidence: append new runs, never rewrite old ones.
- Deploy files mirror what actually runs on the farm; if you change one, the
  farm is the source of truth, re-export rather than hand-edit.
