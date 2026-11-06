# -*- coding: utf-8 -*-
"""Genera los fondos de los temas Premium (1920x1080, JPEG). Uso: python3 gen_themes.py <carpeta_salida>"""
import sys, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080
rng = np.random.default_rng(2026)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
X = xx / W
Y = yy / H


def to_img(a):
    a = np.clip(a, 0, 255).astype(np.uint8)
    if a.ndim == 3 and a.shape[2] == 1:
        a = a[:, :, 0]
    return Image.fromarray(a)


def blur(a, r):
    return np.asarray(to_img(a).filter(ImageFilter.GaussianBlur(r))).astype(np.float32)


def vgrad(stops):
    """stops: [(pos 0..1, (r,g,b)), ...] gradiente vertical."""
    out = np.zeros((H, W, 3), np.float32)
    ps = [s[0] for s in stops]
    for c in range(3):
        col = np.interp(Y[:, 0], ps, [s[1][c] for s in stops])
        out[:, :, c] = col[:, None]
    return out


def glow(cx, cy, r, color, strength=1.0, power=2.0):
    d = np.sqrt((xx - cx * W) ** 2 + (yy - cy * H) ** 2) / (r * H)
    m = np.clip(1 - d, 0, 1) ** power * strength
    return m[:, :, None] * np.array(color, np.float32)[None, None, :]


def vignette(a, strength=0.55, left=0.35):
    d = np.sqrt(((X - 0.5) * 1.1) ** 2 + (Y - 0.5) ** 2)
    v = 1 - strength * np.clip(d * 1.25, 0, 1) ** 2.2
    l = 1 - left * np.clip(1 - X / 0.45, 0, 1)      # zona del reloj (izquierda) más calmada y oscura
    b = 1 - 0.25 * np.clip((Y - 0.78) / 0.22, 0, 1)  # la barra inferior se lee mejor
    return a * (v * l * b)[:, :, None]


def stars(a, n=260, maxy=0.55):
    layer = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(layer)
    for _ in range(n):
        x = rng.uniform(0, W)
        y = rng.uniform(0, H * maxy)
        r = rng.choice([1, 1, 1, 2])
        b = int(rng.uniform(90, 255))
        d.ellipse([x - r, y - r, x + r, y + r], fill=b)
    s = np.asarray(layer.filter(ImageFilter.GaussianBlur(0.7))).astype(np.float32)
    return a + s[:, :, None] * 0.9


def save(a, name, out):
    img = to_img(a)
    img.save(os.path.join(out, name + ".jpg"), quality=84, optimize=True, progressive=True)


def lines_layer(draw_fn, color_blur=6, core=1.0, halo=1.0):
    """Dibuja con PIL sobre una capa negra y devuelve (núcleo, halo) como arreglos."""
    lay = Image.new("RGB", (W, H), (0, 0, 0))
    draw_fn(ImageDraw.Draw(lay))
    core_a = np.asarray(lay).astype(np.float32)
    halo_a = blur(core_a, color_blur)
    return core_a * core, halo_a * halo


