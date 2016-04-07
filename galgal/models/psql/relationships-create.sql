-- relationships-create.sql
---------------------------------------------------------------------------
-- relationships between members, to represent a social graph

begin;
---------------------------------------------------------------------------

create table relationship_kinds (
  id          varchar primary key,
  description text,
  inserted    timestamptz(0) default current_timestamp
);

create table relationships (
  email1      varchar not null
                references members(email)
                on delete cascade 
                on update cascade,
  email2      varchar not null
                references members(email)
                on delete cascade 
                on update cascade,
  kind        varchar 
                references relationship_kinds(id)
                on delete set null
                on update cascade,
  constraint  relationships_unique 
               unique (email1, email2, kind),
  inserted    timestamptz(0) default current_timestamp,
  verified    timestamptz(0)
);

select migrations_insert('relationships create');

---------------------------------------------------------------------------
commit;