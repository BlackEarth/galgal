-- items-tags-create

begin;

create table tags (
  name  varchar primary key
);

create table items_tags (
  tag_name varchar not null references tags(name) on delete cascade on update cascade,
  item_id varchar not null references items(id) on delete cascade on update cascade,
  unique (tag_name, item_id)
);

select migrations_insert('items_tags create');

commit;