#!/bin/bash
set -e

# Parse DATABASE_URL using Python if PGHOST is missing
if [ -z "$PGHOST" ] && [ -n "$DATABASE_URL" ]; then
  echo "==> Parsing DATABASE_URL..."
  eval $(python3 -c "
import urllib.parse, os
url = urllib.parse.urlparse(os.environ['DATABASE_URL'])
print('export PGUSER=\"'  + (url.username or '') + '\"')
print('export PGPASSWORD=\"' + (url.password or '') + '\"')
print('export PGHOST=\"'  + (url.hostname or '') + '\"')
print('export PGPORT=\"'  + str(url.port or 5432) + '\"')
print('export PGDATABASE=\"' + url.path.lstrip('/') + '\"')
")
fi

echo "==> DB connection: ${PGUSER}@${PGHOST}:${PGPORT:-5432}/${PGDATABASE:-odoo}"

if [ -z "$PGHOST" ]; then
  echo "ERROR: PGHOST is still empty. DATABASE_URL or PGHOST must be set."
  exit 1
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

# Check if already initialized
INITIALIZED=$(PGPASSWORD="${PGPASSWORD}" psql \
  -h "${PGHOST}" -p "${PGPORT:-5432}" \
  -U "${PGUSER}" -d "${PGDATABASE:-odoo}" \
  -tAc "SELECT COUNT(*) FROM ir_module_module WHERE name='base' AND state='installed';" \
  2>/dev/null || echo "0")

if [ "$INITIALIZED" = "0" ]; then
  echo "==> First run: initializing Odoo database (~5 min)..."
  odoo $DB_ARGS --init=base,orphan_sponsorship --stop-after-init
  echo "==> Done. Starting server..."
else
  echo "==> Database ready. Starting server..."
fi

exec odoo $DB_ARGS --http-port="${PORT:-8069}"
