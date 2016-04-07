-- users_roles

begin;

insert into roles (id) values ('admin'), ('reader');
alter table users add column role_id varchar default 'reader' references roles(id) on delete set null on update cascade;

select migrations_insert('users_roles create');

commit;