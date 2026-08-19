# Academia Mirza Cortés

Landing page del preuniversitario PAES Academia Mirza Cortés.

**Producción:** https://academia-mirza-cortes-production.up.railway.app

## Estructura

```
public/        raíz web servida por Caddy (index.html + assets)
brand/         fuentes de marca, no se sirven
tools/         script de generación de assets (ejecución puntual)
Dockerfile     caddy:2-alpine
Caddyfile      binding a $PORT, cache headers, fallback a index.html
railway.json   builder DOCKERFILE
```

El sitio es una sola página autocontenida: HTML, CSS y JS inline. No hay build
step ni dependencias de runtime; sólo las fuentes vienen de Google Fonts.

## Desarrollo local

```bash
docker build -t amc .
docker run --rm -p 8080:8080 -e PORT=8080 amc
# http://localhost:8080
```

## Assets de marca

`brand/logo_mirza.jpeg` es el original: un tile blanco de 765×765 con esquinas
squircle sobre fondo lavanda opaco. Como el header del sitio es púrpura oscuro,
ese fondo tiene que ser transparente, así que los assets web se derivan con:

```bash
python3 tools/build_logo_assets.py    # requiere Pillow y numpy
```

Genera `logo-mark.png` (emblema, para nav y footer), `favicon.ico`,
`apple-touch-icon.png` y `og-image.jpg`. El script es de ejecución puntual: los
resultados están versionados y no forman parte del build.

El lockup completo lleva el nombre de la academia, ilegible a 36 px, y el sitio
ya muestra "Mirza Cortés" como texto vivo — por eso en nav y footer va sólo el
emblema, y el lockup completo se reserva para el `og-image`.

## Deploy

```bash
railway up
```

## Pendientes

- [ ] **El formulario de contacto no envía nada.** `#contactForm` hace
      `preventDefault()`, muestra "✓ Solicitud enviada" y limpia el formulario,
      pero nunca contacta un backend: cada lead se pierde en silencio mientras
      el visitante cree que su solicitud llegó. Es lo más urgente.
- [ ] Reemplazar los placeholders de contacto: `+56 9 0000 0000`,
      `wa.me/56900000000`, `contacto@mirzacortes.cl`.
- [ ] Revisar los tres testimonios, hoy idénticos ("1000 puntos", Medicina PUC).
- [ ] Dominio propio en vez del `*.up.railway.app`. Al cambiarlo hay que
      actualizar `og:url`, `og:image` y `canonical` en `public/index.html`.
