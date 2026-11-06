# -*- coding: utf-8 -*-
"""Arma la carpeta del repositorio de temas (catalog.json, themes/, thumbs/, video/) con sus firmas SHA-256.
Uso: python3 construir_repositorio_temas.py <fondos_dir> <video_dir> <salida_dir>
  fondos_dir : carpeta con los fondos .jpg (salida de generar_fondos_temas.py)
  video_dir  : carpeta con roadlive.mp4 / roadlive_poster.jpg / roadlive_thumb.jpg (salida de generar_tema_carretera.py)"""
import sys, os, json, hashlib, shutil, datetime
from PIL import Image

# estilo = índices de Prefs.FONT_FAMILIES y Prefs.COLORS que ya existen en la app
RELEASE = 2          # número de entrega del repositorio (la app lo ignora; sirve para llevar el control)

THEMES = [
    ("roadlive", "video", "Carretera en Movimiento", "Vas al volante por una carretera de montaña y la calle pasa en movimiento continuo.",
     dict(timeFont=11, clockColor=0, clockBold=True, dateFont=11, infoFont=11, infoColor=1)),
    ("nightdrive", "video", "Noche en la Ciudad", "Avenida iluminada de noche, con luces de neón y reflejos en el pavimento mojado.",
     dict(timeFont=9, clockColor=2, clockBold=False, dateFont=9, infoFont=11, infoColor=6)),
    ("coastdrive", "video", "Ruta de la Costa", "Carretera junto al mar entre palmeras, con cielo azul y olas turquesa.",
     dict(timeFont=11, clockColor=0, clockBold=True, dateFont=11, infoFont=14, infoColor=1)),
    ("mountaindrive", "video", "Ruta de Montaña", "Carretera entre pinos con picos nevados y un lago al fondo.",
     dict(timeFont=10, clockColor=0, clockBold=True, dateFont=11, infoFont=11, infoColor=2)),
    ("carbon", "image", "Carbono Racing", "Fibra de carbono con una franja de luz roja. Reloj Orbitron rojo, de estilo deportivo.",
     dict(timeFont=9, clockColor=5, clockBold=True, dateFont=16, infoFont=10, infoColor=4)),
    ("synthwave", "image", "Neón Synthwave", "Sol retro, rejilla de neón y cielo morado. Tipografía futurista en rosa y cian.",
     dict(timeFont=16, clockColor=6, clockBold=False, dateFont=15, infoFont=15, infoColor=2)),
    ("hud", "image", "Cockpit HUD", "Instrumentos circulares sobre azul oscuro, como la pantalla de un auto deportivo.",
     dict(timeFont=9, clockColor=2, clockBold=False, dateFont=9, infoFont=11, infoColor=2)),
    ("gold", "image", "Lujo Dorado", "Mármol negro con vetas doradas y tipografía clásica. Elegante y sobrio.",
     dict(timeFont=17, clockColor=4, clockBold=False, dateFont=17, infoFont=14, infoColor=0)),
    ("brushed", "image", "Metal Cepillado", "Aluminio oscuro con un filo de luz cian. Letras finas y limpias.",
     dict(timeFont=1, clockColor=0, clockBold=False, dateFont=2, infoFont=2, infoColor=0)),
    ("aurora", "image", "Aurora Boreal", "Cielo estrellado con auroras verdes y moradas. Reloj fino en verde menta.",
     dict(timeFont=1, clockColor=3, clockBold=False, dateFont=2, infoFont=2, infoColor=2)),
    ("roadsunset", "image", "Atardecer en Ruta", "Carretera al atardecer entre colinas moradas y cielo naranja.",
     dict(timeFont=11, clockColor=1, clockBold=False, dateFont=11, infoFont=14, infoColor=4)),
    ("ocean", "image", "Océano Profundo", "Azules profundos con rayos de luz y burbujas. Tranquilo y fresco.",
     dict(timeFont=3, clockColor=2, clockBold=False, dateFont=2, infoFont=2, infoColor=7)),
    ("forest", "image", "Bosque Niebla", "Pinos entre la niebla bajo la luna. Letras suaves en verde.",
     dict(timeFont=2, clockColor=3, clockBold=False, dateFont=5, infoFont=5, infoColor=0)),
    ("dunes", "image", "Desierto", "Dunas al atardecer con letras altas y fuertes en naranja. Para aventura.",
     dict(timeFont=10, clockColor=4, clockBold=True, dateFont=11, infoFont=11, infoColor=0)),
    ("citynight", "image", "Noche Urbana", "Ciudad nocturna con luces desenfocadas. Letras condensadas y modernas.",
     dict(timeFont=11, clockColor=0, clockBold=False, dateFont=11, infoFont=11, infoColor=1)),
]


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(65536), b''):
            h.update(b)
    return h.hexdigest()


def main():
    fondos, video, out = sys.argv[1:4]
    for d in ('themes', 'thumbs', 'video'):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    items = []
    for tid, typ, name, desc, style in THEMES:
        e = dict(id=tid, type=typ, name=name, desc=desc, style=style)
        if typ == 'image':
            src = os.path.join(fondos, tid + '.jpg')
            dst = os.path.join(out, 'themes', tid + '.jpg')
            shutil.copyfile(src, dst)
            thumb = os.path.join(out, 'thumbs', tid + '.jpg')
            Image.open(src).convert('RGB').resize((480, 270), Image.LANCZOS).save(thumb, quality=80, optimize=True)
            e.update(file='themes/%s.jpg' % tid, bytes=os.path.getsize(dst), sha256=sha(dst))
        else:
            vsrc = os.path.join(video, tid + '.mp4')
            psrc = os.path.join(video, tid + '_poster.jpg')
            tsrc = os.path.join(video, tid + '_thumb.jpg')
            vdst = os.path.join(out, 'video', tid + '.mp4')
            pdst = os.path.join(out, 'themes', tid + '.jpg')
            thumb = os.path.join(out, 'thumbs', tid + '.jpg')
            shutil.copyfile(vsrc, vdst)
            shutil.copyfile(psrc, pdst)
            shutil.copyfile(tsrc, thumb)
            e.update(file='video/%s.mp4' % tid, bytes=os.path.getsize(vdst), sha256=sha(vdst),
                     poster='themes/%s.jpg' % tid, posterBytes=os.path.getsize(pdst), posterSha256=sha(pdst))
        e.update(thumb='thumbs/%s.jpg' % tid, thumbBytes=os.path.getsize(thumb), thumbSha256=sha(thumb))
        items.append(e)
    cat = dict(version=1, release=RELEASE, updated=datetime.date.today().isoformat(), themes=items)
    with open(os.path.join(out, 'catalog.json'), 'w', encoding='utf-8') as f:
        json.dump(cat, f, ensure_ascii=False, indent=1)
    print('temas:', len(items))


if __name__ == '__main__':
    main()
