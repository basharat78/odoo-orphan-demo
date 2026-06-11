#!/bin/bash
set -e

# Parse DATABASE_URL using Python if PGHOST is missing
if [ -z "$PGHOST" ] && [ -n "$DATABASE_URL" ]; then
  echo "==> Parsing DATABASE_URL..."
  eval $(python3 -c "
import urllib.parse, os
url = urllib.parse.urlparse(os.environ['DATABASE_URL'])
print('export PGUSER=\"'     + (url.username or '') + '\"')
print('export PGPASSWORD=\"' + (url.password or '') + '\"')
print('export PGHOST=\"'     + (url.hostname or '') + '\"')
print('export PGPORT=\"'     + str(url.port or 5432) + '\"')
print('export PGDATABASE=\"' + url.path.lstrip('/') + '\"')
")
fi

echo "==> DB connection: ${PGUSER}@${PGHOST}:${PGPORT:-5432}/${PGDATABASE}"

if [ -z "$PGHOST" ]; then
  echo "ERROR: PGHOST is empty. Set DATABASE_URL in Railway variables."
  exit 1
fi

# Odoo refuses to run as 'postgres' superuser — create a dedicated odoo user
if [ "$PGUSER" = "postgres" ]; then
  echo "==> Creating dedicated 'odoo' database user..."
  PGPASSWORD="${PGPASSWORD}" psql \
    -h "${PGHOST}" -p "${PGPORT:-5432}" \
    -U "postgres" -d "${PGDATABASE}" <<-SQL 2>/dev/null || true
      DO \$\$
      BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'odoo') THEN
          CREATE USER odoo WITH CREATEDB LOGIN PASSWORD 'odoo_railway_2024';
        END IF;
      END \$\$;
      GRANT ALL PRIVILEGES ON DATABASE "${PGDATABASE}" TO odoo;
      ALTER DATABASE "${PGDATABASE}" OWNER TO odoo;
SQL
  export PGUSER=odoo
  export PGPASSWORD=odoo_railway_2024
  echo "==> Switched to 'odoo' user"
fi

DB_ARGS="
  --db_host=${PGHOST}
  --db_port=${PGPORT:-5432}
  --db_user=${PGUSER}
  --db_password=${PGPASSWORD}
  --database=${PGDATABASE:-odoo}
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons
  --proxy-mode
  --without-demo=all
"

# Check if base is initialized
BASE_INSTALLED=$(PGPASSWORD="${PGPASSWORD}" psql \
  -h "${PGHOST}" -p "${PGPORT:-5432}" \
  -U "${PGUSER}" -d "${PGDATABASE:-odoo}" \
  -tAc "SELECT COUNT(*) FROM ir_module_module WHERE name='base' AND state='installed';" \
  2>/dev/null || echo "0")

# Check if our custom module is installed
MODULE_INSTALLED=$(PGPASSWORD="${PGPASSWORD}" psql \
  -h "${PGHOST}" -p "${PGPORT:-5432}" \
  -U "${PGUSER}" -d "${PGDATABASE:-odoo}" \
  -tAc "SELECT COUNT(*) FROM ir_module_module WHERE name='orphan_sponsorship' AND state='installed';" \
  2>/dev/null || echo "0")

if [ "$BASE_INSTALLED" = "0" ]; then
  echo "==> First run: initializing Odoo database (~5 min)..."
  odoo $DB_ARGS --init=base,orphan_sponsorship --stop-after-init
  echo "==> Done. Starting server..."
elif [ "$MODULE_INSTALLED" = "0" ]; then
  echo "==> Installing orphan_sponsorship module..."
  odoo $DB_ARGS --init=orphan_sponsorship --stop-after-init
  echo "==> Module installed. Starting server..."
else
  echo "==> Database ready. Starting server..."
fi

exec odoo $DB_ARGS --http-port="${PORT:-8069}"
