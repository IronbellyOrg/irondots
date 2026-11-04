# Provenance and intentional adaptations

Primary reference: IronbellyOrg/IronClaude `sc:adversarial` command and its mandatory `sc:adversarial-protocol`, inspected at commit [af74de76f48cf380878865fefa644662af0ca8f1](https://github.com/IronbellyOrg/IronClaude/commit/af74de76f48cf380878865fefa644662af0ca8f1).

Inspected paths: `src/superclaude/commands/adversarial.md`; `src/superclaude/skills/sc-adversarial-protocol/SKILL.md`; its `refs/artifact-templates.md` and `refs/scoring-protocol.md`; `src/superclaude/agents/debate-orchestrator.md`; `src/superclaude/agents/merge-executor.md`; root `LICENSE`. Upstream MIT notice is retained in NOTICE. No additional open-source license grant for new material is asserted here; distribution/release rights remain a maintainer decision.

Retained: steelmanning, explicit concessions, source-linked differences/shared assumptions, independent invariant/sufficiency probe, role separation, traceable draft synthesis and interrupted-work recovery.

Adapted: native internal delegation instead of Claude tools/models; bounded rounds; critical evidence gates instead of universal 50/50 scores; unanimity as descriptive agreement rather than confidence; metadata-only masking; explicit requested draft synthesis instead of automatic merge; typed failure/gap results; actual reporting-resource discovery. Generic DAG execution and source command grammar are not supplied.

The source's 25/30 rubric drift, conflict-count/list drift and contradictory pipeline root-input handling are not copied. The scoring discrepancy is tracked in [IronClaude issue 376](https://github.com/IronbellyOrg/IronClaude/issues/376). Source-reported accuracy, error-reduction, deterministic semantic scoring and complete debiasing claims were not adopted.

This package contains reusable instructions and offline structural checks. Installation, resource loading, independent role execution, content acceptance and external publication require their own evidence. Private requests, profiles, source corpora, ledgers and runtime receipts do not belong in this package.
