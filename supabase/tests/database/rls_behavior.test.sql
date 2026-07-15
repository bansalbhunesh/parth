begin;

select plan(12);

insert into auth.users (id, email, aud, role)
values
  ('11111111-1111-1111-1111-111111111111', 'owner-a@example.test', 'authenticated', 'authenticated'),
  ('22222222-2222-2222-2222-222222222222', 'viewer-b@example.test', 'authenticated', 'authenticated');

insert into public.organizations (
  id, name, created_by, raw_upload_retention_days, audit_retention_days
)
values
  (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Organization A',
    '11111111-1111-1111-1111-111111111111', 10, 45
  ),
  (
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Organization B',
    '22222222-2222-2222-2222-222222222222', 30, 365
  );

insert into public.organization_memberships (organization_id, user_id, role)
values
  (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    '11111111-1111-1111-1111-111111111111',
    'owner'
  ),
  (
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    '22222222-2222-2222-2222-222222222222',
    'viewer'
  );

insert into public.projects (id, organization_id, name, created_by)
values
  (
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'Project A',
    '11111111-1111-1111-1111-111111111111'
  ),
  (
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'Project B',
    '22222222-2222-2222-2222-222222222222'
  );

insert into public.cases (id, organization_id, project_id, name, created_by)
values
  (
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'Case A',
    '11111111-1111-1111-1111-111111111111'
  ),
  (
    'ffffffff-ffff-ffff-ffff-ffffffffffff',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    'Case B',
    '22222222-2222-2222-2222-222222222222'
  );

insert into public.documents (
  id, organization_id, case_id, storage_path, sha256, mime_type,
  size_bytes, retention_until, created_by
)
values (
  '12345678-1234-1234-1234-123456789012',
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee/document.txt',
  repeat('a', 64), 'text/plain', 100,
  statement_timestamp() + interval '365 days',
  '11111111-1111-1111-1111-111111111111'
);

insert into public.audit_events (
  organization_id, case_id, actor_user_id, action, entity_type,
  entity_id, metadata, retention_until
)
values (
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
  '11111111-1111-1111-1111-111111111111',
  'case.created', 'case', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
  '{}'::jsonb, statement_timestamp() + interval '365 days'
);

select throws_like(
  $$
    insert into public.cases (organization_id, project_id, name, created_by)
    values (
      'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      'dddddddd-dddd-dddd-dddd-dddddddddddd',
      'Cross-tenant project',
      '11111111-1111-1111-1111-111111111111'
    )
  $$,
  '%violates foreign key constraint "cases_organization_project_fk"%',
  'a case cannot reference another organization project'
);

select throws_like(
  $$
    insert into public.documents (
      organization_id, case_id, storage_path, sha256, mime_type,
      size_bytes, created_by
    )
    values (
      'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      'ffffffff-ffff-ffff-ffff-ffffffffffff',
      'invalid/cross-tenant.txt', repeat('b', 64), 'text/plain', 10,
      '11111111-1111-1111-1111-111111111111'
    )
  $$,
  '%violates foreign key constraint "documents_organization_case_fk"%',
  'a document cannot reference another organization case'
);

select ok(
  (select document.retention_until <= statement_timestamp() + interval '10 days 1 minute'
     from public.documents document
    where document.id = '12345678-1234-1234-1234-123456789012'),
  'document retention cannot exceed the organization maximum'
);

select ok(
  (select event.retention_until <= statement_timestamp() + interval '45 days 1 minute'
     from public.audit_events event
    where event.entity_id = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee'),
  'audit retention cannot exceed the organization maximum'
);

select set_config('request.jwt.claim.sub', '11111111-1111-1111-1111-111111111111', true);
set local role authenticated;

select results_eq(
  $$ select project.name::text from public.projects project order by project.name $$,
  $$ values ('Project A'::text) $$,
  'an owner sees only projects in their organization'
);

select results_eq(
  $$ select overview.name::text from public.case_overview overview order by overview.name $$,
  $$ values ('Case A'::text) $$,
  'the security-invoker view does not leak another organization'
);

select ok(
  public.has_org_role(
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    array['owner']::public.organization_role[]
  ),
  'the owner role resolves for the caller organization'
);

select ok(
  not public.has_org_role(
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    array['owner', 'viewer']::public.organization_role[]
  ),
  'role checks cannot inspect another organization'
);

select results_eq(
  $$
    select membership.organization_id::text
      from public.organization_memberships membership
     order by membership.organization_id
  $$,
  $$ values ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::text) $$,
  'membership rows are self-scoped'
);

reset role;
select set_config('request.jwt.claim.sub', '22222222-2222-2222-2222-222222222222', true);
set local role authenticated;

select results_eq(
  $$ select project.name::text from public.projects project order by project.name $$,
  $$ values ('Project B'::text) $$,
  'a viewer sees only projects in their organization'
);

select results_eq(
  $$ select overview.name::text from public.case_overview overview order by overview.name $$,
  $$ values ('Case B'::text) $$,
  'the view remains tenant-scoped for a viewer'
);

select results_eq(
  $$
    update public.cases
       set name = 'Unauthorized change'
     where id = 'ffffffff-ffff-ffff-ffff-ffffffffffff'
    returning id::text
  $$,
  $$ select null::text where false $$,
  'a viewer cannot mutate a case'
);

select * from finish();
rollback;
