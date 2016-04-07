-- resources-create.sql
---------------------------------------------------------------------------
-- the resources model is used to place resources in the site, 
-- for url-based lookup and url-based rights management.

begin;
---------------------------------------------------------------------------

create table resources (
  uri         varchar primary key,        -- the location of the resource.
  item_id     varchar not null 
                references items(id)      -- the id of the item
                on delete cascade
                on update cascade,
  parent_uri  varchar not null
                references resources(uri) -- and we point to a parent
                on delete cascade
                on update cascade,
  inserted    timestamptz(0) default current_timestamp
);

---------------------------------------------------------------------------
-- now, given an item_id and a parent_uri, 
-- we construct the uri automatically before insert or update on resources.
-- If the uri is also given, then we can set it as long as the parent_uri exists
-- and the uri does not already exist. 
-- The root item ('/') will set its own parent_uri = uri = '/'.
---------------------------------------------------------------------------
-- a trigger + function: when we insert or update a single resource, this 
-- function updates the resource uri (and that of all it s children)
-- to reflect the resource new position in the uri tree.
---------------------------------------------------------------------------

create or replace function resources_uri__insert_update_tr_fn()
returns trigger as $$
declare
  parent    resources%ROWTYPE;
  item      items%ROWTYPE;
begin

  -- A new uri just needs to be created.
  -- There must be a parent_uri and an item_id,
  -- but a new root item will set its own parent_uri and uri = /
  -- -- more error checking needed?
/*
  raise notice 'new.uri = %', new.uri;
  raise notice 'new.parent_uri = %', new.parent_uri;
  raise notice 'new.item_id = %', new.item_id;
*/
  if new.parent_uri = '/' and new.uri = '/' then
    parent := new;
    select into item
      * from items
      where id = new.item_id;
  elsif new.parent_uri is not null and new.item_id is not null then  
    select into parent
      * from resources 
      where uri = new.parent_uri;
    select into item
      * from items
      where id = new.item_id;
  end if;
/*  
  raise notice 'parent.uri = %', parent.uri;
  raise notice 'item.id = %', item.id;
  raise notice 'item.name = %', item.name;
*/  
  -- only proceed if we actually find an item and a parent,
  -- and if the new resource is not going to be root note.
  -- (if not, the insertion itself will raise a key error.)

  if item.id is not null and parent.uri is not null 
    and (new.uri != '/' or new.uri is null) then
/*    
    raise notice 'changing new.uri';
*/    
    -- Children of the root node will just need to add
    -- their name to the root uri of /.
    -- All others will have to add a forward slash separator

    if parent.uri = '/' then
      new.uri := parent.uri::varchar
              || item.name::varchar;
    else
      new.uri := parent.uri::varchar
              || '/'::varchar
              || item.name::varchar;
    end if;
  end if;
/*
  raise notice 'new.uri = %', new.uri;
*/  
  return new;
end;
$$ language plpgsql;

create trigger resources_uri__insert_update_tr
    before insert or update on resources for each row
    execute procedure resources_uri__insert_update_tr_fn();

---------------------------------------------------------------------------

select migrations_insert('create resources');

--------------------------------------------------------------------------------
commit;