-- groups-create.sql

begin;
---------------------------------------------------------------------------

create table groups (
  id          varchar primary key,
  description text,
  inserted    timestamptz(0) default current_timestamp
);

-- members can have memberships in any number of groups.
create table groups_memberships (
  group_id      varchar not null
                  references groups(id)
                  on delete cascade
                  on update cascade,
  email         varchar not null
                  references members(email)
                  on delete cascade
                  on update cascade,
  inserted      timestamptz(0) 
                  default current_timestamp,
  verified      timestamptz(0)
);

-- groups can "own" any number of items, and items can be "owned" by any number of groups.
create table groups_items (
  groupname varchar not null
              references groups(name)
              on delete cascade
              on update cascade,
  item_id   varchar not null
              references items(id)
              on delete cascade
              on update cascade,
  inserted  timestamptz(0)
              default current_timestamp
);

select migrations_insert('groups create');

---------------------------------------------------------------------------
commit;