begin;

select plan(24);

select results_eq(
  $$
    select relation.relname::text collate "C"
      from pg_class relation
      join pg_namespace namespace on namespace.oid = relation.relnamespace
     where namespace.nspname = 'public'
       and relation.relkind = 'r'
       and relation.relname in (
         'analysis_jobs', 'audit_events', 'cases', 'documents', 'findings',
         'organization_memberships', 'organizations', 'projects', 'rfis',
         'webhook_deliveries', 'webhook_subscriptions'
       )
       and relation.relrowsecurity
     order by relation.relname
  $$,
  $$ values
    ('analysis_jobs'::text collate "C"), ('audit_events'::text collate "C"),
    ('cases'::text collate "C"), ('documents'::text collate "C"),
    ('findings'::text collate "C"),
    ('organization_memberships'::text collate "C"),
    ('organizations'::text collate "C"), ('projects'::text collate "C"),
    ('rfis'::text collate "C"), ('webhook_deliveries'::text collate "C"),
    ('webhook_subscriptions'::text collate "C")
  $$,
  'every exposed application table has RLS enabled'
);

select results_eq(
  $$
    select enum_value.enumlabel::text collate "C"
      from pg_type enum_type
      join pg_enum enum_value on enum_value.enumtypid = enum_type.oid
     where enum_type.typname = 'organization_role'
     order by enum_value.enumsortorder
  $$,
  $$ values
    ('owner'::text collate "C"), ('engineer'::text collate "C"),
    ('reviewer'::text collate "C"), ('viewer'::text collate "C")
  $$,
  'organization roles are the reviewed closed set'
);

select ok(
  'security_invoker=true' = any(coalesce(
    (select relation.reloptions
       from pg_class relation
       join pg_namespace namespace on namespace.oid = relation.relnamespace
      where namespace.nspname = 'public' and relation.relname = 'case_overview'),
    array[]::text[]
  )),
  'case_overview executes with caller permissions'
);

select is(
  (select count(*)
     from pg_proc routine
     join pg_namespace namespace on namespace.oid = routine.pronamespace
    where namespace.nspname = 'public'
      and routine.proname in ('is_org_member', 'has_org_role')
      and routine.prosecdef),
  0::bigint,
  'public authorization helpers never bypass RLS'
);

select is(
  (select count(*)
     from pg_proc routine
     join pg_namespace namespace on namespace.oid = routine.pronamespace
    where namespace.nspname = 'private'
      and routine.proname in ('apply_document_retention', 'apply_audit_retention')
      and routine.prosecdef),
  0::bigint,
  'retention triggers are security invokers'
);

select is(
  (select count(*)
     from pg_proc routine
     join pg_namespace namespace on namespace.oid = routine.pronamespace
     cross join lateral aclexplode(coalesce(
       routine.proacl,
       acldefault('f', routine.proowner)
     )) acl_entry
    where namespace.nspname = 'public'
      and routine.proname in ('is_org_member', 'has_org_role')
      and acl_entry.grantee = 0
      and acl_entry.privilege_type = 'EXECUTE'),
  0::bigint,
  'authorization helpers are not executable by PUBLIC'
);

select is(
  (select count(*)
     from pg_proc routine
     join pg_namespace namespace on namespace.oid = routine.pronamespace
    where namespace.nspname = 'public'
      and routine.proname in ('is_org_member', 'has_org_role')
      and has_function_privilege('authenticated', routine.oid, 'EXECUTE')),
  2::bigint,
  'authenticated callers can use both authorization helpers'
);

select ok(
  not has_schema_privilege('authenticated', 'private', 'USAGE'),
  'authenticated cannot enter the worker-private schema'
);

select ok(
  not has_schema_privilege('anon', 'private', 'USAGE'),
  'anonymous callers cannot enter the worker-private schema'
);

select is(
  (select count(*)
     from pg_class relation
     join pg_namespace namespace on namespace.oid = relation.relnamespace
    where namespace.nspname = 'public'
      and relation.relname in (
        'analysis_jobs', 'audit_events', 'cases', 'documents', 'findings',
        'organization_memberships', 'organizations', 'projects', 'rfis',
        'webhook_deliveries', 'webhook_subscriptions'
      )
      and (
        has_table_privilege('anon', relation.oid, 'SELECT')
        or has_table_privilege('anon', relation.oid, 'INSERT')
        or has_table_privilege('anon', relation.oid, 'UPDATE')
        or has_table_privilege('anon', relation.oid, 'DELETE')
      )),
  0::bigint,
  'anonymous callers have no application-table privileges'
);

select is(
  (select bucket.public from storage.buckets bucket where bucket.id = 'case-documents'),
  false,
  'case documents use a private bucket'
);

