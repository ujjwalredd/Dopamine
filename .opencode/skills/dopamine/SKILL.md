---
name: dopamine
description: Solve coding, debugging, research, analysis, planning, and other agentic work with the smallest verified solution, adaptive effort, minimal tool and token cost, and evidence-backed reporting. Use when correctness and efficiency both matter, or when the user says "dopamine", requests fewer tokens, lower cost, less code, faster execution, or asks the agent to iterate until verified. Skip casual conversation, pure creative writing, translation, and tool-free factual answers.
---

# Dopamine

Maximize verified progress per unit of code, time, tokens, and cost. Deliver the smallest complete result and stop.

## Non-negotiables

- Define observable completion conditions before substantial work.
- Prefer repository evidence, authoritative sources, schemas, compilers, and tests over confidence.
- Preserve explicit requirements, security controls, trust-boundary validation, accessibility basics, and error handling that prevents data loss.
- Never repeat an unchanged failed action. Change the hypothesis, input, tool, or scope.
- Never claim verification that did not run or pass.

## Solution ladder

Stop at the first rung that fully satisfies the request:

1. Existing behavior or deletion
2. Configuration
3. Existing project component, helper, pattern, or interface
4. Native platform or standard-library primitive
5. Already-installed dependency
6. Smallest custom implementation

Inspect only enough code to find the relevant flow and one compatible pattern. Do not add a dependency, abstraction, fallback, compatibility layer, generalized API, or refactor without demonstrated need. If two solutions work, choose fewer changed source lines; if tied, choose fewer files and less state.

## Delivery boundary

Derive the output boundary literally from the named artifact:

- **Component:** create one standalone reusable component. Unless the request names a destination, do not mount it, modify a route, bind application data, add global listeners, or invent entries. Expose neutral props and callbacks.
- **Underspecified interaction:** implement the named primary interaction and accessible native fallback. Do not add secondary keyboard navigation, global shortcuts, active-selection state, hover/drag presentation state, empty-state decoration, or responsive variants unless named.
- **Native form control:** transparently wrap the project's existing input and set its native `type`. Forward existing props. Do not add companion inputs, icons, formatting, validation policy, or duplicate state unless requested.
- **Endpoint:** implement the route and smallest necessary backend schema/query change. Do not modify generated clients or UI unless requested.
- **Capability:** implement the lowest existing layer that makes it callable. Cross UI, API, persistence, generated-code, or global-application boundaries only when explicit behavior requires it.
- **Bug fix:** repair the shared root cause in place after checking its callers. Do not create a framework around the fix.

A short feature noun does not imply animations, previews, persistence, shortcuts, alternate modes, elaborate styling, or product-specific policy. Mention possible extensions instead of implementing them.

Before editing, record the chosen ladder rung and delivery boundary internally. After editing, remove every source block and changed file that cannot be mapped to an explicit requirement, required project interface, or correctness/safety condition.

## Effort route

- **Direct:** canonical path and low risk. One targeted inspection, one edit, one decisive check.
- **Probe:** uncertain cause. Keep at most three live hypotheses and run the smallest check that separates them.
- **Explore:** multiple consequential solutions remain or two distinct probes failed. Compare at most three candidates and deepen only the best.
- **Guarded:** security, money, privacy, destructive operations, migrations, authentication, or public compatibility. Use the normal route plus one compact adversarial boundary check.

Escalate only after contradiction, failed verification, or a newly discovered requirement. Combine compatible reads and checks. Do not reread unchanged files or rerun a passing check.

## Correctness contract

For multiple requirements, preserve every qualifier and derive one assertion per independent condition. Run the assertions together against the produced artifact.

For parsers, transformations, graphs, schedulers, caches, and state machines, validate applicable full-output invariants such as format, completeness, domains, ordering, uniqueness, reachability, conservation, referential integrity, and boundaries. Use a tiny obvious reference model for complex deterministic logic when practical.

For bulk transformations, derive the complete dimension set from input or schema, represent rules as data, produce the full artifact early, scan every output, group failures by rule, and never silently skip unresolved dimensions. Do not fabricate labels, conversions, or values.

For classification, assign a known label only from explicit lexical, structural, or contextual evidence tied to the allowed taxonomy. Derive confidence and rationale from the same evidence; use the specified unknown label when support is insufficient.

## Verification

Choose the smallest decisive check from [references/verification.md](references/verification.md). A model review is supporting evidence, never proof when an executable check exists.

After failure, repair only the evidenced defect and rerun the narrow check before any broader suite. Never weaken or bypass a valid verifier. Stop when completion conditions pass; do not add speculative improvements.

## Reporting

Report the outcome, decisive verification, and any limitation. Keep routine completion to three short lines. Say `not verified` when verification was unavailable.
