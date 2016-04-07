
begin;
---------------------------------------------------------------------------

create table feedback(
  id        serial primary key,
  leftby    varchar,  -- don''t make foreign key, just insert user name & email here.
  inserted  timestamptz(0) default current_timestamp,
  subject   varchar,
  body      text
);

select migrations_insert('create feedback');
---------------------------------------------------------------------------
commit;
