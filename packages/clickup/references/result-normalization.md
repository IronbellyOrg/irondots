# Result normalization checklist

Load when producing any v1 result, including preparation-only, blocked and error-ingestion outcomes. This specializes the existing shared contract without replacing its version or inventing evidence.

## Exact criterion keys

Each criterion record uses: `id`, `source_reported_claim`, `independently_observed_evidence`, `verdict`, `reason`. The evidence value identifies actual observations and links/IDs, or an explicit absence. Do not substitute `independent_evidence` or imply that reading a local historical report is fresh provider verification. Permitted verdicts: verified, partial, unresolved, contradicted, not_run. A local preparation check and the unmet external criterion remain distinct.

## Structured artifact records

Each `artifacts` member is an object, not a filename string:

- `artifact_id_or_path`: exact provider ID/link or actual local path, only in the local envelope.
- `source_kind`: provider_artifact, local_output, or retained_source.
- `provider`: actual provider name when observed; null with reason for local-only evidence.
- `observed_fields`: exact field/criterion values checked, or empty with a reason.
- `observed_at`: actual observation/readback time, or null with reason if not inspected.
- `revision_or_hash`: actual source revision or captured-byte hash; null with reason if unavailable.
- `operation_id`: linkage to the current local operation, or null with a reason if its original identity is unknown. A local ID never proves provider identity.
- `evidence_status`: local_readback, provider_readback, source_reported, or unverified, with scope/limitations.

Reference the ledger/provenance map if fuller details reside there, but preserve these essential receipt semantics in the normalized result. Do not invent metadata to make an object look complete. For unsent operations, correlation evidence stays null with an explicit reason. Claim verification must not be inferred from the existence of local result files.

## Final checks

Current result objective matches the ingested/resumed checkpoint. Contract version and parent/operation/attempt/revision linkage are preserved or explicitly unknown. Effect states, calls consumed, next permitted step and independent writeback state remain present. Parent remains integrated publisher. Local paths and debug evidence stay out of the recipient-facing packet. A missing required receipt yields partial/unresolved readiness, not a silently accepted transport result.
