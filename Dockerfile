FROM odoo:17.0

COPY ./custom_addons /mnt/extra-addons
COPY --chmod=755 ./start.sh /start.sh

ENTRYPOINT ["/start.sh"]
