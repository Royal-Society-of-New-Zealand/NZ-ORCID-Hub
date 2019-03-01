/* Create audit log  trigger and all tables: */
CREATE SCHEMA IF NOT EXISTS audit;

CREATE OR REPLACE FUNCTION log_changes() RETURNS TRIGGER AS $$
DECLARE v_sql text;
BEGIN
	v_sql := format('INSERT INTO audit.%I SELECT now(), %L, $1.*',
		TG_TABLE_NAME, left(TG_OP, 1));
	-- store only "old" value. The "new" value is the current record:
	IF TG_OP = 'DELETE' OR TG_OP = 'UPDATE' THEN
		EXECUTE v_sql USING OLD;
		RETURN OLD;
	END IF;
	RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TABLE IF EXISTS audit.orcid_api_call;
DROP TABLE IF EXISTS audit.orcid_authorize_call;
DROP TABLE IF EXISTS audit.task;

DROP TRIGGER IF EXISTS orcid_authorize_call_audit_delete_tr ON orcid_authorize_call;
DROP TRIGGER IF EXISTS orcid_authorize_call_audit_update_tr ON orcid_authorize_call;

DROP TRIGGER IF EXISTS orcid_api_call_audit_delete_tr ON orcid_api_call;
DROP TRIGGER IF EXISTS orcid_api_call_audit_update_tr ON orcid_api_call;

DROP TRIGGER IF EXISTS task_delete_tr ON task;
DROP TRIGGER IF EXISTS task_update_tr ON task;

DO $$
DECLARE r RECORD; v_sql text;
BEGIN
	FOR r IN (SELECT  tablename, schemaname, tableowner
		FROM pg_tables
		WHERE schemaname= 'public'
		AND tablename IN (
			'user',
			'user_org',
			'orcidtoken',
			'organisation',
			'affiliation_record',
			'user_organisation_affiliation',
			'task',
			'client')) LOOP
	v_sql := format('CREATE TABLE IF NOT EXISTS audit.%2$I AS
		SELECT NULL::timestamp without time zone AS ts, NULL::char(1) AS op,
		source.* FROM %1$I.%2$I AS source WHERE 1=0;
		ALTER TABLE audit.%2$I OWNER TO %3$I;',
		r.schemaname, r.tablename, r.tableowner);
		RAISE NOTICE 'EXECUTING %', v_sql;
		EXECUTE v_sql;
		EXECUTE format('DROP TRIGGER IF EXISTS %3$I ON %1$I.%2$I;',
			r.schemaname, r.tablename, r.tablename||'_audit_update_tr');
		v_sql := format('CREATE TRIGGER %3$I
			AFTER UPDATE ON %1$I.%2$I
			FOR EACH ROW
			WHEN (OLD.* IS DISTINCT FROM NEW.*)
			EXECUTE PROCEDURE log_changes();',
			r.schemaname, r.tablename, r.tablename||'_audit_update_tr');
		RAISE NOTICE 'EXECUTING %', v_sql;
		EXECUTE v_sql;
		EXECUTE format('DROP TRIGGER IF EXISTS %3$I ON %1$I.%2$I;',
			r.schemaname, r.tablename, r.tablename||'_audit_delete_tr');
		v_sql := format('CREATE TRIGGER %3$I
			AFTER DELETE ON %1$I.%2$I
			FOR EACH ROW
			EXECUTE PROCEDURE log_changes();',
			r.schemaname, r.tablename, r.tablename||'_audit_delete_tr');
		RAISE NOTICE 'EXECUTING %', v_sql;
		EXECUTE v_sql;
	END LOOP;
END;
$$;
