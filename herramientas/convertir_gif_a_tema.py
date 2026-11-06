# -*- coding: utf-8 -*-
"""Convierte un GIF corto de carretera en un tema animado (MP4 en bucle + póster + miniatura).
Uso: python3 convertir_gif_a_tema.py <entrada.gif> <id_del_tema> <carpeta_salida> [ciclos]
Pasos: (1) repite el ciclo del GIF 3 veces y lo interpola a 24 fps con compensación de movimiento (los GIF suelen
ir a 4 fps y se verían entrecortados); (2) toma el ciclo central, que ya incluye el paso de la última imagen a la primera;
(3) lo escala a 1280x720 con Lanczos y realce suave; (4) repite el ciclo [ciclos] veces para que el reinicio del
reproductor ocurra pocas veces; (5) codifica H.264 sin audio."""
import sys, os, shutil, subprocess, tempfile
import numpy as np
from PIL import Image, ImageSequence, ImageFilter
import imageio, imageio_ffmpeg

FPS = 24
W, H = 1280, 720


def main():
    gif, tid, out = sys.argv[1:4]
    cycles = int(sys.argv[4]) if len(sys.argv) > 4 else 0     # 0 = repetir hasta cubrir unos 8 s
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs(out, exist_ok=True)
    im = Image.open(gif)
    frames = [f.convert('RGB').copy() for f in ImageSequence.Iterator(im)]
    durs = []
    for i in range(im.n_frames):
        im.seek(i)
        durs.append(im.info.get('duration', 250))
    in_fps = 1000.0 / (sum(durs) / len(durs))
    n_in = len(frames)
    step = int(round(FPS / in_fps))                         # fotogramas de salida por cada paso del GIF (24 / 4 = 6)
    tmp = tempfile.mkdtemp()
    pad = 3
    seq = [frames[0]] * pad + frames + [frames[-1]] * pad   # se repiten los extremos para que el interpolador no pierda los bordes
    for i, f in enumerate(seq):
        f.save(os.path.join(tmp, 'i%03d.png' % i))
    r = subprocess.run([exe, '-y', '-loglevel', 'error', '-framerate', '%.4f' % in_fps, '-i', os.path.join(tmp, 'i%03d.png'),
                        '-vf', 'minterpolate=fps=%d:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1' % FPS,
                        os.path.join(tmp, 'o%04d.png')], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    outs = sorted(f for f in os.listdir(tmp) if f.startswith('o'))
    arr = [np.asarray(Image.open(os.path.join(tmp, f)).convert('RGB')).astype(np.int16) for f in outs]
    # localizar el fotograma original del medio y, a partir de él, el primero y el último (se comprueba que coinciden)
    mid = n_in // 2
    ref_mid = np.asarray(frames[mid]).astype(np.int16)
    kmid = min(range(len(arr)), key=lambda k: np.abs(arr[k] - ref_mid).mean())
    k0 = kmid - mid * step
    k1 = k0 + (n_in - 1) * step
    errs = [float(np.abs(arr[k0 + i * step] - np.asarray(frames[i]).astype(np.int16)).mean()) for i in range(n_in)]
    print('originales encontrados en su sitio (error medio %.2f, peor %.2f)' % (sum(errs) / len(errs), max(errs)))
    if k0 < 0 or k1 >= len(arr) or max(errs) > 3.0:
        raise SystemExit('No se pudo alinear la interpolación con los fotogramas originales')
    src = [outs[k] for k in range(k0, k1 + 1)]               # clip lineal interpolado: (n_in-1)*step+1 fotogramas
    N = len(src)

    def load(i):
        return np.asarray(Image.open(os.path.join(tmp, src[i])).convert('RGB')).astype(np.float32)

    # bucle: los K primeros fotogramas son un fundido del final del clip hacia su principio, así no hay salto
    K = 6
    frames_loop = []
    for j in range(K):
        al = (j + 1) / (K + 1.0)
        frames_loop.append((1 - al) * load(N - K + j) + al * load(j))
    for i in range(K, N - K):
        frames_loop.append(load(i))
    per_cycle = len(frames_loop)
    print('ciclo: %d fotogramas (%.2f s)' % (per_cycle, per_cycle / FPS))
    cyc = ['loop%03d.png' % i for i in range(per_cycle)]
    for name, fr in zip(cyc, frames_loop):
        Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8)).save(os.path.join(tmp, name))

    def up(path, size=(W, H)):
        img = Image.open(path).convert('RGB').resize(size, Image.LANCZOS)
        return img.filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2))

    ups = [np.asarray(up(os.path.join(tmp, f))) for f in cyc]
    path = os.path.join(out, tid + '.mp4')
    w = imageio.get_writer(path, fps=FPS, codec='libx264', quality=None, macro_block_size=None,
                           ffmpeg_params=['-crf', '27', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-profile:v', 'main',
                                          '-level', '4.0', '-movflags', '+faststart', '-an'])
    if cycles <= 0:
        cycles = max(1, int(round(8.0 * FPS / per_cycle)))
    for _ in range(cycles):
        for fr in ups:
            w.append_data(fr)
    w.close()
    first = os.path.join(tmp, src[N // 2])                  # póster: un fotograma original (sin fundido)
    up(first, (1920, 1080)).save(os.path.join(out, tid + '_poster.jpg'), quality=84, optimize=True, progressive=True)
    up(first, (480, 270)).save(os.path.join(out, tid + '_thumb.jpg'), quality=82, optimize=True)
    # muestras del punto del bucle (últimos 3 y primeros 3 fotogramas del ciclo) para revisarlas
    Image.fromarray(np.concatenate([np.concatenate([ups[-3 + i][::3, ::3] for i in range(3)], 1),
                                    np.concatenate([ups[i][::3, ::3] for i in range(3)], 1)], 0)).save(os.path.join(out, tid + '_bucle.jpg'), quality=85)
    shutil.rmtree(tmp, ignore_errors=True)
    print(tid, '->', os.path.getsize(path) // 1024, 'KB,', cycles * per_cycle / FPS, 's')


if __name__ == '__main__':
    main()
