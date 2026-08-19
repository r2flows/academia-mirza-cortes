# Sitio estatico: no hay build step, solo Caddy sirviendo public/.
# La imagen base ya trae el CMD correcto (caddy run --config /etc/caddy/Caddyfile).
FROM caddy:2-alpine

COPY Caddyfile /etc/caddy/Caddyfile
COPY public/ /srv/

EXPOSE 8080
