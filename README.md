# Temas para Radio Android Launcher

Repositorio de temas Premium. La app **no los lleva dentro**: los descarga solo cuando el usuario toca "Descargar".

## Cómo publicarlo (una sola vez)
1. En GitHub crea un repositorio **público** llamado `RadioLauncher-Temas` (rama `main`).
2. Sube el contenido de esta carpeta tal cual: `catalog.json`, `themes/`, `thumbs/`, `video/`.
3. Comprueba que se abre en el navegador:
   `https://raw.githubusercontent.com/RhonnieTucson/RadioLauncher-Temas/main/catalog.json`
4. Si usas otro usuario, otro nombre o otra rama, cambia **una sola línea** en la app:
   `app/src/main/res/values/repo.xml` → `themes_repo_base` (debe terminar en `/`).

## Cómo agregar un tema nuevo (sin actualizar la app)
1. Pon la imagen 1920x1080 (JPG, menos de 3 MB) en `themes/` y una miniatura 480x270 (menos de 300 KB) en `thumbs/`.
   Para un tema animado: video MP4 H.264 en `video/` (menos de 30 MB, sin audio, de 8 a 10 s en bucle) y su imagen fija en `themes/`.
2. Agrega su entrada en `catalog.json`. Los campos `bytes` y `sha256` deben ser los reales del archivo
   (la app rechaza cualquier archivo cuya firma no coincida). Lo más fácil es regenerar todo con
   `tools/construir_repositorio_temas.py` del proyecto de la app.
3. `style` usa los números de tipografía (0 a 19) y color (0 a 7) que ya existen en la app.
4. Haz commit. Los usuarios verán el tema nuevo al abrir la pestaña Temas (o al pulsar "Actualizar lista").

## Notas
- Todo se descarga por HTTPS y se verifica con SHA-256 antes de usarse.
- GitHub guarda en caché los archivos unos minutos: un cambio puede tardar en verse.
- Los archivos de un repositorio público los puede descargar cualquiera que conozca la dirección. El candado Premium
  está en la app (descargar y aplicar exige Premium), no en el servidor.
