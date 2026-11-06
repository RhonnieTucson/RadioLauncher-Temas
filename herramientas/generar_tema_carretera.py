# -*- coding: utf-8 -*-
"""Genera el tema animado "Carretera en Movimiento" (vista desde el parabrisas) como video MP4 en bucle perfecto.
Uso: python3 generar_tema_carretera.py <carpeta_salida> [--prueba]
Crea: roadlive.mp4 (1280x720, 24 fps, 10 s, sin audio), roadlive_poster.jpg (1920x1080) y roadlive_thumb.jpg (480x270).
Todo se dibuja con código (sin fotos de terceros)."""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

FPS = 24
SECONDS = 10
FRAMES = FPS * SECONDS
LOOP_DIST = 180.0           # metros recorridos en un ciclo = 15 periodos de raya (12 m) -> bucle perfecto
PERIOD = 12.0
HAZE = np.array([200, 217, 230], np.float32)


class Scene:
    def __init__(self, W, H):
        self.W, self.H = W, H
        rng = np.random.default_rng(7)
        self.xs = np.arange(W, dtype=np.float32)
        self.ys = np.arange(H, dtype=np.float32)
        self.F = 0.70 * W                         # distancia focal en píxeles
        self.cam_h = 1.35
        # tablas de ruido de la hierba (periódicas en z)
        self.t1 = rng.random((8, 96)).astype(np.float32)      # celdas de 1,5 m
        self.t2 = rng.random((16, 96)).astype(np.float32)     # celdas de 0,75 m
        self.t3 = rng.random((24, 96)).astype(np.float32)     # celdas de 0,5 m (asfalto)
        self.sky = self._sky()
        self.clouds = self._clouds(rng)
        self.far, self.near = self._mountains(rng)
        self.bush_x = [(-9.5, 6), (8.0, 11), (-12.5, 4), (10.5, 8), (-7.0, 9), (13.0, 3)]
        self.rng = rng

    # ---------------------------------------------------------------- cielo y nubes
    def _sky(self):
        H, W = self.H, self.W
        t = np.clip(self.ys / (0.46 * H), 0, 1)[:, None, None]
        top = np.array([62, 130, 200], np.float32)
        hor = np.array([190, 221, 242], np.float32)
        return np.broadcast_to(top * (1 - t) + hor * t, (H, W, 3)).copy()

    def _clouds(self, rng):
        W, H = self.W, int(self.H * 0.46)
        tw = W // 4
        yy, xx = np.mgrid[0:H, 0:3 * tw].astype(np.float32)
        dens = np.zeros((H, 3 * tw), np.float32)
        for _ in range(11):                                    # nubes grandes; cada una repetida en las 3 copias
            cx = rng.uniform(0, tw)
            cy = rng.uniform(0.10, 0.60) * H
            r = rng.uniform(0.05, 0.10) * H * (1 + 0.6 * (cy / H))
            puffs = [(rng.normal(0, r * 1.1), rng.normal(-r * 0.25, r * 0.30), rng.uniform(0.55, 1.0)) for _ in range(9)]
            for rep in range(3):
                for ox, oy, k in puffs:
                    px = cx + rep * tw + ox
                    py = cy + oy
                    rr = r * k
                    dens += np.exp(-(((xx - px) / (rr * 1.25)) ** 2 + ((yy - py) / (rr * 0.85)) ** 2) * 1.15)
        dens = np.asarray(Image.fromarray(np.clip(dens / dens.max() * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2))).astype(np.float32) / 255
        dens = dens[:, tw:2 * tw]                              # el tramo central es periódico
        alpha = np.clip((dens - 0.26) * 3.2, 0, 1) ** 1.05
        gy = np.gradient(dens, axis=0)
        shade = np.clip(0.55 + gy * 7.0 + (dens - 0.5) * 0.25, 0, 1)   # arriba claro, abajo gris azulado
        return np.tile(alpha, (1, 4)), np.tile(shade, (1, 4))

    # ---------------------------------------------------------------- montañas
    def _mountains(self, rng):
        W = self.W
        x = np.arange(W, dtype=np.float32) / W

        def ridge(seeds, amp):
            r = np.zeros(W, np.float32)
            for k, (f, ph, a) in enumerate(seeds):
                r += a * np.sin(2 * math.pi * f * x + ph)
            return r

        env = 0.30 + 0.70 * (np.abs(2 * x - 1) ** 1.15)
        far = (ridge([(2, 0.4, 1.0), (5, 1.1, 0.55), (11, 2.3, 0.22), (23, 0.7, 0.08)], 1) * 0.5 + 0.7) * env
        near = (ridge([(3, 2.2, 1.0), (7, 0.3, 0.45), (15, 1.9, 0.18), (31, 0.2, 0.06)], 1) * 0.5 + 0.7) * env * 0.8
        snown = 0.5 + 0.5 * np.sin(2 * math.pi * (x * 37) + 1.0) * np.sin(2 * math.pi * (x * 13) + 0.3)
        return (far, snown), (near, snown)

    def _draw_mountains(self, img, yh):
        H, W = self.H, self.W
        for (rid, snown), col, scale, snow in ((self.far, np.array([132, 156, 184], np.float32), 0.20, True),
                                               (self.near, np.array([98, 115, 134], np.float32), 0.15, False)):
            top = yh - rid * scale * H                         # fila de la cresta por columna
            rows = self.ys[:, None]
            m = (rows >= top[None, :]) & (rows <= yh + 3)
            depth = np.clip((rows - top[None, :]) / (scale * H), 0, 1.5)
            c = col[None, None, :] * (1.0 - 0.18 * depth[:, :, None])
            c = c * 0.85 + HAZE[None, None, :] * 0.15 * (1 - np.clip(depth, 0, 1))[:, :, None] * 0 + 0
            # neblina hacia la base
            hz = np.clip(1 - (yh - rows) / (scale * H * 0.9), 0, 1)[:, :, None] * 0.55
            c = c * (1 - hz) + HAZE[None, None, :] * hz
            if snow:
                thick = (0.16 + 0.22 * snown) * scale * H
                sm = (rows - top[None, :]) < thick[None, :]
                lit = np.clip(1.0 - (rows - top[None, :]) / np.maximum(thick[None, :], 1), 0, 1)[:, :, None]
                snowc = np.array([236, 242, 248], np.float32)[None, None, :]
                c = np.where(sm[:, :, None], c * (1 - lit * 0.85) + snowc * lit * 0.85, c)
            img[:] = np.where(m[:, :, None], c, img)

    # ---------------------------------------------------------------- suelo en perspectiva
    def _ground(self, img, yh, cx, s):
        H, W, F = self.H, self.W, self.F
        y0 = int(math.floor(yh)) + 1
        rows = self.ys[y0:]
        d = np.maximum(rows - yh, 0.6)
        z = F * self.cam_h / d                                  # distancia hacia adelante (m)
        xw = (self.xs[None, :] - cx) * z[:, None] / F           # posición lateral (m)
        Zw = z[:, None] + s                                      # coordenada del mundo a lo largo de la ruta
        ax = np.abs(xw)

        def tex(table, cz, cxs):
            fz = Zw / cz
            fx = xw / cxs
            z0 = np.floor(fz)
            x0 = np.floor(fx)
            tz = fz - z0
            tx = fx - x0
            tz = tz * tz * (3 - 2 * tz)
            tx = tx * tx * (3 - 2 * tx)
            nz, nx = table.shape
            iz0 = z0.astype(np.int64) % nz
            iz1 = (iz0 + 1) % nz
            ix0 = x0.astype(np.int64) % nx
            ix1 = (ix0 + 1) % nx
            a = table[iz0, ix0] * (1 - tx) + table[iz0, ix1] * tx
            b = table[iz1, ix0] * (1 - tx) + table[iz1, ix1] * tx
            return a * (1 - tz) + b * tz

        n1 = tex(self.t1, 1.5, 1.2)
        n2 = tex(self.t2, 0.75, 0.9)
        grass_a = np.array([176, 142, 86], np.float32)
        grass_b = np.array([128, 104, 62], np.float32)
        g = grass_a[None, None, :] * (1 - n1[:, :, None]) + grass_b[None, None, :] * n1[:, :, None]
        g = g + ((n2 - 0.5) * 34)[:, :, None]
        g = g * (0.92 + 0.08 * np.sin(xw * 1.7))[:, :, None]     # vetas paralelas a la ruta
        # grava del arcén
        n3 = tex(self.t3, 0.5, 0.5)
        gravel = (np.array([150, 146, 138], np.float32)[None, None, :] + ((n3 - 0.5) * 26)[:, :, None])
        g = np.where(((ax > 3.65) & (ax < 5.1))[:, :, None], gravel, g)
        # asfalto
        asph = np.array([94, 96, 101], np.float32)[None, None, :] + ((n3 - 0.5) * 9)[:, :, None]
        tracks = np.exp(-(((ax - 1.15) / 0.38) ** 2)) * 7        # huellas de las llantas
        asph = asph - tracks[:, :, None]
        road = ax < 3.65
        g = np.where(road[:, :, None], asph, g)
        # líneas: bordes blancos y rayas amarillas centrales
        edge = (np.abs(ax - 3.38) < 0.085)
        g = np.where(edge[:, :, None], np.array([232, 232, 226], np.float32)[None, None, :], g)
        dash = (ax < 0.1) & ((Zw % PERIOD) < 4.6)
        g = np.where(dash[:, :, None], np.array([236, 192, 60], np.float32)[None, None, :], g)
        # distancia: neblina atmosférica
        f = (1 - np.exp(-z / 95.0))[:, None, None]
        far_col = np.array([168, 184, 200], np.float32)
        g = g * (1 - f * 0.9) + far_col[None, None, :] * f * 0.9
        img[y0:] = g

    # ---------------------------------------------------------------- postes y arbustos
    def _props(self, img, yh, cx, s):
        H, W, F = self.H, self.W, self.F
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        items = []
        for k in range(10):                                      # postes de cerca cada 18 m
            z = (k * 18.0 - s) % LOOP_DIST
            if 3.0 < z < 160:
                for side in (-1, 1):
                    items.append((z, 'post', side * 5.7, 0))
        for k in range(3):                                       # arbustos cada 60 m
            for j, (bx, ph) in enumerate(self.bush_x[k * 2:k * 2 + 2]):
                z = ((k * 60.0 + ph * 7.0) - s) % LOOP_DIST
                if 4.0 < z < 170:
                    items.append((z, 'bush', bx, j))
        items.sort(key=lambda t: -t[0])                          # primero lo lejano
        for z, kind, x, j in items:
            sc = F / z
            xb = cx + x * sc
            yb = yh + self.cam_h * sc
            al = int(255 * np.clip((150 - z) / 70.0, 0, 1))
            if al <= 0:
                continue
            if kind == 'post':
                h, w = 1.2 * sc, max(1.0, 0.16 * sc)
                col = (74, 56, 40, al)
                d.rectangle([xb - w / 2, yb - h, xb + w / 2, yb], fill=col)
                d.rectangle([xb - w * 1.4, yb - h, xb + w * 1.4, yb - h + max(1, 0.08 * sc)], fill=(60, 44, 30, al))
            else:
                w, h = 1.9 * sc, 0.95 * sc
                base = (104, 100, 58) if j == 0 else (88, 98, 60)
                d.ellipse([xb - w / 2, yb - h, xb + w / 2, yb + h * 0.18], fill=base + (al,))
                d.ellipse([xb - w * 0.32, yb - h * 0.95, xb + w * 0.30, yb - h * 0.25], fill=(base[0] + 22, base[1] + 22, base[2] + 12, al))
        lay = lay.filter(ImageFilter.GaussianBlur(0.6))
        a = np.asarray(lay).astype(np.float32)
        alpha = a[:, :, 3:4] / 255.0
        img[:] = img * (1 - alpha) + a[:, :, :3] * alpha

    # ---------------------------------------------------------------- tablero
    def _dashboard(self, img):
        H, W = self.H, self.W
        x = self.xs / W
        top = H * (0.905 - 0.03 * np.sin(np.pi * x) ** 1.6)
        rows = self.ys[:, None]
        m = rows >= top[None, :]
        t = np.clip((rows - top[None, :]) / (H * 0.1), 0, 1)
        col = np.array([34, 36, 41], np.float32)[None, None, :] * (1 - t[:, :, None]) + np.array([9, 9, 11], np.float32)[None, None, :] * t[:, :, None]
        glare = np.clip(1 - (rows - top[None, :]) / (H * 0.018), 0, 1)[:, :, None] * 0.35
        col = col * (1 - glare) + np.array([150, 176, 204], np.float32)[None, None, :] * glare
        img[:] = np.where(m[:, :, None], col, img)

    # ---------------------------------------------------------------- fotograma
    def frame(self, u):
        H, W = self.H, self.W
        yh0 = 0.462 * H
        yh = yh0 + 0.0011 * H * math.sin(2 * math.pi * 7 * u) + 0.0006 * H * math.sin(2 * math.pi * 13 * u + 1.3)
        cx = 0.5 * W + 0.002 * W * math.sin(2 * math.pi * 3 * u)
        s = u * LOOP_DIST
        img = self.sky.copy()
        # nubes (se desplazan despacio; un ciclo = un cuarto del ancho)
        a, sh = self.clouds
        sh_px = int(round(u * (W // 4)))
        a = np.roll(a, -sh_px, axis=1)
        sh = np.roll(sh, -sh_px, axis=1)
        hs = a.shape[0]
        al = a[:, :, None]
        lit = np.array([255, 255, 255], np.float32)[None, None, :]
        dark = np.array([168, 186, 210], np.float32)[None, None, :]
        cloud_col = dark * (1 - sh[:, :, None]) + lit * sh[:, :, None]
        img[:hs] = img[:hs] * (1 - al * 0.97) + cloud_col * al * 0.97
        glow = np.exp(-(((self.xs[None, :] - 0.80 * W) / (0.26 * W)) ** 2 + ((self.ys[:, None] - 0.06 * H) / (0.22 * H)) ** 2))
        img += glow[:, :, None] * np.array([34, 30, 16], np.float32)[None, None, :]
        self._draw_mountains(img, yh)
        self._ground(img, yh, cx, s)
        self._props(img, yh, cx, s)
        # parabrisas: banda superior tintada y viñeta suave
        t = np.clip(1 - self.ys / (0.1 * H), 0, 1)[:, None, None] * 0.30
        img = img * (1 - t) + np.array([22, 44, 78], np.float32)[None, None, :] * t
        self._dashboard(img)
        v = 1 - 0.30 * np.clip(np.sqrt(((self.xs[None, :] / W - 0.5) * 1.15) ** 2 + (self.ys[:, None] / H - 0.5) ** 2) * 1.35, 0, 1) ** 2.4
        img = img * v[:, :, None]
        return np.clip(img, 0, 255).astype(np.uint8)


def main():
    out = sys.argv[1]
    test = '--prueba' in sys.argv
    os.makedirs(out, exist_ok=True)
    if test:
        sc = Scene(1280, 720)
        for u in (0.0, 0.5):
            Image.fromarray(sc.frame(u)).save(os.path.join(out, 'prueba_%02d.jpg' % int(u * 100)), quality=88)
        print('pruebas listas')
        return
    import imageio
    sc = Scene(1280, 720)
    path = os.path.join(out, 'roadlive.mp4')
    w = imageio.get_writer(path, fps=FPS, codec='libx264', quality=None, macro_block_size=None,
                           ffmpeg_params=['-crf', '27', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-profile:v', 'main',
                                          '-level', '4.0', '-movflags', '+faststart', '-an'])
    for i in range(FRAMES):
        w.append_data(sc.frame(i / FRAMES))
        if i % 48 == 0:
            print('fotograma', i, '/', FRAMES, flush=True)
    w.close()
    big = Scene(1920, 1080)
    Image.fromarray(big.frame(0.0)).save(os.path.join(out, 'roadlive_poster.jpg'), quality=84, optimize=True, progressive=True)
    Image.fromarray(big.frame(0.0)).resize((480, 270), Image.LANCZOS).save(os.path.join(out, 'roadlive_thumb.jpg'), quality=82, optimize=True)
    print('listo:', os.path.getsize(path) // 1024, 'KB')


if __name__ == '__main__':
    main()
