# Voice waiting

Default target: about 30 seconds since either party's last actual voice activity, only while relevant background work is pending. Check at available model opportunities, such as a worker result or new turn. This instruction is not a persistent timer and cannot guarantee a 30-second wake.

Before speaking, establish pending work, active call, safe speaking opportunity, no current user speech or assistant playback, no quiet/hold instruction and no newer completion/blocker. Transcript silence is not proof of audio silence. If activity state is unknown, wait for a safe opportunity rather than assert silence. Do not infer audio delivery from connection or queued text. Keep the acknowledgment brief and consolidate worker updates. Do not interrupt a sentence to announce a background finding. Completed results take precedence over “I'm still working”; failed/stalled work needs truthful status, not an active-work claim.

Quiet mode suppresses nonessential waiting updates for this session, not required safety questions or requested result delivery. No reminders when no work is pending. Reconnect must not flush old queued notifications into a new call.

A separately authorized future deterministic adapter would require verified call lifecycle, speech and playback start/end events, monotonic clock, pending-work state, quiet state, wake/delivery mechanism and actual playback acknowledgment. Arm only while pending work and both parties idle; reset on either party's activity; disarm on completion, call end, quiet mode or missing telemetry; recheck immediately before emission and allow one in-flight notification per call epoch. None of these capabilities is established by this Markdown. Do not create cron jobs, polls, hooks or credentials to simulate them.

When independent work is genuinely underway and another user-attention item is ready, move to that next prioritized item one at a time instead of filling time with repeated progress acknowledgments. Preserve the outstanding operation and return important findings at a safe opportunity. Do not start unrelated or unauthorized actions to avoid a pause, and do not call stalled/historical work running.
