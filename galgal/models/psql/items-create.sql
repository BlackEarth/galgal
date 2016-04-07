-- items-create.sql

begin;

-------------
-- TABLES -- 
-------------

create table item_kinds (
  id          varchar primary key,
  parent      varchar references item_kinds(name) 
                on delete set null 
                on update cascade,
  description text,
  inserted    timestamptz(0) default now(),
  updated     timestamptz(0) default now()
);
insert into item_kinds (name, description) values ('Item', 'the base item_type for all items.');

create table items (
  id          varchar primary key,          -- a meaningful, unique moniker, appropriate to this domain.
  name        varchar not null,             -- all items have a name
  typename    varchar not null              -- and a typename
                default 'Item'
                references item_kinds(name)
                on delete cascade           -- deleting from item_kinds will delete all such items.
                on update cascade,
  title       varchar,
  title_idx   varchar,                      -- a stripped, text-only version of title, for searching.
  body        text,
  body_idx    text,                         -- a stripped, text-only version of body, for searching.
  inserted    timestamptz(0) default now(),
  updated     timestamptz(0) default now()
);

-- make items full-text searchable in pg.
alter table items add column tsv tsvector;
create index items_tsv_idx on items using gin(tsv);
create trigger items_tsv_update_trigger before insert or update 
  on items for each row execute procedure 
  tsvector_update_trigger(tsv, 'pg_catalog.english', title_idx, body_idx);

--------------
-- TRIGGERS --
--------------

-- automatically set the updated field.
create or replace function item_kinds_update_tr_fn() returns trigger as $$
    begin
        new.updated := now();
        return new;
    end;
$$ language plpgsql;
create trigger item_kinds_update_tr before update on item_kinds
  for each row execute procedure item_kinds_update_tr_fn();

-- text_to_idx_clean(text) -- to create body_idx from body and title_idx from title
create or replace function text_to_idx_clean(text) returns text as $body_idx$
  declare
    body  text;
    spat  varchar;      -- span pattern for special cases where space should not be added around the span tags.
  begin
    -- special cases: any span with class name that contains, as whole words, "sc", "ital", or "red".
    spat := $$<span class=["'].*?\b(?:sc|ital|red)\b.*?['"]>([^<]*?)</span>$$;
    body := regexp_replace($1, spat, E'\1', 'ig');          -- special-case spans removed without leaving space
    body := regexp_replace(body, $$<[^>]*?>$$, ' ', 'ig');  -- all other element tags replaced with a space
    body := regexp_replace(body, $$&[^&;]*?;$$, ' ', 'ig'); -- all entity references replaced with a space
    body := regexp_replace(body, $$\W+$$, ' ', 'ig');       -- all multiple non-word characters replaced with a space
    return body;
  end;
$body_idx$ language 'plpgsql';

-- trigger function
-- automatically generate id from name + typename + product
-- automatically generate title_idx from title, and body_idx from body
create or replace function items_insert_update_tr_fn() returns trigger as $items_insert_update_tr_fn$
  begin
    if new.title is null then
      new.title = '';
    end if;
    if new.name is null then
      new.name = regexp_replace(new.title, $$\s+$$, '-');
    end if;
    if new.id is null then
      new.id := rand_id();
    end if;
    new.title_idx := text_to_idx_clean(new.title);
    new.body_idx := text_to_idx_clean(new.body);
    new.updated := now();
    return new;
  end;
$items_insert_update_tr_fn$ language plpgsql;

-- trigger
create trigger items_insert_update_tr before insert or update on items
  for each row execute procedure items_insert_update_tr_fn();


---------------------------------------------------------------------------

select migrations_insert('items create');

---------------------------------------------------------------------------
commit;
