create extension if not exists pgmq;

create schema if not exists private;
revoke all on schema private from public, anon, authenticated;

create type public.organization_role as enum ('owner', 'engineer', 'reviewer', 'viewer');
create type public.case_status as enum ('open', 'in_review', 'resolved', 'deleted');
create type public.finding_status as enum ('open', 'accepted', 'rfi_drafted', 'resolved', 'dismissed');
create type public.rfi_status as enum ('draft', 'issued', 'answered', 'closed');
create type public.analysis_job_status as enum ('queued', 'running', 'succeeded', 'failed', 'cancelled');

create table public.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null check (char_length(name) between 1 and 160),
  created_by uuid not null references auth.users(id),
  raw_upload_retention_days integer not null default 30 check (raw_upload_retention_days between 1 and 3650),
  audit_retention_days integer not null default 365 check (audit_retention_days between 30 and 3650),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.organization_memberships (
  organization_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role public.organization_role not null,
  created_at timestamptz not null default now(),
  primary key (organization_id, user_id)
);

create table public.projects (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  name text not null check (char_length(name) between 1 and 200),
  external_key text,
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (organization_id, external_key)
);

create table public.cases (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  project_id uuid references public.projects(id) on delete set null,
  name text not null default '' check (char_length(name) <= 240),
  status public.case_status not null default 'open',
  version bigint not null default 1 check (version > 0),
  created_by uuid not null references auth.users(id),
  deleted_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.documents (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  case_id uuid not null references public.cases(id) on delete cascade,
  storage_bucket text not null default 'case-documents',
  storage_path text not null,
  sha256 text not null check (sha256 ~ '^[0-9a-f]{64}$'),
  mime_type text not null,
  size_bytes bigint not null check (size_bytes between 0 and 15728640),
  extraction_status text not null default 'pending' check (extraction_status in ('pending', 'running', 'succeeded', 'failed')),
  retention_until timestamptz not null default (now() + interval '30 days'),
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  unique (storage_bucket, storage_path)
);

create table public.findings (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  case_id uuid not null references public.cases(id) on delete cascade,
  component text not null default '',
  parameter text not null default '',
  required_value text not null default '',
  provided_value text not null default '',
  unit text not null default '',
  severity text not null check (severity in ('Critical', 'Major', 'Minor')),
  standard_ref text not null default '',
  spec_clause text not null default '',
  predicted_cx_test text not null default '',
  lead_time_weeks numeric,
  rationale text not null default '',
  status public.finding_status not null default 'open',
  owner_user_id uuid references auth.users(id),
  resolution_note text not null default '',
  resolved_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.rfis (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  case_id uuid not null references public.cases(id) on delete cascade,
  finding_id uuid not null references public.findings(id) on delete cascade,
  question text not null default '',
  drafted_text text not null default '',
  response_text text not null default '',
  sources jsonb not null default '[]'::jsonb check (jsonb_typeof(sources) = 'array'),
  mode text not null default '',
  status public.rfi_status not null default 'draft',
  issued_by uuid references auth.users(id),
  answered_by uuid references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.analysis_jobs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  case_id uuid references public.cases(id) on delete cascade,
  requested_by uuid not null references auth.users(id),
  input_hash text not null check (input_hash ~ '^[0-9a-f]{64}$'),
  idempotency_key text not null check (char_length(idempotency_key) between 8 and 200),
  status public.analysis_job_status not null default 'queued',
  mode text,
  result jsonb,
  error_code text,
  attempts integer not null default 0 check (attempts between 0 and 20),
  created_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz,
  unique (organization_id, idempotency_key)
);

create table public.audit_events (
  id bigint generated always as identity primary key,
  organization_id uuid not null references public.organizations(id) on delete cascade,
  case_id uuid references public.cases(id) on delete set null,
  actor_user_id uuid references auth.users(id) on delete set null,
  action text not null check (char_length(action) between 1 and 120),
  entity_type text not null check (char_length(entity_type) between 1 and 80),
  entity_id uuid,
  metadata jsonb not null default '{}'::jsonb check (jsonb_typeof(metadata) = 'object'),
  retention_until timestamptz not null default (now() + interval '365 days'),
  created_at timestamptz not null default now()
);

create table public.webhook_subscriptions (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  case_id uuid references public.cases(id) on delete cascade,
  endpoint_ciphertext bytea not null,
  endpoint_hint text not null,
  secret_ciphertext bytea not null,
  active boolean not null default true,
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.webhook_deliveries (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  subscription_id uuid not null references public.webhook_subscriptions(id) on delete cascade,
  event_id bigint references public.audit_events(id) on delete set null,
  status text not null default 'queued' check (status in ('queued', 'delivering', 'succeeded', 'failed', 'dead_letter')),
  attempt_count integer not null default 0 check (attempt_count between 0 and 20),
  response_status integer,
  next_attempt_at timestamptz,
  last_error_code text,
  created_at timestamptz not null default now(),
  delivered_at timestamptz
);

create index memberships_user_idx on public.organization_memberships (user_id, organization_id);
create index projects_organization_idx on public.projects (organization_id, created_at desc);
create index cases_organization_idx on public.cases (organization_id, updated_at desc) where deleted_at is null;
create index documents_retention_idx on public.documents (retention_until);
create index findings_case_idx on public.findings (case_id, created_at);
create index rfis_case_idx on public.rfis (case_id, created_at);
create index analysis_jobs_status_idx on public.analysis_jobs (status, created_at);
create index audit_events_case_idx on public.audit_events (case_id, created_at desc);
create index audit_events_retention_idx on public.audit_events (retention_until);
create index webhook_deliveries_retry_idx on public.webhook_deliveries (status, next_attempt_at);

create function public.is_org_member(target_organization_id uuid)
returns boolean
language sql
stable
security invoker
set search_path = ''
as $$
  select exists (
    select 1 from public.organization_memberships membership
    where membership.organization_id = target_organization_id
      and membership.user_id = (select auth.uid())
  );
$$;

create function public.has_org_role(target_organization_id uuid, allowed_roles public.organization_role[])
returns boolean
language sql
stable
security invoker
set search_path = ''
as $$
  select exists (
    select 1 from public.organization_memberships membership
    where membership.organization_id = target_organization_id
      and membership.user_id = (select auth.uid())
      and membership.role = any(allowed_roles)
  );
$$;

revoke all on function public.is_org_member(uuid) from public;
revoke all on function public.has_org_role(uuid, public.organization_role[]) from public;
grant execute on function public.is_org_member(uuid) to authenticated;
grant execute on function public.has_org_role(uuid, public.organization_role[]) to authenticated;

alter table public.organizations enable row level security;
alter table public.organization_memberships enable row level security;
alter table public.projects enable row level security;
alter table public.cases enable row level security;
alter table public.documents enable row level security;
alter table public.findings enable row level security;
alter table public.rfis enable row level security;
alter table public.analysis_jobs enable row level security;
alter table public.audit_events enable row level security;
alter table public.webhook_subscriptions enable row level security;
alter table public.webhook_deliveries enable row level security;

create policy organizations_select on public.organizations for select to authenticated
using (created_by = (select auth.uid()) or public.is_org_member(id));
create policy organizations_insert on public.organizations for insert to authenticated
with check (created_by = (select auth.uid()));
create policy organizations_update on public.organizations for update to authenticated
using (public.has_org_role(id, array['owner']::public.organization_role[]))
with check (public.has_org_role(id, array['owner']::public.organization_role[]));

create policy memberships_select on public.organization_memberships for select to authenticated
using (user_id = (select auth.uid()));
create policy memberships_insert on public.organization_memberships for insert to authenticated
with check (
  public.has_org_role(organization_id, array['owner']::public.organization_role[])
  or (
    user_id = (select auth.uid())
    and role = 'owner'
    and exists (
      select 1 from public.organizations organization
      where organization.id = organization_id and organization.created_by = (select auth.uid())
    )
  )
);
create policy memberships_update on public.organization_memberships for update to authenticated
using (public.has_org_role(organization_id, array['owner']::public.organization_role[]))
with check (public.has_org_role(organization_id, array['owner']::public.organization_role[]));
create policy memberships_delete on public.organization_memberships for delete to authenticated
using (public.has_org_role(organization_id, array['owner']::public.organization_role[]));

create policy projects_select on public.projects for select to authenticated using (public.is_org_member(organization_id));
create policy projects_insert on public.projects for insert to authenticated
with check (public.has_org_role(organization_id, array['owner','engineer']::public.organization_role[]) and created_by = (select auth.uid()));
create policy projects_update on public.projects for update to authenticated
using (public.has_org_role(organization_id, array['owner','engineer']::public.organization_role[]))
with check (public.has_org_role(organization_id, array['owner','engineer']::public.organization_role[]));
create policy projects_delete on public.projects for delete to authenticated
using (public.has_org_role(organization_id, array['owner']::public.organization_role[]));

create policy cases_select on public.cases for select to authenticated using (public.is_org_member(organization_id));
create policy cases_insert on public.cases for insert to authenticated
with check (public.has_org_role(organization_id, array['owner','engineer']::public.organization_role[]) and created_by = (select auth.uid()));
create policy cases_update on public.cases for update to authenticated
using (public.has_org_role(organization_id, array['owner','engineer','reviewer']::public.organization_role[]))
with check (public.has_org_role(organization_id, array['owner','engineer','reviewer']::public.organization_role[]));
create policy cases_delete on public.cases for delete to authenticated
using (public.has_org_role(organization_id, array['owner']::public.organization_role[]));

create policy documents_select on public.documents for select to authenticated using (public.is_org_member(organization_id));
create policy documents_insert on public.documents for insert to authenticated
with check (public.has_org_role(organization_id, array['owner','engineer']::public.organization_role[]) and created_by = (select auth.uid()));
create policy documents_delete on public.documents for delete to authenticated
using (public.has_org_role(organization_id, array['owner','engineer']::public.organization_role[]));

create policy findings_select on public.findings for select to authenticated using (public.is_org_member(organization_id));
create policy findings_insert on public.findings for insert to authenticated
with check (public.has_org_role(organization_id, array['owner','engineer']::public.organization_role[]));
create policy findings_update on public.findings for update to authenticated
using (public.has_org_role(organization_id, array['owner','engineer','reviewer']::public.organization_role[]))
with check (public.has_org_role(organization_id, array['owner','engineer','reviewer']::public.organization_role[]));
create policy findings_delete on public.findings for delete to authenticated
using (public.has_org_role(organization_id, array['owner']::public.organization_role[]));

create policy rfis_select on public.rfis for select to authenticated using (public.is_org_member(organization_id));
create policy rfis_insert on public.rfis for insert to authenticated
with check (public.has_org_role(organization_id, array['owner','engineer','reviewer']::public.organization_role[]));
create policy rfis_update on public.rfis for update to authenticated
using (public.has_org_role(organization_id, array['owner','engineer','reviewer']::public.organization_role[]))
with check (public.has_org_role(organization_id, array['owner','engineer','reviewer']::public.organization_role[]));
create policy rfis_delete on public.rfis for delete to authenticated
using (public.has_org_role(organization_id, array['owner']::public.organization_role[]));

create policy jobs_select on public.analysis_jobs for select to authenticated using (public.is_org_member(organization_id));
create policy jobs_insert on public.analysis_jobs for insert to authenticated
with check (public.is_org_member(organization_id) and requested_by = (select auth.uid()));
create policy audit_select on public.audit_events for select to authenticated using (public.is_org_member(organization_id));

create policy webhook_subscriptions_select on public.webhook_subscriptions for select to authenticated using (public.is_org_member(organization_id));
create policy webhook_subscriptions_insert on public.webhook_subscriptions for insert to authenticated
with check (public.has_org_role(organization_id, array['owner','engineer']::public.organization_role[]) and created_by = (select auth.uid()));
create policy webhook_subscriptions_update on public.webhook_subscriptions for update to authenticated
using (public.has_org_role(organization_id, array['owner','engineer']::public.organization_role[]))
with check (public.has_org_role(organization_id, array['owner','engineer']::public.organization_role[]));
create policy webhook_subscriptions_delete on public.webhook_subscriptions for delete to authenticated
using (public.has_org_role(organization_id, array['owner']::public.organization_role[]));
create policy webhook_deliveries_select on public.webhook_deliveries for select to authenticated using (public.is_org_member(organization_id));

create view public.case_overview with (security_invoker = true) as
select case_record.id, case_record.organization_id, case_record.project_id, case_record.name,
       case_record.status, case_record.version, case_record.updated_at,
       count(distinct finding.id) as finding_count,
       count(distinct rfi.id) as rfi_count
from public.cases case_record
left join public.findings finding on finding.case_id = case_record.id
left join public.rfis rfi on rfi.case_id = case_record.id
where case_record.deleted_at is null
group by case_record.id;

grant select, insert, update on public.organizations to authenticated;
grant select, insert, update, delete on public.organization_memberships to authenticated;
grant select, insert, update, delete on public.projects, public.cases, public.findings, public.rfis to authenticated;
grant select, insert, delete on public.documents to authenticated;
grant select, insert on public.analysis_jobs to authenticated;
grant select on public.audit_events, public.webhook_deliveries, public.case_overview to authenticated;
grant select, insert, update, delete on public.webhook_subscriptions to authenticated;
grant all on all tables in schema public to service_role;
grant all on all sequences in schema public to service_role;

insert into storage.buckets (id, name, public, file_size_limit)
values ('case-documents', 'case-documents', false, 15728640)
on conflict (id) do update set public = false, file_size_limit = excluded.file_size_limit;

create policy case_documents_select on storage.objects for select to authenticated
using (
  bucket_id = 'case-documents'
  and exists (
    select 1 from public.organization_memberships membership
    join public.cases case_record on case_record.organization_id = membership.organization_id
    where membership.organization_id::text = (storage.foldername(name))[1]
      and case_record.id::text = (storage.foldername(name))[2]
      and case_record.deleted_at is null
      and membership.user_id = (select auth.uid())
  )
);
create policy case_documents_insert on storage.objects for insert to authenticated
with check (
  bucket_id = 'case-documents'
  and exists (
    select 1 from public.organization_memberships membership
    join public.cases case_record on case_record.organization_id = membership.organization_id
    where membership.organization_id::text = (storage.foldername(name))[1]
      and case_record.id::text = (storage.foldername(name))[2]
      and case_record.deleted_at is null
      and membership.user_id = (select auth.uid())
      and membership.role in ('owner','engineer')
  )
);
create policy case_documents_update on storage.objects for update to authenticated
using (
  bucket_id = 'case-documents'
  and exists (
    select 1 from public.organization_memberships membership
    join public.cases case_record on case_record.organization_id = membership.organization_id
    where membership.organization_id::text = (storage.foldername(name))[1]
      and case_record.id::text = (storage.foldername(name))[2]
      and case_record.deleted_at is null
      and membership.user_id = (select auth.uid())
      and membership.role in ('owner','engineer')
  )
)
with check (
  bucket_id = 'case-documents'
  and exists (
    select 1 from public.organization_memberships membership
    join public.cases case_record on case_record.organization_id = membership.organization_id
    where membership.organization_id::text = (storage.foldername(name))[1]
      and case_record.id::text = (storage.foldername(name))[2]
      and case_record.deleted_at is null
      and membership.user_id = (select auth.uid())
      and membership.role in ('owner','engineer')
  )
);
create policy case_documents_delete on storage.objects for delete to authenticated
using (
  bucket_id = 'case-documents'
  and exists (
    select 1 from public.organization_memberships membership
    join public.cases case_record on case_record.organization_id = membership.organization_id
    where membership.organization_id::text = (storage.foldername(name))[1]
      and case_record.id::text = (storage.foldername(name))[2]
      and case_record.deleted_at is null
      and membership.user_id = (select auth.uid())
      and membership.role in ('owner','engineer')
  )
);

do $$
begin
  if to_regclass('pgmq.q_analysis_jobs') is null then
    perform pgmq.create('analysis_jobs');
  end if;
end;
$$;
