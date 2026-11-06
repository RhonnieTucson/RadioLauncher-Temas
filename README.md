# Temas para Radio Android Launcher (entrega 2)

Repositorio de temas Premium. La app **no los lleva dentro**: los descarga solo cuando el usuario toca "Descargar".
Contiene 15 temas: 11 de fondo fijo y 4 animados ("Carretera en Movimiento", "Noche en la Ciudad", "Ruta de la Costa" y "Ruta de Montaña").

## Cómo publicarlo
1. En GitHub crea un repositorio **público** llamado `RadioLauncher-Temas` (rama `main`). Si ya lo creaste con la entrega 1,
   reemplaza su contenido por esta carpeta completa (sube `catalog.json`, `themes/`, `thumbs/`, `video/` y, si quieres, `herramientas/`).
2. Comprueba que se abre en el navegador:
   `https://raw.githubusercontent.com/RhonnieTucson/RadioLauncher-Temas/main/catalog.json`
3. Si usas otro usuario, otro nombre o otra rama, cambia **una sola línea** en la app:
   `app/src/main/res/values/repo.xml` → `themes_repo_base` (debe terminar en `/`).
4. En la app: pestaña Temas → "Actualizar lista". Los temas nuevos aparecen sin actualizar la app.

## Cómo agregar un tema nuevo
1. Imagen 1920x1080 (JPG, menos de 3 MB) en `themes/` y miniatura 480x270 (menos de 300 KB) en `thumbs/`.
   Tema animado: video MP4 H.264 en `video/` (menos de 30 MB, sin audio, en bucle) y su imagen fija en `themes/`.
2. Agrega su entrada en `catalog.json`. Los campos `bytes` y `sha256` deben ser los reales del archivo
   (la app rechaza cualquier archivo cuya firma no coincida). Lo más fácil es regenerar todo con
   `herramientas/construir_repositorio_temas.py` (agrega el tema a su lista `THEMES`).
3. `style` usa los números de tipografía (0 a 19) y color (0 a 7) que ya existen en la app.

## Temas animados desde un GIF o video
Con `herramientas/convertir_gif_a_tema.py` se convierte un GIF corto de carretera en un tema animado
(interpola a 24 fps, escala a 1280x720, cierra el bucle con un fundido corto y genera el MP4, el póster y la miniatura):

    python3 herramientas/convertir_gif_a_tema.py mi.gif mi_tema carpeta_salida

Después se agrega a la lista `THEMES` de `construir_repositorio_temas.py` y se vuelve a generar el repositorio.

**Calidad del original:** un GIF de 550x310 px y 4 cuadros por segundo se ve suave tras la interpolación, pero algo blando en una
pantalla grande. Lo ideal es partir de un video MP4 de 1280x720 o más y 15 cuadros por segundo o más; ahí el resultado es mucho mejor.

## Notas
- Todo se descarga por HTTPS y se verifica con SHA-256 antes de usarse.
- GitHub guarda en caché los archivos unos minutos: un cambio puede tardar en verse.
- Los archivos de un repositorio público los puede descargar cualquiera que conozca la dirección. El candado Premium
  está en la app (descargar y aplicar exige Premium), no en el servidor.
- Sube solo material del que tengas derechos de uso: un repositorio público lo puede ver y copiar cualquiera.
