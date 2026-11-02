"""Offline synthetic authorization model. NOT a deployed gateway or AnythingLLM adapter."""
from dataclasses import dataclass, field
from threading import RLock
from typing import FrozenSet


class Denied(Exception):
    """Deliberately nonrevealing public error."""
    def __init__(self):
        super().__init__("Context unavailable")


@dataclass(frozen=True)
class Document:
    id: str
    pool: str
    text: str
    readers: FrozenSet[str]
    permitted_teams: FrozenSet[str]
    version: int = 1
    reviewed: bool = True
    modified_at: str = "2020-01-01T00:00:00Z"
    fetched_at: str = "2026-01-01T00:00:00Z"
    containers: tuple = ()
    source: str = "synthetic-drive"


@dataclass(frozen=True)
class Envelope:
    user: str
    team: str
    purpose: str
    dependencies: tuple
    epoch: int
    text: str


class Model:
    def __init__(self):
        self.lock = RLock()
        self.members = {}
        self.sessions = {}  # synthetic trusted issuer; not a real authentication system
        self.pools = {}  # pool -> {owner, grants}; owner tag never authorizes
        self.docs = {}
        self.archives = {}  # (source, path) -> {revision, approved_revision, kind}
        self.epoch = 0
        self.available = True
        self.cache = {}
        self.derived = {}
        self.context_sink = []  # synthetic pre-model boundary, not an LLM payload
        self.audit = []

    def changed(self):
        self.epoch += 1
        self.cache.clear()

    def user(self, name, teams):
        with self.lock:
            self.members[name] = frozenset(teams)
            self.changed()

    def issue(self, token, user, team, purpose="answer"):
        with self.lock:
            if team not in self.members.get(user, ()):
                raise Denied()
            self.sessions[token] = (user, team, purpose)

    def principal(self, token):
        if not self.available or token not in self.sessions:
            raise Denied()
        user, team, purpose = self.sessions[token]
        if team not in self.members.get(user, ()):
            raise Denied()
        return user, team, purpose

    def pool(self, name, owner, grants):
        with self.lock:
            self.pools[name] = {"owner": owner, "grants": frozenset(grants)}
            self.changed()

    def put(self, doc):
        with self.lock:
            self.docs[doc.id] = doc
            self.changed()

    def delete(self, doc_id):
        with self.lock:
            self.docs.pop(doc_id, None)
            self.changed()

    @staticmethod
    def valid_revision(revision):
        """Fixture contract only: positive integer, never bool or missing value."""
        return type(revision) is int and revision > 0

    def discover_container(self, source, path, revision):
        """Discovery only; exact Archive is approval-gated, OLD is quality-flagged."""
        with self.lock:
            leaf = path.rstrip('/').split('/')[-1].casefold()
            kind = 'archive' if leaf == 'archive' else 'quality_review'
            key = (source, path)
            previous = self.archives.get(key)
            approved = bool(self.valid_revision(revision) and previous
                            and previous.get('approved') is True
                            and previous['revision'] == revision
                            and previous['approved_revision'] == revision)
            approval = revision if approved else None
            self.archives[key] = dict(revision=revision, approved_revision=approval,
                                      approved=approved, kind=kind)
            self.changed()
            return dict(self.archives[key])

    def approve_archive(self, source, path, revision):
        """Trusted administrative test hook, never a user/model-facing tool."""
        with self.lock:
            item = self.archives.get((source, path))
            if (not item or not self.valid_revision(revision)
                    or not self.valid_revision(item['revision'])
                    or item['revision'] != revision or item['kind'] != 'archive'):
                raise Denied()
            item['approved_revision'] = revision
            item['approved'] = True
            self.changed()

    def revoke_archive(self, source, path):
        with self.lock:
            self.archives[(source, path)]['approved_revision'] = None
            self.archives[(source, path)]['approved'] = False
            self.changed()

    def _allowed(self, user, team, doc):
        if doc is None or not doc.reviewed:
            return False
        pool = self.pools.get(doc.pool)
        if not pool or team not in pool['grants']:
            return False
        if user not in doc.readers or team not in doc.permitted_teams:
            return False
        for path in doc.containers:
            # Unknown exact Archive ancestor also denies; discovery is not a bypass.
            if path.rstrip('/').split('/')[-1].casefold() == 'archive':
                item = self.archives.get((doc.source, path))
                if (not item or not self.valid_revision(item['revision'])
                        or item.get('approved') is not True
                        or not self.valid_revision(item['approved_revision'])
                        or item['approved_revision'] != item['revision']):
                    return False
        return True

    def discover_pools(self, token):
        with self.lock:
            _, team, _ = self.principal(token)
            return sorted(k for k, v in self.pools.items() if team in v['grants'])

    def _envelope(self, token, ids):
        user, team, purpose = self.principal(token)
        ids = tuple(sorted(set(ids)))
        if not ids:
            raise Denied()
        docs = [self.docs.get(k) for k in ids]
        if not all(self._allowed(user, team, d) for d in docs):
            self.audit.append((user, team, 'deny'))
            raise Denied()
        deps = tuple((d.id, d.version) for d in docs)
        return Envelope(user, team, purpose, deps, self.epoch, '\n'.join(d.text for d in docs))

    def prepare(self, token, ids):
        with self.lock:
            return self._envelope(token, ids)

    def deliver(self, token, envelope):
        with self.lock:
            principal = self.principal(token)
            if principal != (envelope.user, envelope.team, envelope.purpose):
                raise Denied()
            current = self._envelope(token, [k for k, _ in envelope.dependencies])
            if current.dependencies != envelope.dependencies or current.epoch != envelope.epoch or current.text != envelope.text:
                raise Denied()
            self.context_sink.append((principal, current.dependencies, current.text))
            self.audit.append((principal[0], principal[1], 'allow'))
            return current.text

    def query(self, token, ids):
        with self.lock:
            principal = self.principal(token)
            key = (principal, tuple(sorted(set(ids))), self.epoch)
            envelope = self.cache.get(key)
            if envelope is None:
                envelope = self._envelope(token, ids)
                self.cache[key] = envelope
            return self.deliver(token, envelope)

    def derive(self, token, name, ids):
        """Synthetic concatenation only; no summarizing model or inference detector."""
        with self.lock:
            envelope = self._envelope(token, ids)
            self.derived[name] = envelope

    def read_derived(self, token, name):
        with self.lock:
            if name not in self.derived:
                raise Denied()
            envelope = self.derived[name]
            # Can share only if every source remains authorized and unchanged;
            # no dependency-free derived text may enter context.
            current = self._envelope(token, [k for k, _ in envelope.dependencies])
            if current.dependencies != envelope.dependencies or current.epoch != envelope.epoch or current.text != envelope.text:
                raise Denied()
            return self.deliver(token, current)
