-- roles-create.sql

begin;
---------------------------------------------------------------------------

create table roles (
  id          varchar primary key,
  description text,
  created     timestamptz(0) default current_timestamp
);

select migrations_insert('roles create');

---------------------------------------------------------------------------
commit;