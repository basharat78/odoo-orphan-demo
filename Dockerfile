FROM odoo:17.0

COPY ./custom_addons /mnt/extra-addons
COPY ./start.sh /start.sh
RUN chmod +x /start.sh

ENTRYPOINT ["/start.sh"]
