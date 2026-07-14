import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "supabase" / "migrations"


def _migration_sql() -> str:
    files = sorted(MIGRATIONS.glob("*_production_foundation.sql"))
    assert len(files) == 1
    return files[0].read_text(encoding="utf-8").lower()


def test_every_exposed_application_table_enables_rls() -> None:
    sql = _migration_sql()
    tables = re.findall(r"create table public\.([a-z_]+)", sql)
    assert tables
    for table in tables:
        assert f"alter table public.{table} enable row level security" in sql


def test_policies_scope_authenticated_users_to_membership() -> None:
    sql = _migration_sql()
    assert "to authenticated" in sql
    assert "public.is_org_member" in sql
    assert "public.has_org_role" in sql
    assert "user_metadata" not in sql
    assert "auth.role()" not in sql


def test_privileged_schema_and_views_do_not_bypass_rls() -> None:
    sql = _migration_sql()
    assert "revoke all on schema private from public, anon, authenticated" in sql
    assert "security_invoker = true" in sql
    assert "security definer" not in sql


def test_storage_is_private_and_update_has_select_update_policies() -> None:
    sql = _migration_sql()
    assert "values ('case-documents', 'case-documents', false" in sql
    for operation in ("select", "insert", "update", "delete"):
        assert f"case_documents_{operation}" in sql
    assert "join public.cases case_record" in sql
    assert "case_record.id::text = (storage.foldername(name))[2]" in sql


def test_queue_is_durable_and_not_exposed_through_public_helpers() -> None:
    sql = _migration_sql()
    assert "create extension if not exists pgmq" in sql
    assert "pgmq.create('analysis_jobs')" in sql
    assert "pgmq_public" not in sql
