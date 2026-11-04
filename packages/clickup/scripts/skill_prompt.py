"""Local prompt formatting only. No provider calls or execution authority."""
import re


def render(body, *, command=None, command_evidence=None, resuming=False):
    """Format a NEW authorized named-skill request before its packet is frozen.

    The coordinator must verify command_evidence and authority. This helper cannot
    prove either. For pending/sent work, recover the original packet instead.
    """
    if resuming:
        raise ValueError('Resume the existing operation and retained packet; do not render a new invocation')
    if not isinstance(body, str) or not body.strip():
        raise ValueError('Nonempty recipient packet required')
    if command is None:
        if command_evidence is not None:
            raise ValueError('Command evidence without a selected command')
        return body
    if not isinstance(command, str) or not re.fullmatch(r'/if:[a-z][a-z0-9-]*', command):
        raise ValueError('Exact verified /if: command required; no placeholders or prose')
    if not isinstance(command_evidence, str) or not command_evidence.strip():
        raise ValueError('Record actual command verification evidence before formatting')
    if body.lstrip().startswith('/if:'):
        raise ValueError('Packet already starts with an invocation; review rather than duplicate or replace it')
    return command + '\n\n' + body