select results_eq(
  $$
    select policy.policyname::text collate "C"
      from pg_policies policy
     where policy.schemaname = 'storage'
       and policy.tablename = 'objects'
       and policy.policyname like 'case_documents_%'
     order by policy.policyname
  $$,
  $$ values
    ('case_documents_delete'::text collate "C"),
    ('case_documents_insert'::text collate "C"),
    ('case_documents_select'::text collate "C"),
    ('case_documents_update'::text collate "C")
  $$,
  'private storage has the complete operation policy set'
);

select ok(
  to_regclass('pgmq.q_analysis_jobs') is not null,
  'the durable analysis queue exists'
);

select is(
  (select relation.relpersistence
     from pg_class relation
     join pg_namespace namespace on namespace.oid = relation.relnamespace
    where namespace.nspname = 'pgmq' and relation.relname = 'q_analysis_jobs'),
  'p'::"char",
  'the analysis queue is logged and durable'
);

select ok(
  not has_schema_privilege('authenticated', 'pgmq', 'USAGE'),
  'authenticated callers cannot access direct queue primitives'
);

select ok(
  not has_schema_privilege('anon', 'pgmq', 'USAGE'),
  'anonymous callers cannot access direct queue primitives'
);

select is(
  (select count(*)
     from pg_proc routine
     join pg_namespace namespace on namespace.oid = routine.pronamespace
     cross join lateral aclexplode(coalesce(
       routine.proacl,
       acldefault('f', routine.proowner)
     )) acl_entry
    where namespace.nspname = 'pgmq'
      and acl_entry.grantee = 0
      and acl_entry.privilege_type = 'EXECUTE'),
  0::bigint,
  'queue functions are not executable by PUBLIC'
);

select results_eq(
  $$
    select retention_trigger.tgname::text collate "C"
      from pg_trigger retention_trigger
      join pg_class relation on relation.oid = retention_trigger.tgrelid
      join pg_namespace namespace on namespace.oid = relation.relnamespace
     where namespace.nspname = 'public'
       and not retention_trigger.tgisinternal
       and retention_trigger.tgname in ('documents_apply_retention', 'audit_events_apply_retention')
     order by retention_trigger.tgname
  $$,
  $$ values
    ('audit_events_apply_retention'::text collate "C"),
    ('documents_apply_retention'::text collate "C")
  $$,
  'organization retention is enforced by database triggers'
);

select is(
  (select count(*)
     from information_schema.columns field
    where field.table_schema = 'public'
      and (field.table_name, field.column_name) in (
        ('documents', 'retention_until'), ('audit_events', 'retention_until')
      )
      and field.column_default is null),
  2::bigint,
  'retention timestamps are no longer fixed global defaults'
);

select is(
  (select count(*)
     from pg_policies policy
    where policy.schemaname in ('public', 'storage')
      and (
        policy.schemaname = 'public'
        or policy.policyname like 'case_documents_%'
      )
      and policy.cmd = 'UPDATE'
      and policy.with_check is null),
  0::bigint,
  'every update policy protects both old and resulting rows'
);

select is(
  (select count(*)
     from pg_policies policy
    where (
        policy.schemaname = 'public'
        or (policy.schemaname = 'storage' and policy.policyname like 'case_documents_%')
      )
      and policy.roles <> array['authenticated']::name[]),
  0::bigint,
  'application policies explicitly target authenticated callers'
);

select has_index(
  'public',
  'documents',
  'documents_case_idx',
  'document-to-case joins and cascades are indexed'
);

select is(
  (select count(*)
     from pg_constraint relation_constraint
    where relation_constraint.contype = 'f'
      and relation_constraint.conname in (
        'cases_organization_project_fk',
        'documents_organization_case_fk',
        'findings_organization_case_fk',
        'rfis_organization_case_fk',
        'rfis_organization_case_finding_fk',
        'analysis_jobs_organization_case_fk',
        'audit_events_organization_case_fk',
        'webhook_subscriptions_organization_case_fk',
        'webhook_deliveries_organization_subscription_fk',
        'webhook_deliveries_organization_event_fk'
      )),
  10::bigint,
  'organization-owned references enforce tenant consistency'
);

select is(
  (select count(*)
     from pg_proc routine
     join pg_namespace namespace on namespace.oid = routine.pronamespace
    where namespace.nspname = 'private'
      and routine.proname in ('apply_document_retention', 'apply_audit_retention')
      and not exists (
        select 1
          from unnest(coalesce(routine.proconfig, array[]::text[])) setting
         where setting in ('search_path=', 'search_path=""')
      )),
  0::bigint,
  'private trigger functions pin an empty search path'
);

select * from finish();
rollback;
