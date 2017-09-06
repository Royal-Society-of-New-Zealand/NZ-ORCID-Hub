/* Create audit log  trigger and all tables: */
CREATE SCHEMA IF NOT EXISTS audit;
CREATE OR REPLACE FUNCTION log_changes() RETURNS TRIGGER AS $$
DECLARE v_sql text;
BEGIN
v_sql := format('INSERT INTO audit.%I SELECT now(), %L, $1.*', 
  TG_TABLE_NAME, left(TG_OP, 1));
IF (TG_OP = 'DELETE') THEN
    EXECUTE v_sql USING OLD;
    RETURN OLD;
ELSIF (TG_OP = 'DELETE' OR TG_OP = 'UPDATE') THEN
    EXECUTE v_sql USING NEW;
    RETURN NEW;
END IF;
RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE r RECORD; v_sql text;
BEGIN
FOR r IN (SELECT table_schema, table_name
FROM information_schema.tables 
WHERE table_catalog = 'orcidhub' AND table_schema = 'public'
  AND table_name IN (
	'user',
	'task',
	'user_org',
	'orcidtoken',
	'organisation',
	'affiliation_record',
	'user_organisation_affiliation',
	'orcid_authorize_call')) LOOP
v_sql := format('CREATE TABLE IF NOT EXISTS audit.%2$I AS 
SELECT NULL::timestamp without time zone AS ts, NULL::char(1) AS op,
 source.* FROM %1$I.%2$I AS source WHERE 1=0;',
 r.table_schema, r.table_name);
RAISE NOTICE 'EXECUTING %', v_sql;
EXECUTE v_sql;
EXECUTE format('DROP TRIGGER IF EXISTS %3$I ON %1$I.%2$I;',
	r.table_schema, r.table_name, r.table_name||'_audit_tr');
v_sql := format('CREATE TRIGGER %3$I
AFTER INSERT OR UPDATE OR DELETE ON %1$I.%2$I
  FOR EACH ROW EXECUTE PROCEDURE log_changes();',
 r.table_schema, r.table_name, r.table_name||'_audit_tr');
RAISE NOTICE 'EXECUTING %', v_sql;
EXECUTE v_sql;
END LOOP;
END;$$;
