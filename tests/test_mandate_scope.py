from __future__ import annotations

from verace_runtime.ledger.db import apply_schema, connect
from verace_runtime.ledger.repository import LedgerRepository
from verace_runtime.time import utc_now_iso


def test_active_mandate_is_scoped_by_principal_and_contour(tmp_path):
    with connect(tmp_path / "runtime.sqlite3") as conn:
        apply_schema(conn)
        repo = LedgerRepository(conn)
        now = utc_now_iso()
        seed = repo.seed_founder(now)
        marina_id = repo.ensure_person("marina", "Marina", now)
        mandate_id = repo.ensure_mandate(marina_id, seed["contour_id"], now)

        oleg = repo.active_mandate("oleg", "verace_project")
        marina = repo.active_mandate("marina", "verace_project")

        assert oleg["id"] == seed["mandate_id"]
        assert marina["id"] == mandate_id
        assert oleg["id"] != marina["id"]
