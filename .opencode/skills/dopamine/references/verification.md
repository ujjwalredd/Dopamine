# Verification selection

Choose the smallest decisive check first, then broaden in proportion to risk.

| Task | Primary evidence | Broader evidence when warranted |
|---|---|---|
| Bug fix | Reproduction fails before and passes after | Related regression suite |
| Feature | Acceptance test for requested behavior | Existing project test suite |
| Refactor | Existing behavior tests remain unchanged | Typecheck, lint, build |
| Security | Exploit or abuse case is rejected | Authorization, input-boundary, secret, and dependency checks |
| Data or migration | Dry run and invariant checks | Backup/rollback rehearsal and representative sample |
| Research | Primary or authoritative sources support each unstable claim | Independent source or primary study replication |
| Analysis | Reproducible calculation and stated inputs | Sensitivity or boundary checks |
| Plan or design | Requirements and constraints map to the proposal | Failure-mode and reversibility review |

## Evidence hierarchy

Prefer evidence in this order:

1. Deterministic executable verifier or direct observation
2. Authoritative specification or primary source
3. Independent implementation or measurement
4. Static analysis or structured review
5. Model judgment

Do not substitute a lower level when a practical higher-level check exists.

## Aspect checks

Cover these aspects in one compact verifier when practical. Split them only when the risks require different setups or evidence:

- **Correctness:** Does the result meet each explicit acceptance condition?
- **Regression:** What existing behavior could this change break?
- **Security:** Does untrusted input cross a boundary safely? Are authorization and secrets preserved?
- **Efficiency:** Did the solution add avoidable code, dependencies, calls, or context?
- **Evidence:** Does every completion claim follow from an observed result?

For low-risk direct tasks, one deterministic correctness check is sufficient. After a compact check passes, do not rerun its individual assertions separately. Do not create a review ceremony that costs more than the work.
