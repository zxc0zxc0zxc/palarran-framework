-- Executed once by the official PostgreSQL entrypoint on an EMPTY data volume.
-- psql quotes the variable as an SQL literal; the password is never passed in argv.
\set app_password `cat /run/secrets/db_password`
CREATE ROLE app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD :'app_password';
CREATE DATABASE app OWNER app;