# ---------------------------------------------------------------- 1 carbono
def carbon(out):
    c = 8
    cx = (xx // c).astype(np.int32)
    cy = (yy // c).astype(np.int32)
    pat = ((cx + cy) % 2).astype(np.float32)
    fx = (xx % c) / c
    fy = (yy % c) / c
    fiber = np.where(pat > 0, fx, fy)
    base = 20 + 22 * pat + 14 * fiber
    sheen = 0.55 + 0.45 * np.sin((xx + yy) / 260.0)
    g = base * (0.7 + 0.6 * sheen)
    a = np.stack([g, g, g * 1.04], -1)
    # banda de luz roja en diagonal
    d = np.abs((xx * 0.42 + yy) - (H * 0.95 + W * 0.18))
    band = np.exp(-(d / 70.0) ** 2) * 0.9
    a += band[:, :, None] * np.array([210, 20, 30], np.float32)[None, None, :]
    a += blur(band[:, :, None] * np.array([255, 40, 50], np.float32)[None, None, :], 40) * 0.8
    d2 = np.abs((xx * 0.42 + yy) - (H * 0.95 + W * 0.18 + 120))
    a += (np.exp(-(d2 / 5.0) ** 2) * 0.7)[:, :, None] * np.array([255, 90, 90], np.float32)[None, None, :]
    save(vignette(a, 0.5, 0.45), "carbon", out)


# ---------------------------------------------------------------- 2 synthwave
def synthwave(out):
    hz = 0.56
    a = vgrad([(0, (8, 0, 34)), (0.25, (46, 6, 86)), (0.45, (150, 24, 120)), (hz, (255, 90, 120))])
    below = Y > hz
    floor = vgrad([(hz, (40, 4, 70)), (1, (6, 0, 22))])
    a = np.where(below[:, :, None], floor, a)
    a = stars(a, 300, 0.4)
    # sol
    scx, scy, sr = 0.68 * W, 0.40 * H, 0.2 * H
    d = np.sqrt((xx - scx) ** 2 + (yy - scy) ** 2)
    sun = np.clip((sr - d) / 3.0, 0, 1)
    t = np.clip((yy - (scy - sr)) / (2 * sr), 0, 1)
    sun_col = np.stack([255 * np.ones_like(t), 230 - 200 * t, 60 + 130 * t], -1)
    slit = np.ones_like(yy)
    for k in range(9):
        y0 = scy - sr + 2 * sr * (0.42 + k * 0.065)
        th = 2 + k * 2.4
        slit = np.where((yy > y0) & (yy < y0 + th), 0, slit)
    a = a * (1 - (sun * slit)[:, :, None]) + sun_col * (sun * slit)[:, :, None]
    a += glow(0.68, 0.40, 0.55, (255, 70, 150), 0.55, 2.2)
    # rejilla en perspectiva
    def draw(dr):
        vx = 0.68 * W
        hy = hz * H
        for i in range(-30, 31):
            x_bottom = vx + i * 150
            dr.line([(vx, hy), (x_bottom, H)], fill=(0, 220, 255), width=2)
        t = 0.0
        for k in range(1, 22):
            yv = hy + (H - hy) * (k / 21.0) ** 2.2
            dr.line([(0, yv), (W, yv)], fill=(255, 40, 190), width=2)
    core, halo = lines_layer(draw, 5, 0.85, 1.4)
    mask = (Y > hz)[:, :, None]
    fade = np.clip((Y - hz) / 0.1, 0, 1)[:, :, None]
    a += (core + halo) * mask * fade
    a += glow(0.5, hz, 0.1, (255, 120, 200), 0.6, 1.5) * 0.7
    save(vignette(a, 0.45, 0.4), "synthwave", out)


# ---------------------------------------------------------------- 3 aurora
def aurora(out):
    a = vgrad([(0, (2, 6, 20)), (0.6, (6, 22, 40)), (1, (4, 30, 34))])
    a = stars(a, 380, 0.7)
    ribbons = [((0.30, 0.10, 0.045, 0.7), (40, 255, 160)), ((0.38, 0.12, 0.035, 2.1), (60, 200, 255)),
               ((0.24, 0.09, 0.03, 4.0), (160, 90, 255))]
    for (y0, amp, th, ph), col in ribbons:
        curve = y0 + amp * np.sin(X * 6.2 + ph) + 0.05 * np.sin(X * 13 + ph * 2)
        d = (Y - curve)
        prof = np.where(d > 0, np.exp(-(d / th) ** 2), np.exp(-(d / (th * 4.5)) ** 2))
        rays = 0.6 + 0.4 * np.sin(X * 90 + ph * 3 + 6 * np.sin(X * 7))
        m = prof * rays
        a += blur((m[:, :, None] * np.array(col, np.float32)[None, None, :]) * 0.9, 6) * 1.2
    # montañas
    for lay, (base, amp, col) in enumerate([(0.82, 0.05, (6, 14, 22)), (0.90, 0.045, (3, 8, 14))]):
        ridge = base - amp * (np.sin(X * 9 + lay * 2) * 0.6 + np.sin(X * 23 + lay) * 0.3 + np.sin(X * 51) * 0.1)
        m = (Y > ridge)[:, :, None]
        a = np.where(m, np.array(col, np.float32)[None, None, :], a)
    save(vignette(a, 0.4, 0.3), "aurora", out)


# ---------------------------------------------------------------- 4 metal cepillado
def brushed(out):
    n = rng.normal(0, 1, (H, W)).astype(np.float32)
    k = 90
    cs = np.cumsum(np.pad(n, ((0, 0), (k, 0)), mode="edge"), axis=1)
    streak = (cs[:, k:] - cs[:, :-k]) / math.sqrt(k)
    streak = streak / (np.std(streak) + 1e-6)
    base = 44 + 9 * streak
    g = base * (0.65 + 0.7 * (1 - np.abs(X - 0.72) * 1.2))
    g += 55 * np.exp(-(((X - 0.78) / 0.28) ** 2 + ((Y - 0.12) / 0.3) ** 2))
    a = np.stack([g * 0.95, g, g * 1.08], -1)
    # filo de luz
    def draw(dr):
        dr.line([(0, int(H * 0.86)), (W, int(H * 0.86))], fill=(0, 210, 255), width=3)
    core, halo = lines_layer(draw, 9, 0.9, 1.5)
    a += core * 0.8 + halo
    save(vignette(a, 0.5, 0.5), "brushed", out)


# ---------------------------------------------------------------- 5 cockpit HUD
def hud(out):
    d = np.sqrt(((X - 0.72) * 1.1) ** 2 + (Y - 0.5) ** 2)
    a = np.stack([4 + 10 * np.exp(-d * 2.5), 14 + 34 * np.exp(-d * 2.2), 30 + 60 * np.exp(-d * 2)], -1) * 1.0
    cxp, cyp = 0.72 * W, 0.5 * H

    def draw(dr):
        for r, w, al in [(170, 2, 1), (240, 1, 0.6), (320, 3, 1), (410, 1, 0.5), (500, 2, 0.8)]:
            c = (0, int(200 * al), int(255 * al))
            dr.ellipse([cxp - r, cyp - r, cxp + r, cyp + r], outline=c, width=w)
        # arcos gruesos
        for r, a0, a1, w in [(320, -210, -30, 10), (410, 20, 120, 8), (240, 150, 330, 6)]:
            dr.arc([cxp - r, cyp - r, cxp + r, cyp + r], a0, a1, fill=(0, 230, 255), width=w)
        # marcas
        for i in range(0, 360, 5):
            ang = math.radians(i)
            r0 = 320 + (14 if i % 30 == 0 else 6)
            r1 = 320 - (4)
            dr.line([(cxp + r0 * math.cos(ang), cyp + r0 * math.sin(ang)),
                     (cxp + (r1 - 18 if i % 30 == 0 else r1 - 6) * math.cos(ang), cyp + (r1 - 18 if i % 30 == 0 else r1 - 6) * math.sin(ang))],
                    fill=(120, 230, 255), width=2)
        # cruz central
        dr.line([(cxp - 30, cyp), (cxp + 30, cyp)], fill=(0, 255, 240), width=2)
        dr.line([(cxp, cyp - 30), (cxp, cyp + 30)], fill=(0, 255, 240), width=2)
        # puntos de cuadrícula
        for gx in range(0, W, 60):
            for gy in range(0, H, 60):
                dr.point([gx, gy], fill=(40, 90, 130))
    core, halo = lines_layer(draw, 7, 0.75, 1.6)
    a += core + halo
    a *= (1 - 0.05 * ((yy % 4) < 1.5))[:, :, None]     # líneas de barrido
    save(vignette(a, 0.5, 0.35), "hud", out)


# ---------------------------------------------------------------- 6 atardecer en ruta
def roadsunset(out):
    hz = 0.52
    a = vgrad([(0, (18, 8, 48)), (0.28, (110, 30, 100)), (0.45, (240, 100, 60)), (hz, (255, 190, 90))])
    a += glow(0.62, hz, 0.5, (255, 160, 60), 0.9, 2.0)
    sun_d = np.sqrt((xx - 0.62 * W) ** 2 + (yy - (hz - 0.015) * H) ** 2)
    sun = np.clip((0.085 * H - sun_d) / 3, 0, 1)
    a = a * (1 - sun[:, :, None]) + np.array([255, 235, 170], np.float32)[None, None, :] * sun[:, :, None]
    # colinas
    for lay, (base, amp, col) in enumerate([(0.50, 0.04, (70, 22, 70)), (0.52, 0.03, (34, 10, 44))]):
        ridge = base - amp * (np.sin(X * 7 + lay * 3) * 0.6 + np.sin(X * 19 + lay) * 0.3 + 0.2)
        a = np.where((Y > ridge)[:, :, None], np.array(col, np.float32)[None, None, :], a)
    # asfalto
    vx, vy = 0.62 * W, hz * H
    road = Image.new("L", (W, H), 0)
    ImageDraw.Draw(road).polygon([(vx - 6, vy), (vx + 6, vy), (W * 1.25, H), (-W * 0.05, H)], fill=255)
    rm = np.asarray(road).astype(np.float32) / 255
    asph = vgrad([(hz, (60, 30, 50)), (1, (14, 10, 20))])
    a = a * (1 - rm[:, :, None]) + asph * rm[:, :, None]
    def draw(dr):
        for k in range(0, 18):
            t0 = (k / 18.0) ** 2.0
            t1 = ((k + 0.45) / 18.0) ** 2.0
            def pt(t, off):
                y = vy + (H - vy) * t
                x = vx + (W * 0.22 + 0.0) * t * off + (0)
                return x, y
            y0, y1 = vy + (H - vy) * t0, vy + (H - vy) * t1
            w0, w1 = 2 + 22 * t0, 2 + 22 * t1
            dr.polygon([(vx - w0 / 2, y0), (vx + w0 / 2, y0), (vx + w1 / 2, y1), (vx - w1 / 2, y1)], fill=(255, 220, 120))
    core, halo = lines_layer(draw, 3, 0.9, 0.5)
    a += core + halo
    save(vignette(a, 0.5, 0.45), "roadsunset", out)


# ---------------------------------------------------------------- 7 lujo dorado
def gold(out):
    def vnoise(scale, seed):
        r = np.random.default_rng(seed)
        small = r.random((max(2, int(H / scale)), max(2, int(W / scale)))).astype(np.float32)
        return np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255
    n = 0.55 * vnoise(380, 1) + 0.3 * vnoise(170, 2) + 0.15 * vnoise(70, 3)
    warp = n * 6.0 + X * 1.5 + Y * 2.2
    v = np.abs(np.sin(warp * math.pi * 2))
    line = np.clip((v - 0.965) / 0.035, 0, 1) ** 1.5
    soft = np.exp(-((1 - v) / 0.015) ** 2) * 0.35
    base = 10 + 14 * vnoise(240, 5)
    a = np.stack([base, base, base * 1.05], -1)
    gold_c = np.array([226, 184, 74], np.float32)[None, None, :]
    lb = blur(line * 255, 4) / 255
    a += ((line * 0.85 + lb * 0.5)[:, :, None]) * gold_c
    a += soft[:, :, None] * gold_c * 0.25
    a += glow(0.82, 0.12, 0.65, (90, 66, 16), 1.0, 2.0)
    save(vignette(a, 0.55, 0.45), "gold", out)


# ---------------------------------------------------------------- 8 océano
def ocean(out):
    a = vgrad([(0, (6, 80, 140)), (0.45, (2, 40, 96)), (1, (1, 8, 30))])
    rays = np.zeros((H, W), np.float32)
    for i in range(9):
        x0 = rng.uniform(0.25, 1.1) * W
        wid = rng.uniform(40, 150)
        slope = rng.uniform(-0.35, -0.1)
        d = np.abs((xx - x0) - slope * yy * 1.4)
        rays += np.exp(-(d / wid) ** 2) * rng.uniform(0.25, 0.6)
    rays *= np.clip(1 - Y * 1.15, 0, 1)
    a += blur(rays[:, :, None] * np.array([120, 210, 255], np.float32)[None, None, :], 18) * 0.9
    # burbujas
    lay = Image.new("RGB", (W, H), (0, 0, 0))
    dr = ImageDraw.Draw(lay)
    for _ in range(90):
        x = rng.uniform(0.3, 1.0) * W
        y = rng.uniform(0.05, 1.0) * H
        r = rng.uniform(5, 30)
        b = int(rng.uniform(40, 130))
        dr.ellipse([x - r, y - r, x + r, y + r], outline=(b, b + 40, 255), width=2)
    a += blur(np.asarray(lay).astype(np.float32), 1.6) * 0.8
    a += glow(0.7, -0.05, 0.9, (40, 150, 220), 0.5, 1.8)
    save(vignette(a, 0.55, 0.4), "ocean", out)


# ---------------------------------------------------------------- 9 bosque
def forest(out):
    a = vgrad([(0, (6, 18, 26)), (0.5, (22, 52, 56)), (0.75, (50, 88, 84))])
    a += glow(0.78, 0.14, 0.3, (210, 235, 235), 0.85, 2.6)
    moon_d = np.sqrt((xx - 0.78 * W) ** 2 + (yy - 0.14 * H) ** 2)
    a = a * (1 - np.clip((0.045 * H - moon_d) / 2, 0, 1))[:, :, None] + np.array([235, 245, 240], np.float32) * np.clip((0.045 * H - moon_d) / 2, 0, 1)[:, :, None]
    a = stars(a, 150, 0.35)
    layers = [(0.78, (26, 62, 62), 26, 0.10), (0.84, (14, 38, 42), 36, 0.13), (0.92, (6, 20, 24), 50, 0.17), (1.02, (2, 9, 12), 70, 0.22)]
    for base, col, size, hh in layers:
        lay = Image.new("L", (W, H), 0)
        dr = ImageDraw.Draw(lay)
        x = -50.0
        while x < W + 50:
            th = H * hh * rng.uniform(0.7, 1.4)
            tw = size * rng.uniform(0.8, 1.3)
            by = base * H
            tiers = 5
            for t in range(tiers):
                f0 = t / tiers
                f1 = (t + 1) / tiers
                dr.polygon([(x, by - th * f1), (x - tw * (1 - f0) * 0.6, by - th * f0), (x + tw * (1 - f0) * 0.6, by - th * f0)], fill=255)
            dr.rectangle([x - 3, by - th * 0.1, x + 3, by + 20], fill=255)
            x += tw * rng.uniform(0.55, 0.9)
        dr.rectangle([0, min(base * H, H), W, H], fill=255)
        m = np.asarray(lay).astype(np.float32) / 255
        a = a * (1 - m[:, :, None]) + np.array(col, np.float32)[None, None, :] * m[:, :, None]
        fog = np.exp(-(((Y - (base - 0.02)) / 0.05) ** 2))
        a += blur(fog[:, :, None] * np.array([70, 110, 110], np.float32)[None, None, :], 25) * 0.55
    save(vignette(a, 0.45, 0.35), "forest", out)


# ---------------------------------------------------------------- 10 dunas
def dunes(out):
    a = vgrad([(0, (36, 18, 70)), (0.25, (150, 56, 90)), (0.45, (244, 130, 70)), (0.6, (255, 204, 130))])
    sun_d = np.sqrt((xx - 0.7 * W) ** 2 + (yy - 0.46 * H) ** 2)
    a += glow(0.7, 0.46, 0.5, (255, 190, 100), 0.8, 2.0)
    s = np.clip((0.065 * H - sun_d) / 3, 0, 1)
    a = a * (1 - s[:, :, None]) + np.array([255, 244, 214], np.float32) * s[:, :, None]
    cols = [(214, 120, 70), (180, 88, 56), (140, 60, 46), (94, 38, 38), (52, 22, 30)]
    for i, col in enumerate(cols):
        base = 0.56 + i * 0.1
        ridge = base - 0.06 * (np.sin(X * (2.6 + i * 0.7) + i * 1.7) * 0.7 + np.sin(X * (7 + i) + i) * 0.25)
        ridge = ridge + 0.0
        m = (Y > ridge)[:, :, None]
        shade = 1 - 0.35 * np.clip((Y - ridge) / 0.12, 0, 1)
        a = np.where(m, np.array(col, np.float32)[None, None, :] * shade[:, :, None], a)
    save(vignette(a, 0.45, 0.4), "dunes", out)


# ---------------------------------------------------------------- 11 ciudad nocturna
def citynight(out):
    a = vgrad([(0, (4, 6, 18)), (0.6, (18, 16, 40)), (1, (30, 18, 36))])
    # skyline desenfocada
    lay = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(lay)
    x = 0
    while x < W:
        bw = int(rng.uniform(50, 150))
        bh = int(rng.uniform(0.12, 0.42) * H)
        dr.rectangle([x, H * 0.72 - bh, x + bw, H], fill=255)
        for wy in range(int(H * 0.72 - bh) + 12, int(H * 0.72), 22):
            for wx in range(x + 8, x + bw - 8, 18):
                if rng.random() < 0.25:
                    dr.rectangle([wx, wy, wx + 6, wy + 9], fill=140)
        x += bw + int(rng.uniform(0, 14))
    sky = np.asarray(lay.filter(ImageFilter.GaussianBlur(3.2))).astype(np.float32)
    mask = np.clip(sky / 255 * 1.9, 0, 1)
    a = a * (1 - 0.8 * mask[:, :, None]) + np.array([200, 170, 90], np.float32) * (np.clip(sky - 120, 0, 140) / 140 * 0.55)[:, :, None]
    # bokeh
    bl = Image.new("RGB", (W, H), (0, 0, 0))
    bd = ImageDraw.Draw(bl, "RGBA")
    palette = [(255, 190, 90), (255, 140, 60), (255, 240, 200), (90, 170, 255), (60, 220, 255), (255, 80, 120)]
    for _ in range(70):
        x = rng.uniform(0.2, 1.05) * W
        y = rng.uniform(0.35, 1.0) * H
        r = rng.uniform(18, 75)
        c = palette[int(rng.integers(0, len(palette)))]
        al = int(rng.uniform(35, 105))
        bd.ellipse([x - r, y - r, x + r, y + r], fill=c + (al,))
        bd.ellipse([x - r, y - r, x + r, y + r], outline=c + (min(255, al + 60),), width=2)
    a += blur(np.asarray(bl).astype(np.float32), 2.2) * 0.9
    # estelas de luz en el piso
    def draw(dr2):
        for k in range(9):
            y = H * (0.88 + 0.011 * k)
            dr2.line([(0, y), (W, y + rng.uniform(-30, 30))], fill=(255, 90 + 12 * k, 60), width=2)
    core, halo = lines_layer(draw, 10, 0.45, 1.0)
    a += core * 0.5 + halo * 0.8
    save(vignette(a, 0.5, 0.4), "citynight", out)


# ======================= versiones mejoradas (sustituyen a las anteriores) =======================
def aurora(out):
    a = vgrad([(0, (2, 6, 20)), (0.6, (6, 22, 40)), (1, (4, 30, 34))])
    a = stars(a, 380, 0.7)
    ribbons = [((0.36, 0.09, 0.07, 0.7), (40, 255, 170)), ((0.44, 0.10, 0.055, 2.1), (60, 190, 255)),
               ((0.30, 0.08, 0.05, 4.0), (170, 100, 255))]
    for (y0, amp, th, ph), col in ribbons:
        curve = y0 + amp * np.sin(X * 4.6 + ph) + 0.04 * np.sin(X * 9.5 + ph * 2)
        d = (Y - curve)
        prof = np.where(d > 0, np.exp(-(d / (th * 0.8)) ** 2), np.exp(-(d / (th * 3.6)) ** 2))
        rays = 0.86 + 0.14 * np.sin(X * 42 + ph * 3 + 4 * np.sin(X * 5))
        m = prof * rays
        layer = blur((m[:, :, None] * np.array(col, np.float32)[None, None, :]) * 0.95, 16)
        a += layer * 0.8
    for lay, (base, amp, col) in enumerate([(0.82, 0.05, (6, 14, 22)), (0.90, 0.045, (3, 8, 14))]):
        ridge = base - amp * (np.sin(X * 9 + lay * 2) * 0.6 + np.sin(X * 23 + lay) * 0.3 + np.sin(X * 51) * 0.1)
        a = np.where((Y > ridge)[:, :, None], np.array(col, np.float32)[None, None, :], a)
    save(vignette(a, 0.4, 0.3), "aurora", out)


def brushed(out):
    n = rng.normal(0, 1, (H, W)).astype(np.float32)
    k = 90
    ext = np.concatenate([n[:, -k:], n], axis=1)          # envuelve los bordes: sin franja rara a la izquierda
    cs = np.cumsum(ext, axis=1)
    streak = (cs[:, k:] - cs[:, :-k]) / math.sqrt(k)
    streak = streak / (np.std(streak) + 1e-6)
    base = 44 + 9 * streak
    g = base * (0.65 + 0.7 * (1 - np.abs(X - 0.72) * 1.2))
    g += 55 * np.exp(-(((X - 0.78) / 0.28) ** 2 + ((Y - 0.12) / 0.3) ** 2))
    a = np.stack([g * 0.95, g, g * 1.08], -1)
    def draw(dr):
        dr.line([(0, int(H * 0.86)), (W, int(H * 0.86))], fill=(0, 210, 255), width=3)
    core, halo = lines_layer(draw, 9, 0.9, 1.5)
    a += core * 0.8 + halo
    save(vignette(a, 0.5, 0.5), "brushed", out)


def gold(out):
    def vnoise(scale, seed):
        r = np.random.default_rng(seed)
        small = r.random((max(2, int(H / scale)), max(2, int(W / scale)))).astype(np.float32)
        return np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255
    base = 9 + 13 * vnoise(260, 5) + 6 * vnoise(90, 6)
    a = np.stack([base, base, base * 1.06], -1)
    gold_c = np.array([228, 186, 78], np.float32)[None, None, :]
    # pocas venas grandes y finas, más otras tenues (mármol negro con vetas doradas)
    for seed, freq, thr, gain in [(11, 1.15, 0.9965, 1.0), (23, 1.7, 0.995, 0.5), (37, 2.4, 0.994, 0.3)]:
        n = 0.6 * vnoise(520, seed) + 0.3 * vnoise(210, seed + 1) + 0.1 * vnoise(80, seed + 2)
        warp = n * 4.2 + X * 0.9 + Y * 1.3
        v = np.abs(np.sin(warp * math.pi * freq))
        line = np.clip((v - thr) / (1 - thr), 0, 1) ** 1.2
        lb = blur(line * 255, 5) / 255
        a += ((line * 0.95 + lb * 0.9)[:, :, None]) * gold_c * gain
        a += (blur(line * 255, 22) / 255 * 0.6)[:, :, None] * gold_c * 0.5 * gain
    a += glow(0.82, 0.12, 0.65, (84, 62, 16), 1.0, 2.0)
    save(vignette(a, 0.55, 0.5), "gold", out)


def forest(out):
    a = vgrad([(0, (6, 18, 26)), (0.5, (22, 52, 56)), (0.75, (50, 88, 84))])
    a += glow(0.78, 0.14, 0.3, (210, 235, 235), 0.85, 2.6)
    moon_d = np.sqrt((xx - 0.78 * W) ** 2 + (yy - 0.14 * H) ** 2)
    mm = np.clip((0.045 * H - moon_d) / 2, 0, 1)[:, :, None]
    a = a * (1 - mm) + np.array([235, 245, 240], np.float32) * mm
    a = stars(a, 150, 0.35)
    layers = [(0.80, (28, 66, 66), 54, 0.17), (0.88, (15, 40, 44), 74, 0.22), (0.97, (7, 22, 26), 102, 0.28), (1.06, (2, 9, 12), 140, 0.36)]
    for base, col, size, hh in layers:
        lay = Image.new("L", (W, H), 0)
        dr = ImageDraw.Draw(lay)
        x = -60.0
        while x < W + 60:
            th = H * hh * rng.uniform(0.7, 1.35)
            tw = size * rng.uniform(0.85, 1.25)
            by = base * H
            tiers = 6
            for t in range(tiers):
                f0 = t / tiers
                f1 = (t + 1) / tiers
                dr.polygon([(x, by - th * f1), (x - tw * (1 - f0 * 0.9) * 0.62, by - th * f0 * 0.92), (x + tw * (1 - f0 * 0.9) * 0.62, by - th * f0 * 0.92)], fill=255)
            dr.rectangle([x - 4, by - th * 0.1, x + 4, by + 30], fill=255)
            x += tw * rng.uniform(0.7, 1.05)
        dr.rectangle([0, min(base * H, H), W, H], fill=255)
        m = np.asarray(lay).astype(np.float32) / 255
        a = a * (1 - m[:, :, None]) + np.array(col, np.float32)[None, None, :] * m[:, :, None]
        fog = np.exp(-(((Y - (base - 0.03)) / 0.06) ** 2))
        a += blur(fog[:, :, None] * np.array([70, 112, 112], np.float32)[None, None, :], 30) * 0.5
    save(vignette(a, 0.45, 0.35), "forest", out)


def citynight(out):
    a = vgrad([(0, (4, 6, 18)), (0.55, (20, 16, 42)), (1, (34, 18, 38))])
    a += glow(0.7, 0.62, 0.6, (90, 50, 110), 0.5, 2.0)
    bl = Image.new("L", (W, H), 0)
    wl = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(bl)
    wd = ImageDraw.Draw(wl)
    x = -20
    while x < W:
        bw = int(rng.uniform(60, 170))
        bh = int(rng.uniform(0.14, 0.46) * H)
        top = int(H * 0.8 - bh)
        bd.rectangle([x, top, x + bw, H], fill=255)
        for wy in range(top + 14, int(H * 0.8), 24):
            for wx in range(x + 10, x + bw - 10, 20):
                if rng.random() < 0.28:
                    wd.rectangle([wx, wy, wx + 7, wy + 11], fill=255)
        x += bw + int(rng.uniform(0, 10))
    bmask = np.asarray(bl.filter(ImageFilter.GaussianBlur(2.2))).astype(np.float32) / 255
    wmask = np.asarray(wl.filter(ImageFilter.GaussianBlur(1.4))).astype(np.float32) / 255
    a = a * (1 - 0.92 * bmask[:, :, None]) + np.array([6, 6, 16], np.float32) * (0.92 * bmask)[:, :, None]
    a += wmask[:, :, None] * np.array([255, 196, 110], np.float32)[None, None, :] * 0.8 * bmask[:, :, None]
    bk = Image.new("RGB", (W, H), (0, 0, 0))
    bdr = ImageDraw.Draw(bk, "RGBA")
    palette = [(255, 190, 90), (255, 140, 60), (255, 240, 200), (90, 170, 255), (60, 220, 255), (255, 80, 120)]
    for _ in range(64):
        x = rng.uniform(0.25, 1.05) * W
        y = rng.uniform(0.45, 1.0) * H
        r = rng.uniform(16, 70)
        c = palette[int(rng.integers(0, len(palette)))]
        al = int(rng.uniform(30, 95))
        bdr.ellipse([x - r, y - r, x + r, y + r], fill=c + (al,))
        bdr.ellipse([x - r, y - r, x + r, y + r], outline=c + (min(255, al + 70),), width=2)
    a += blur(np.asarray(bk).astype(np.float32), 2.0) * 0.9
    def draw(dr2):
        for k in range(9):
            y = H * (0.9 + 0.01 * k)
            dr2.line([(0, y), (W, y + rng.uniform(-24, 24))], fill=(255, 90 + 12 * k, 60), width=2)
    core, halo = lines_layer(draw, 10, 0.45, 1.0)
    a += core * 0.5 + halo * 0.8
    save(vignette(a, 0.5, 0.4), "citynight", out)


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for fn in (carbon, synthwave, aurora, brushed, hud, roadsunset, gold, ocean, forest, dunes, citynight):
        fn(out)
        print("ok", fn.__name__)
