-- Keep worker queues unreachable from Data API roles even if extension defaults
-- change. The API/worker connects with a privileged server-only database role.
revoke all on schema pgmq from public, anon, authenticated;
revoke all on all tables in schema pgmq from public, anon, authenticated;
revoke all on all sequences in schema pgmq from public, anon, authenticated;
revoke execute on all functions in schema pgmq from public, anon, authenticated;

alter default privileges in schema pgmq
  revoke all on tables from public, anon, authenticated;
alter default privileges in schema pgmq
  revoke all on sequences from public, anon, authenticated;
alter default privileges in schema pgmq
  revoke execute on functions from public, anon, authenticated;

-- Supabase projects created before the May 2026 Data API grant change can
-- retain broad anon grants. Make the intended deny-by-default posture
-- migration-defined so upgrades and local resets behave identically.
revoke all on table
  public.organizations,
  public.organization_memberships,
  public.projects,
  public.cases,
  public.documents,
  public.findings,
  public.rfis,
  public.analysis_jobs,
  public.audit_events,
  public.webhook_subscriptions,
  public.webhook_deliveries,
  public.case_overview
from anon;

-- Index every foreign-key access path that is not already covered by the
-- leading columns of an existing index. This keeps tenant cascades, joins,
-- assignment lookups, and deletion work bounded as organizations grow.
create index organizations_created_by_idx on public.organizations (created_by);
create index projects_created_by_idx on public.projects (created_by);
create index cases_project_idx on public.cases (project_id);
create index cases_organization_project_idx on public.cases (organization_id, project_id);
create index cases_created_by_idx on public.cases (created_by);
create index documents_case_idx on public.documents (case_id);
create index documents_organization_case_idx on public.documents (organization_id, case_id);
create index documents_created_by_idx on public.documents (created_by);
create index findings_organization_case_idx on public.findings (organization_id, case_id);
create index findings_owner_idx on public.findings (owner_user_id);
create index rfis_organization_case_idx on public.rfis (organization_id, case_id);
create index rfis_organization_case_finding_idx
  on public.rfis (organization_id, case_id, finding_id);
create index rfis_finding_idx on public.rfis (finding_id);
create index rfis_issued_by_idx on public.rfis (issued_by);
create index rfis_answered_by_idx on public.rfis (answered_by);
create index analysis_jobs_organization_idx on public.analysis_jobs (organization_id, created_at desc);
create index analysis_jobs_case_idx on public.analysis_jobs (case_id);
create index analysis_jobs_organization_case_idx
  on public.analysis_jobs (organization_id, case_id);
create index analysis_jobs_requested_by_idx on public.analysis_jobs (requested_by);
create index audit_events_organization_idx on public.audit_events (organization_id, created_at desc);
create index audit_events_organization_case_idx on public.audit_events (organization_id, case_id);
create index audit_events_actor_idx on public.audit_events (actor_user_id);
create index webhook_subscriptions_organization_idx on public.webhook_subscriptions (organization_id);
create index webhook_subscriptions_case_idx on public.webhook_subscriptions (case_id);
create index webhook_subscriptions_organization_case_idx
  on public.webhook_subscriptions (organization_id, case_id);
create index webhook_subscriptions_created_by_idx on public.webhook_subscriptions (created_by);
create index webhook_deliveries_subscription_idx on public.webhook_deliveries (subscription_id);
create index webhook_deliveries_event_idx on public.webhook_deliveries (event_id);
create index webhook_deliveries_organization_subscription_idx
  on public.webhook_deliveries (organization_id, subscription_id);
create index webhook_deliveries_organization_event_idx
  on public.webhook_deliveries (organization_id, event_id);

-- A row's organization must agree with every organization-owned parent it
-- references. Independent foreign keys would otherwise permit a row to carry
-- organization A while pointing at a case, finding, event, or subscription in
-- organization B. RLS filters are not a substitute for relational integrity.
create unique index projects_organization_id_unique_idx
  on public.projects (organization_id, id);
create unique index cases_organization_id_unique_idx
  on public.cases (organization_id, id);
create unique index findings_organization_case_id_unique_idx
  on public.findings (organization_id, case_id, id);
create unique index audit_events_organization_id_unique_idx
  on public.audit_events (organization_id, id);
create unique index webhook_subscriptions_organization_id_unique_idx
  on public.webhook_subscriptions (organization_id, id);

alter table public.cases
  add constraint cases_organization_project_fk
  foreign key (organization_id, project_id)
  references public.projects (organization_id, id);
alter table public.documents
  add constraint documents_organization_case_fk
  foreign key (organization_id, case_id)
  references public.cases (organization_id, id);
alter table public.findings
  add constraint findings_organization_case_fk
  foreign key (organization_id, case_id)
  references public.cases (organization_id, id);
alter table public.rfis
  add constraint rfis_organization_case_fk
  foreign key (organization_id, case_id)
  references public.cases (organization_id, id),
  add constraint rfis_organization_case_finding_fk
  foreign key (organization_id, case_id, finding_id)
  references public.findings (organization_id, case_id, id);
alter table public.analysis_jobs
  add constraint analysis_jobs_organization_case_fk
  foreign key (organization_id, case_id)
  references public.cases (organization_id, id);
alter table public.audit_events
  add constraint audit_events_organization_case_fk
  foreign key (organization_id, case_id)
  references public.cases (organization_id, id);
alter table public.webhook_subscriptions
  add constraint webhook_subscriptions_organization_case_fk
  foreign key (organization_id, case_id)
  references public.cases (organization_id, id);
alter table public.webhook_deliveries
  add constraint webhook_deliveries_organization_subscription_fk
  foreign key (organization_id, subscription_id)
  references public.webhook_subscriptions (organization_id, id),
  add constraint webhook_deliveries_organization_event_fk
  foreign key (organization_id, event_id)
  references public.audit_events (organization_id, id);

-- Retention is an organization policy, not a client-controlled timestamp.
-- Callers may request a shorter lifetime but can never extend past the
-- organization's configured maximum.
create function private.apply_document_retention()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
declare
  configured_days integer;
  maximum_retention timestamptz;
begin
  select organization.raw_upload_retention_days
    into strict configured_days
    from public.organizations organization
   where organization.id = new.organization_id;

  maximum_retention := statement_timestamp() + make_interval(days => configured_days);
  new.retention_until := least(coalesce(new.retention_until, maximum_retention), maximum_retention);
  return new;
end;
$$;

create function private.apply_audit_retention()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
declare
  configured_days integer;
  maximum_retention timestamptz;
begin
  select organization.audit_retention_days
    into strict configured_days
    from public.organizations organization
   where organization.id = new.organization_id;

  maximum_retention := statement_timestamp() + make_interval(days => configured_days);
  new.retention_until := least(coalesce(new.retention_until, maximum_retention), maximum_retention);
  return new;
end;
$$;

revoke all on function private.apply_document_retention() from public, anon, authenticated;
revoke all on function private.apply_audit_retention() from public, anon, authenticated;

alter table public.documents alter column retention_until drop default;
alter table public.audit_events alter column retention_until drop default;

create trigger documents_apply_retention
before insert or update of organization_id, retention_until on public.documents
for each row execute function private.apply_document_retention();

create trigger audit_events_apply_retention
before insert or update of organization_id, retention_until on public.audit_events
for each row execute function private.apply_audit_retention();
