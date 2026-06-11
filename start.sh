#!/bin/bash
set -e

# If individual PG vars are missing, parse them from DATABASE_URL
if [ -z "$PGHOST" ] && [ -n "$DATABASE_URL" ]; then
  echo "==> Parsing DATABASE_URL..."
  export PGUSER=$(echo "$DATABASE_URL"     | sed -n 's|.*://\([^:]*\):.*|\1|p')
  export PGPASSWORD=$(echo "$DATABASE_URL" | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p')
  export PGHOST=$(echo "$DATABASE_URL"     | sed -n 's|.*@\([^:/]*\).*|\1|p')
  export PGPORT=$(echo "$DATABASE_URL"     | sed -n 's|.*:\([0-9]\+\)/.*|\1|p')
  export PGDATABASE=$(echo "$DATABASE_URL" | sed -n 's|.*/\([^?]*\)|\1|p')
fi

echo "==> Connecting to: ${PGUSER}@${PGHOST}:${PGPORT:-5432}/${PGDATABASE}"

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

# Check if database has already been initialized
INITIALIZED=$(PGPASSWORD="${PGPASSWORD}" psql -h "${PGHOST}" -p "${PGPORT:-5432}" -U "${PGUSER}" -d "${PGDATABASE:-odoo}" \
  -tAc "SELECT COUNT(*) FROM ir_module_module WHERE name='base' AND state='installed';" 2>/dev/null || echo "0")

if [ "$INITIALIZED" = "0" ]; then
  echo "==> First run: initializing database (this takes ~5 min)..."
  odoo $DB_ARGS --init=base,orphan_sponsorship --stop-after-init
  echo "==> Init complete. Starting server..."
else
  echo "==> Database ready. Starting server..."
fi

exec odoo $DB_ARGS --http-port="${PORT:-8069}"
