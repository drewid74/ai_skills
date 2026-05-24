"""Backend conformance + claim atomicity tests.

Run:
    pytest mcp-server-dev/postgres-control-plane/tests/

Postgres tests are skipped unless DATABASE_URL is set.
"""
from __future__ import annotations

import os
import threading
import tempfile

import pytest

from postgres_control_plane import (
    MemoryBackend,
    PostgresBackend,
    SQLiteBackend,
    Task,
    TaskQueue,
)


def make_queue_memory():
    return TaskQueue(backend=MemoryBackend())


def make_queue_sqlite():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    return TaskQueue(backend=SQLiteBackend(tmp.name))


BACKENDS = [make_queue_memory, make_queue_sqlite]

if os.environ.get("DATABASE_URL"):
    def make_queue_postgres():
        return TaskQueue(backend=PostgresBackend(os.environ["DATABASE_URL"]))
    BACKENDS.append(make_queue_postgres)


@pytest.fixture(params=BACKENDS, ids=lambda f: f.__name__)
def queue(request):
    return request.param()


def test_add_and_get(queue):
    queue.add(Task(id="t1", job_name="demo"))
    t = queue.get("t1")
    assert t and t.id == "t1" and t.status == "pending"


def test_list_pending(queue):
    queue.add(Task(id="a", job_name="demo"))
    queue.add(Task(id="b", job_name="demo"))
    queue.add(Task(id="c", job_name="other"))
    pending = queue.list_pending("demo")
    assert {t.id for t in pending} == {"a", "b"}


def test_claim_sets_metadata(queue):
    queue.add(Task(id="x", job_name="demo"))
    claimed = queue.claim("x", "worker-1")
    assert claimed.status == "claimed"
    assert claimed.claimed_by == "worker-1"
    assert claimed.claimed_at is not None
    assert claimed.updated_at is not None


def test_claim_twice_fails(queue):
    queue.add(Task(id="y", job_name="demo"))
    queue.claim("y", "w1")
    with pytest.raises(ValueError):
        queue.claim("y", "w2")


def test_claim_missing_fails(queue):
    with pytest.raises(KeyError):
        queue.claim("nope", "w1")


def test_status_transition_valid(queue):
    queue.add(Task(id="s1", job_name="demo"))
    queue.claim("s1", "w1")
    done = queue.update_status("s1", "completed", reason="ok")
    assert done.status == "completed"
    assert done.reason == "ok"


def test_status_transition_invalid(queue):
    queue.add(Task(id="s2", job_name="demo"))
    with pytest.raises(ValueError):
        queue.update_status("s2", "completed")  # pending -> completed not allowed


def test_heartbeat_updates_claimed_at(queue):
    queue.add(Task(id="h1", job_name="demo"))
    claimed = queue.claim("h1", "w1")
    first_ts = claimed.claimed_at
    import time; time.sleep(0.01)
    refreshed = queue.heartbeat("h1", "w1")
    assert refreshed.claimed_at != first_ts


def test_heartbeat_wrong_worker(queue):
    queue.add(Task(id="h2", job_name="demo"))
    queue.claim("h2", "w1")
    with pytest.raises(ValueError):
        queue.heartbeat("h2", "w2")


def test_stats(queue):
    queue.add(Task(id="g1", job_name="g"))
    queue.add(Task(id="g2", job_name="g"))
    queue.claim("g1", "w1")
    stats = queue.get_stats("g")
    assert stats["pending"] == 1
    assert stats["claimed"] == 1


def test_claim_atomicity(queue):
    """Race 10 workers against 1 task. Exactly one must win."""
    queue.add(Task(id="race", job_name="demo"))
    winners: list[str] = []
    lock = threading.Lock()

    def worker(wid: str):
        try:
            queue.claim("race", wid)
            with lock:
                winners.append(wid)
        except ValueError:
            pass

    threads = [threading.Thread(target=worker, args=(f"w{i}",)) for i in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()

    assert len(winners) == 1, f"Expected 1 winner, got {len(winners)}: {winners}"
