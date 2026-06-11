#!/bin/bash
set -e

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
INITIALIZED=$(psql "postgresql://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT:-5432}/${PGDATABASE:-odoo}" \
  -tAc "SELECT COUNT(*) FROM ir_module_module WHERE name='base' AND state='installed';" 2>/dev/null || echo "0")

if [ "$INITIALIZED" = "0" ]; then
  echo "==> First run: initializing database (this takes ~5 min)..."
  odoo $DB_ARGS --init=base,orphan_sponsorship --stop-after-init
  echo "==> Init complete. Starting server..."
else
  echo "==> Database exists. Starting server..."
fi

exec odoo $DB_ARGS --http-port="${PORT:-8069}"
