-- subscriptions-create.sql

begin;
---------------------------------------------------------------------------

create table subscription_kinds (
  name        varchar primary key,
  description text,
  inserted    timestamptz(0) default current_timestamp
);

create table subscriptions(
  email     varchar not null 
              references members(email)        
              on delete cascade 
              on update cascade,
  kind      varchar 
              references subscription_kinds
              on delete cascade
              on update cascade,
  constraint subscriptions_unique
              unique (email, kind),
  inserted  timestamptz(0) default current_timestamp
);

select migrations_insert('subscriptions create');

---------------------------------------------------------------------------
commit;