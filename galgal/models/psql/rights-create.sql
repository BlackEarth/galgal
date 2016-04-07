-- rights-create.sql

begin;
---------------------------------------------------------------------------

-- rights that are defined
create table rights (
  name        varchar primary key,
  description text,
  inserted    timestamptz(0) default current_timestamp
);

-- which rights each role has
create table rights_roles (
  right_id    varchar not null
                references rights(id)
                on delete cascade
                on update cascade,
  role_id     varchar not null
                references roles(id)
                on delete cascade
                on update cascade,
  inserted    timestamptz(0) default current_timestamp
);

select migrations_insert('rights create');

---------------------------------------------------------------------------
commit;