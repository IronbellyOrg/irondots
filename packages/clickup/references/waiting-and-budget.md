# Waiting and budget
Inputs: finite scope/call limits, verification/reporting reserve and accumulated usage. Outputs: cumulative budget/checkpoint and next permitted observation. No implicit scheduler or timer.

Track discovery, reads, dispatch, polling, retries, verification and reporting in one persisted ledger across resumes. Quota/credit values unavailable from tools stay unknown. Before each call consume the relevant budget; do not spend the verification/reporting reserve on discretionary polling. Budget exhaustion leaves pending work with exact continuation, not success or no-change.

Prefer genuine completion events only when exposed. Otherwise choose a bounded delayed observation from provider guidance or measured completion times; identify uncalibrated delay as a proposed default. Do not continuously poll each action. Preserve next_observation_at, consumed totals and uncertain effects through interruption. Reconciliation reads do not resend. Count all overhead before claiming savings and compare equal coverage/outcomes. Local staging tests cannot establish latency or quota improvements.


## Brain route boundary
For whole-batch read/propose and normal-session recovery, load [Brain routing and continuity](brain-routing-continuity.md) before source fanout. Preserve actual local request/return state and cumulative reservations. Native mutation dispatcher restrictions do not disable the separate historically validated generic private AI transport; no new mutation authority follows.
