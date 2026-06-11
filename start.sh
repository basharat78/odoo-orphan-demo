#!/bin/bash
set -e

exec odoo \
  --db_host="${PGHOST}" \
  --db_port="${PGPORT:-5432}" \
  --db_user="${PGUSER}" \
  --db_password="${PGPASSWORD}" \
  --database="${PGDATABASE:-odoo}" \
  --http-port="${PORT:-8069}" \
  --addons-path="/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons" \
  --proxy-mode \
  --without-demo=all \
  --init=base,orphan_sponsorship
