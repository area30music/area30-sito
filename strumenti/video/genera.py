"""Video tutorial AREA30 per ledwall: 960x1080, 30 fps, ~54 s, senza audio."""
import math
import subprocess
import sys
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

SITO = Path("/Users/gabrielelascala/AREA30 Sito")
QUI = Path(__file__).parent
OUT_MP4 = Path(sys.argv[1]) if len(sys.argv) > 1 else QUI / "area30-tutorial-app.mp4"
W, H, FPS = 960, 1080, 30

GOLD = (227, 189, 99)
GOLD2 = (245, 220, 148)
BG = (9, 9, 11)
WHITE = (240, 238, 232)
MUTED = (165, 162, 155)


def font(nome, size, weight=None):
    f = ImageFont.truetype(str(QUI / f"{nome}.ttf"), size)
    if weight:
        f.set_variation_by_axes([weight])
    return f


F_TIT = lambda s: font("big-shoulders", s, 800)
F_UI = lambda s, w=600: font("manrope", s, w)

LOGO = Image.open(SITO / "assets/logo-area30.png").convert("RGBA")
ICON = Image.open(SITO / "assets/icon-512.png").convert("RGBA")
HERO = Image.open(SITO / "media/live-05.jpg").convert("RGB")
POSTER = Image.open(SITO / "media/locandina-absolute5-2026.jpg").convert("RGB")


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def logo(w):
    return LOGO.resize((w, int(LOGO.height * w / LOGO.width)), Image.LANCZOS)


def rr(d, box, r, **kw):
    d.rounded_rectangle(box, r, **kw)


def text_c(d, cx, y, s, f, fill):
    w = d.textlength(s, font=f)
    d.text((cx - w / 2, y), s, font=f, fill=fill)


def wrap(d, s, f, maxw):
    righe, cur = [], ""
    for p in s.split():
        prova = (cur + " " + p).strip()
        if d.textlength(prova, font=f) <= maxw:
            cur = prova
        else:
            righe.append(cur)
            cur = p
    if cur:
        righe.append(cur)
    return righe


def icona_app(size):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size - 1, size - 1), int(size * 0.23), fill=255)
    ic = ICON.resize((size, size), Image.LANCZOS)
    ic.putalpha(m)
    return ic


# ------------------------------------------------------------------ sfondo con fasci di luce
def sfondo():
    im = Image.new("RGB", (W, H), BG)
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    for i in range(30, 0, -1):
        r = i * 26
        c = int(40 * (1 - i / 30))
        g.ellipse((W / 2 - r, -r * 0.6, W / 2 + r, r * 0.6), fill=(c, int(c * 0.8), int(c * 0.35)))
    im = Image.blend(im, glow, 0.9)
    beams = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b = ImageDraw.Draw(beams)
    for x, ang, col in ((120, -18, (255, 226, 150, 34)), (480, 6, (190, 140, 255, 22)), (840, 20, (255, 226, 150, 30))):
        top = (x, -40)
        L = 1400
        a1, a2 = math.radians(ang - 7), math.radians(ang + 7)
        poly = [(x - 6, -40), (x + 6, -40), (x + 6 + L * math.sin(a2), L * math.cos(a2)), (x - 6 + L * math.sin(a1), L * math.cos(a1))]
        b.polygon(poly, fill=col)
    beams = beams.filter(ImageFilter.GaussianBlur(24))
    im = im.convert("RGBA")
    im.alpha_composite(beams)
    return im


BGIMG = sfondo()

# ------------------------------------------------------------------ QR
def qr_img(size):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    q.add_data("https://area30.it")
    q.make(fit=True)
    im = q.make_image(fill_color=(10, 10, 12), back_color=(255, 255, 255)).convert("RGBA")
    im = im.resize((size, size), Image.NEAREST)
    # icona al centro
    c = icona_app(int(size * 0.22))
    pad = Image.new("RGBA", (c.width + 16, c.height + 16), (255, 255, 255, 255))
    pm = Image.new("L", pad.size, 0)
    ImageDraw.Draw(pm).rounded_rectangle((0, 0, pad.width - 1, pad.height - 1), 18, fill=255)
    pad.putalpha(pm)
    im.alpha_composite(pad, ((size - pad.width) // 2, (size - pad.height) // 2))
    im.alpha_composite(c, ((size - c.width) // 2, (size - c.height) // 2))
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size - 1, size - 1), int(size * 0.06), fill=255)
    im.putalpha(m)
    return im


QR_BIG = qr_img(520)
QR_SMALL = qr_img(170)

# ------------------------------------------------------------------ telefono
PW, PH = 400, 816
PX, PY = (W - PW) // 2, 252
INS = 14
SW, SH = PW - 2 * INS, PH - 2 * INS
SX, SY = PX + INS, PY + INS


def cornice():
    im = Image.new("RGBA", (PW + 40, PH + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((20, 30, PW + 20, PH + 30), 64, fill=(0, 0, 0, 200))
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    im.alpha_composite(sh)
    d = ImageDraw.Draw(im)
    rr(d, (20, 20, PW + 19, PH + 19), 62, fill=(28, 28, 32), outline=(120, 100, 60), width=3)
    rr(d, (20 + INS - 2, 20 + INS - 2, PW + 19 - INS + 2, PH + 19 - INS + 2), 50, fill=(0, 0, 0))
    return im


FRAME = cornice()
SCREEN_MASK = Image.new("L", (SW, SH), 0)
ImageDraw.Draw(SCREEN_MASK).rounded_rectangle((0, 0, SW - 1, SH - 1), 48, fill=255)


def isola(d):  # Dynamic Island
    rr(d, (SW // 2 - 62, 12, SW // 2 + 62, 46), 17, fill=(0, 0, 0))


def statusbar(d, scuro=True):
    col = WHITE if scuro else (20, 20, 20)
    d.text((34, 16), "21:00", font=F_UI(19, 700), fill=col)
    # batteria
    rr(d, (SW - 64, 20, SW - 32, 36), 4, outline=col, width=2)
    d.rectangle((SW - 61, 23, SW - 40, 33), fill=col)
    for i, h in enumerate((5, 8, 11, 14)):
        d.rectangle((SW - 112 + i * 7, 36 - h, SW - 108 + i * 7, 36), fill=col)


# ------------------------------------------------------------------ schermate
def pagina_sito(top=0, bottom_bar=0, app=False):
    """Home del sito AREA30 come appare sul telefono."""
    im = Image.new("RGBA", (SW, SH), BG + (255,))
    d = ImageDraw.Draw(im)
    h_hero = 470
    hero = ImageOps.fit(HERO, (SW, h_hero), Image.LANCZOS, centering=(0.1, 0.4)).convert("RGBA")
    shade = Image.new("RGBA", (SW, h_hero), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for y in range(h_hero):
        a = int(70 + 185 * (y / h_hero) ** 1.4)
        sd.line((0, y, SW, y), fill=(9, 9, 11, min(255, a)))
    hero.alpha_composite(shade)
    im.alpha_composite(hero, (0, top))
    lg = logo(300)
    im.alpha_composite(lg, ((SW - lg.width) // 2, top + 190))
    text_c(d, SW // 2, top + 252, "SERVICE AUDIO E LUCI · EVENTI LIVE", F_TIT(24), WHITE)
    # card prossimo evento
    y0 = top + 310
    rr(d, (22, y0, SW - 22, y0 + 128), 16, fill=(30, 26, 18), outline=GOLD + (120,), width=2)
    d.text((40, y0 + 16), "PROSSIMO EVENTO", font=F_UI(14, 700), fill=GOLD)
    d.text((40, y0 + 38), "ABSOLUTE 5 IN CONCERTO", font=F_TIT(30), fill=WHITE)
    d.text((40, y0 + 78), "Sabato 28 novembre · ore 21.00", font=F_UI(16, 500), fill=MUTED)
    # pulsante
    rr(d, (22, y0 + 152, 230, y0 + 204), 26, fill=GOLD)
    d.text((48, y0 + 165), "Prossimi eventi", font=F_UI(19, 700), fill=(22, 18, 10))
    # locandina
    p = ImageOps.fit(POSTER, (150, 210), Image.LANCZOS).convert("RGBA")
    pm = Image.new("L", p.size, 0)
    ImageDraw.Draw(pm).rounded_rectangle((0, 0, 149, 209), 14, fill=255)
    p.putalpha(pm)
    im.alpha_composite(p, (22, y0 + 232))
    d.text((190, y0 + 246), "I nostri", font=F_TIT(34), fill=WHITE)
    d.text((190, y0 + 284), "prossimi eventi", font=F_TIT(34), fill=WHITE)
    # intestazione del sito (campanella + menu)
    if app:
        rr(d, (SW - 128, 60, SW - 84, 104), 22, outline=GOLD, width=2)
        cx, cy = SW - 106, 82
        d.arc((cx - 10, cy - 12, cx + 10, cy + 10), 180, 360, fill=GOLD, width=3)
        d.line((cx - 10, cy, cx - 10, cy + 6), fill=GOLD, width=3)
        d.line((cx + 10, cy, cx + 10, cy + 6), fill=GOLD, width=3)
        d.line((cx - 14, cy + 7, cx + 14, cy + 7), fill=GOLD, width=3)
        rr(d, (SW - 72, 60, SW - 28, 104), 22, outline=GOLD, width=2)
        d.line((SW - 60, 76, SW - 40, 76), fill=WHITE, width=3)
        d.line((SW - 60, 88, SW - 40, 88), fill=WHITE, width=3)
    isola(d)
    statusbar(d)
    return im


def safari_bar(im, evid=False):
    d = ImageDraw.Draw(im)
    y = SH - 150
    d.rectangle((0, y, SW, SH), fill=(32, 32, 36))
    rr(d, (18, y + 12, SW - 18, y + 58), 14, fill=(58, 58, 64))
    text_c(d, SW // 2, y + 22, "area30.it", F_UI(20, 600), WHITE)
    # icone: indietro, avanti, condividi, segnalibri, pannelli
    yi = y + 96
    xs = [44, 114, SW // 2, SW - 114, SW - 44]
    blu = (64, 150, 255)
    d.line((xs[0] + 6, yi - 12, xs[0] - 6, yi, xs[0] + 6, yi + 12), fill=blu, width=4, joint="curve")
    d.line((xs[1] - 6, yi - 12, xs[1] + 6, yi, xs[1] - 6, yi + 12), fill=(90, 90, 96), width=4, joint="curve")
    c = xs[2]
    col = GOLD2 if evid else blu
    rr(d, (c - 15, yi - 6, c + 15, yi + 20), 4, outline=col, width=3)
    d.rectangle((c - 6, yi - 9, c + 6, yi - 3), fill=(32, 32, 36))
    d.line((c, yi - 22, c, yi + 6), fill=col, width=3)
    d.line((c - 8, yi - 14, c, yi - 22, c + 8, yi - 14), fill=col, width=3)
    d.line((xs[3] - 14, yi - 10, xs[3] + 14, yi - 10), fill=blu, width=3)
    d.arc((xs[3] - 14, yi - 14, xs[3] + 14, yi + 14), 0, 180, fill=blu, width=3)
    rr(d, (xs[4] - 12, yi - 12, xs[4] + 12, yi + 12), 4, outline=blu, width=3)
    return (c, yi)


def chrome_bar(im):
    d = ImageDraw.Draw(im)
    d.rectangle((0, 50, SW, 116), fill=(40, 40, 46))
    rr(d, (18, 60, SW - 70, 106), 23, fill=(64, 64, 70))
    d.text((44, 70), "area30.it", font=F_UI(21, 600), fill=WHITE)
    x = SW - 38
    for k in (-11, 0, 11):
        d.ellipse((x - 4, 83 + k - 4, x + 4, 83 + k + 4), fill=WHITE)
    return (x, 83)


def ios_sheet():
    im = Image.new("RGBA", (SW, 520), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rr(d, (0, 0, SW, 560), 28, fill=(242, 242, 247))
    rr(d, (SW // 2 - 22, 10, SW // 2 + 22, 15), 3, fill=(190, 190, 196))
    ic = icona_app(54)
    im.alpha_composite(ic, (22, 34))
    d.text((90, 38), "AREA30", font=F_UI(20, 700), fill=(20, 20, 20))
    d.text((90, 64), "area30.it", font=F_UI(16, 500), fill=(120, 120, 128))
    righe = ["Copia", "Aggiungi a Elenco lettura", "Aggiungi ai Preferiti", "Aggiungi alla schermata Home", "Trova nella pagina"]
    y = 116
    rr(d, (16, y, SW - 16, y + 5 * 62), 14, fill=(255, 255, 255))
    pos = None
    for i, r in enumerate(righe):
        yy = y + i * 62
        if i == 3:
            rr(d, (16, yy, SW - 16, yy + 62), 14, fill=(255, 241, 206))
            pos = (SW - 44, yy + 31)
        d.text((36, yy + 19), r, font=F_UI(19, 700 if i == 3 else 500), fill=(20, 20, 20))
        if i == 3:
            rr(d, (SW - 58, yy + 17, SW - 30, yy + 45), 6, outline=(20, 20, 20), width=2)
            d.line((SW - 44, yy + 23, SW - 44, yy + 39), fill=(20, 20, 20), width=2)
            d.line((SW - 52, yy + 31, SW - 36, yy + 31), fill=(20, 20, 20), width=2)
        if i < 4:
            d.line((36, yy + 62, SW - 16, yy + 62), fill=(225, 225, 230), width=1)
    return im, pos


def ios_aggiungi():
    im = Image.new("RGBA", (SW, SH), (242, 242, 247, 255))
    d = ImageDraw.Draw(im)
    isola(d)
    statusbar(d, scuro=False)
    blu = (0, 122, 255)
    d.text((22, 74), "Annulla", font=F_UI(19, 500), fill=blu)
    text_c(d, SW // 2, 74, "Aggiungi a Home", F_UI(19, 700), (20, 20, 20))
    aw = d.textlength("Aggiungi", font=F_UI(19, 800))
    d.text((SW - 22 - aw, 74), "Aggiungi", font=F_UI(19, 800), fill=blu)
    rr(d, (16, 130, SW - 16, 262), 14, fill=(255, 255, 255))
    im.alpha_composite(icona_app(88), (32, 152))
    d.text((140, 166), "AREA30", font=F_UI(24, 700), fill=(20, 20, 20))
    d.line((140, 204, SW - 32, 204), fill=(225, 225, 230), width=1)
    d.text((140, 214), "area30.it", font=F_UI(17, 500), fill=(120, 120, 128))
    rr(d, (16, 290, SW - 16, 350), 14, fill=(255, 255, 255))
    d.text((34, 308), "Apri come app web", font=F_UI(19, 500), fill=(20, 20, 20))
    rr(d, (SW - 90, 304, SW - 34, 336), 16, fill=(52, 199, 89))
    d.ellipse((SW - 64, 306, SW - 36, 334), fill=(255, 255, 255))
    for i, s in enumerate(["Verrà aggiunta un'icona alla schermata", "Home per accedere rapidamente al sito."]):
        d.text((32, 366 + i * 24), s, font=F_UI(15, 500), fill=(120, 120, 128))
    return im, (SW - 22 - aw / 2, 86)


ICON_COLS = [(255, 94, 87), (52, 199, 89), (0, 122, 255), (255, 159, 10), (175, 82, 222), (90, 200, 250),
             (255, 55, 95), (100, 210, 140), (255, 204, 0), (88, 86, 214), (142, 142, 147), (48, 176, 199)]


def home(android=False, area_scale=1.0):
    im = Image.new("RGBA", (SW, SH), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    for y in range(SH):
        t = y / SH
        d.line((0, y, SW, y), fill=(int(40 + 60 * t), int(30 + 20 * t), int(90 + 60 * (1 - t))))
    isola(d) if not android else None
    statusbar(d)
    s, gap = 68, (SW - 4 * 68) // 5
    pos_area = None
    for i in range(12):
        r, c = divmod(i, 4)
        x = gap + c * (s + gap)
        y = 110 + r * 120
        if i == 10:  # posto per AREA30
            pos_area = (x + s // 2, y + s // 2)
            continue
        rr(d, (x, y, x + s, y + s), 16 if not android else 34, fill=ICON_COLS[i % len(ICON_COLS)])
        rr(d, (x + 14, y + 52 + 30, x + s - 14, y + 52 + 38), 4, fill=(255, 255, 255, 150))
    if area_scale > 0:
        sz = max(2, int(s * area_scale))
        ic = icona_app(sz) if not android else ImageOps.fit(ICON, (sz, sz))
        if android:
            m = Image.new("L", (sz, sz), 0)
            ImageDraw.Draw(m).ellipse((0, 0, sz - 1, sz - 1), fill=255)
            ic = ic.copy()
            ic.putalpha(m)
        im.alpha_composite(ic, (pos_area[0] - sz // 2, pos_area[1] - sz // 2))
        if area_scale >= 0.95:
            text_c(d, pos_area[0], pos_area[1] + 40, "AREA30", F_UI(15, 700), WHITE)
    # dock
    rr(d, (16, SH - 128, SW - 16, SH - 28), 34, fill=(255, 255, 255, 60))
    for c in range(4):
        x = gap + c * (s + gap)
        rr(d, (x, SH - 112, x + s, SH - 112 + s), 16 if not android else 34, fill=ICON_COLS[(c + 5) % 12])
    return im, pos_area


def android_menu():
    im = Image.new("RGBA", (250, 330), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rr(d, (0, 0, 249, 329), 16, fill=(48, 48, 54))
    voci = ["Nuova scheda", "Cronologia", "Download", "Installa app", "Impostazioni"]
    pos = None
    for i, v in enumerate(voci):
        y = 14 + i * 62
        if i == 3:
            rr(d, (8, y, 241, y + 56), 12, fill=(92, 78, 40))
            pos = (205, y + 28)
        d.text((24, y + 16), v, font=F_UI(19, 700 if i == 3 else 500), fill=WHITE)
    return im, pos


def android_dialog():
    im = Image.new("RGBA", (SW - 60, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rr(d, (0, 0, im.width - 1, 299), 26, fill=(44, 44, 50))
    d.text((28, 26), "Installa app", font=F_UI(26, 700), fill=WHITE)
    im.alpha_composite(icona_app(64), (28, 88))
    d.text((108, 92), "AREA30", font=F_UI(21, 700), fill=WHITE)
    d.text((108, 122), "area30.it", font=F_UI(16, 500), fill=MUTED)
    d.text((im.width - 250, 232), "Annulla", font=F_UI(20, 600), fill=(150, 190, 255))
    rr(d, (im.width - 140, 220, im.width - 24, 272), 26, fill=(150, 190, 255))
    d.text((im.width - 116, 232), "Installa", font=F_UI(20, 700), fill=(20, 30, 60))
    return im, (im.width - 82, 246)


def notify_sheet():
    im = Image.new("RGBA", (SW - 24, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rr(d, (0, 0, im.width - 1, 299), 24, fill=(28, 24, 16), outline=GOLD + (160,), width=2)
    rr(d, (20, 22, 72, 74), 14, fill=GOLD)
    cx, cy = 46, 46
    d.arc((cx - 12, cy - 14, cx + 12, cy + 12), 180, 360, fill=(22, 18, 10), width=3)
    d.line((cx - 12, cy, cx - 12, cy + 7), fill=(22, 18, 10), width=3)
    d.line((cx + 12, cy, cx + 12, cy + 7), fill=(22, 18, 10), width=3)
    d.line((cx - 16, cy + 8, cx + 16, cy + 8), fill=(22, 18, 10), width=3)
    d.text((88, 20), "NON PERDERTI I", font=F_TIT(28), fill=WHITE)
    d.text((88, 50), "PROSSIMI CONCERTI", font=F_TIT(28), fill=WHITE)
    d.text((22, 96), "Ti avvisiamo quando annunciamo", font=F_UI(17, 500), fill=(215, 212, 205))
    d.text((22, 120), "un nuovo evento AREA30.", font=F_UI(17, 500), fill=(215, 212, 205))
    rr(d, (20, 164, im.width - 20, 222), 29, fill=GOLD)
    text_c(d, im.width // 2, 180, "Attiva le notifiche", F_UI(21, 800), (22, 18, 10))
    rr(d, (20, 234, im.width - 20, 284), 25, outline=(120, 100, 60), width=2)
    text_c(d, im.width // 2, 246, "Non ora", F_UI(18, 600), WHITE)
    return im, (im.width - 64, 193)


def ios_alert():
    im = Image.new("RGBA", (290, 210), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rr(d, (0, 0, 289, 209), 18, fill=(236, 236, 240))
    text_c(d, 145, 22, "“AREA30” vorrebbe", F_UI(18, 700), (20, 20, 20))
    text_c(d, 145, 46, "inviarti delle notifiche", F_UI(18, 700), (20, 20, 20))
    text_c(d, 145, 80, "Avvisi, suoni e badge.", F_UI(14, 500), (90, 90, 96))
    d.line((0, 150, 290, 150), fill=(200, 200, 206), width=1)
    d.line((145, 150, 145, 210), fill=(200, 200, 206), width=1)
    text_c(d, 72, 168, "Non consentire", F_UI(16, 500), (0, 122, 255))
    rr(d, (148, 152, 288, 207), 0, fill=(255, 241, 206))
    text_c(d, 217, 166, "Consenti", F_UI(18, 800), (0, 122, 255))
    return im, (252, 180)


def toast_ok():
    im = Image.new("RGBA", (SW - 60, 92), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rr(d, (0, 0, im.width - 1, 91), 22, fill=(20, 60, 40), outline=(76, 195, 138), width=2)
    d.ellipse((20, 22, 68, 70), fill=(76, 195, 138))
    d.line((32, 46, 41, 56, 57, 36), fill=(255, 255, 255), width=5, joint="curve")
    d.text((86, 18), "Notifiche attive", font=F_UI(22, 800), fill=WHITE)
    d.text((86, 50), "Ti avvisiamo noi!", font=F_UI(17, 500), fill=(200, 235, 215))
    return im


# ------------------------------------------------------------------ elementi del fotogramma
def intestazione(fr, numero, titolo, sotto, didascalia, alpha=1.0, piattaforma=None):
    lay = Image.new("RGBA", (W, 250), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x = 44
    if numero:
        d.ellipse((x, 34, x + 84, 118), fill=GOLD)
        text_c(d, x + 42, 38, str(numero), F_TIT(70), (22, 18, 10))
        x += 108
    d.text((x, 30), titolo, font=F_TIT(84), fill=WHITE)
    if piattaforma:
        pf = F_UI(28, 800)
        pw = d.textlength(piattaforma, font=pf) + 44
        rr(d, (W - 44 - pw, 52, W - 44, 102), 25, fill=(40, 34, 20), outline=GOLD, width=2)
        d.text((W - 44 - pw + 22, 59), piattaforma, font=pf, fill=GOLD2)
    if didascalia:
        f = F_UI(38, 700)
        righe = wrap(d, didascalia, f, W - 88)
        for i, r in enumerate(righe[:2]):
            text_c(d, W // 2, 142 + i * 48, r, f, GOLD2)
    if alpha < 1:
        a = lay.getchannel("A").point(lambda v: int(v * alpha))
        lay.putalpha(a)
    fr.alpha_composite(lay, (0, 0))


def angolo_qr(fr):
    fr.alpha_composite(QR_SMALL, (40, H - 40 - QR_SMALL.height - 34))
    d = ImageDraw.Draw(fr)
    text_c(d, 40 + QR_SMALL.width // 2, H - 64, "area30.it", F_UI(24, 800), WHITE)


def passi(fr, attivo):
    d = ImageDraw.Draw(fr)
    x0 = W - 40 - 170
    y = H - 210
    for i, (n, t) in enumerate([(1, "Sito"), (2, "App"), (3, "Notifiche")]):
        yy = y + i * 58
        on = n == attivo
        done = n < attivo
        col = GOLD if on else ((120, 100, 60) if done else (70, 70, 74))
        d.ellipse((x0, yy, x0 + 42, yy + 42), fill=col if (on or done) else None, outline=col, width=3)
        text_c(d, x0 + 21, yy + 2, str(n), F_TIT(32), (22, 18, 10) if (on or done) else col)
        d.text((x0 + 56, yy + 4), t, font=F_UI(26, 800 if on else 600), fill=WHITE if on else MUTED)


def tocco(fr, pos, t):
    """Cerchio che indica dove toccare (t in 0..1 della durata del tocco)."""
    if pos is None:
        return
    x, y = SX + pos[0], SY + pos[1]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    puls = (t * 2.2) % 1
    r2 = 30 + 40 * puls
    d.ellipse((x - r2, y - r2, x + r2, y + r2), outline=(255, 226, 150, int(220 * (1 - puls))), width=5)
    press = 1 - abs(math.sin(t * math.pi * 2.2)) * 0.18
    r = 28 * press
    d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 70), outline=(255, 226, 150, 255), width=4)
    fr.alpha_composite(lay)


def telefono(fr, schermo):
    fr.alpha_composite(FRAME, (PX - 20, PY - 20))
    s = schermo.copy()
    s.putalpha(Image.composite(s.getchannel("A"), Image.new("L", s.size, 0), SCREEN_MASK))
    fr.alpha_composite(s, (SX, SY))


# ------------------------------------------------------------------ precalcolo schermate
SITO_IOS = pagina_sito()
SHARE_POS = safari_bar(SITO_IOS, evid=True)
SHEET, SHEET_POS = ios_sheet()
AGG, AGG_POS = ios_aggiungi()
SITO_AND = pagina_sito(top=66)
MENU_POS = chrome_bar(SITO_AND)
DROPDOWN, DROP_POS = android_menu()
DIALOG, DIALOG_POS = android_dialog()
APP = pagina_sito(app=True)
NSHEET, NSHEET_POS = notify_sheet()
ALERT, ALERT_POS = ios_alert()
TOAST = toast_ok()
HOME_IOS_FULL, AREA_POS_IOS = home()
HOME_AND_FULL, AREA_POS_AND = home(android=True)

def scurisci(im, a=0.45):
    o = im.copy()
    o.alpha_composite(Image.new("RGBA", im.size, (0, 0, 0, int(255 * a))))
    return o


# ------------------------------------------------------------------ scene: (durata s, funzione(fr, t, T))
def sc_intro(fr, t, T):
    a = ease(t / 0.9)
    lg = logo(780)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lay.alpha_composite(lg, ((W - lg.width) // 2, 300 - int(30 * (1 - a))))
    d = ImageDraw.Draw(lay)
    text_c(d, W // 2, 470, "PORTA AREA30", F_TIT(110), WHITE)
    text_c(d, W // 2, 590, "SUL TUO TELEFONO", F_TIT(110), GOLD2)
    text_c(d, W // 2, 760, "App gratuita in 3 passaggi", F_UI(40, 700), WHITE)
    text_c(d, W // 2, 818, "+ avvisi dei nuovi concerti", F_UI(40, 700), MUTED)
    lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    fr.alpha_composite(lay)


def sc_qr(fr, t, T):
    a = ease(t / 0.6)
    intestazione(fr, 1, "VAI SU AREA30.IT", None, "Inquadra il QR con la fotocamera del telefono", a)
    s = 0.85 + 0.15 * ease(t / 0.8)
    q = QR_BIG.resize((int(520 * s), int(520 * s)), Image.LANCZOS)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle((W / 2 - 290, 290, W / 2 + 290, 870), 40, fill=GOLD + (90,))
    fr.alpha_composite(glow.filter(ImageFilter.GaussianBlur(30)))
    fr.alpha_composite(q, ((W - q.width) // 2, 320 + (520 - q.height) // 2))
    d = ImageDraw.Draw(fr)
    text_c(d, W // 2, 880, "oppure scrivi", F_UI(34, 600), MUTED)
    text_c(d, W // 2, 926, "area30.it", F_TIT(96), GOLD2)



def scena_telefono(numero, titolo, piattaforma, passi_n, tappe):
    """tappe: lista di (durata, didascalia, funzione_schermo(t)->(img, pos_tocco_o_None))"""
    tot = sum(x[0] for x in tappe)

    def f(fr, t, T):
        acc = 0
        for i, (dur, cap, fn) in enumerate(tappe):
            if t < acc + dur or i == len(tappe) - 1:
                tl = t - acc
                schermo, pos = fn(tl, dur)
                a = ease(tl / 0.4)
                intestazione(fr, numero, titolo, None, cap, 1.0, piattaforma)
                telefono(fr, schermo)
                if pos is not None and tl > 0.5:
                    tocco(fr, pos, (tl - 0.5) / max(0.6, dur - 0.5))
                angolo_qr(fr)
                passi(fr, passi_n)
                return
            acc += dur
    return tot, f


# --- iPhone
def ios1(t, dur):
    return SITO_IOS, SHARE_POS


def ios2(t, dur):
    s = scurisci(SITO_IOS, 0.4 * ease(t / 0.4))
    off = int(SHEET.height * (1 - ease(t / 0.45)))
    s.alpha_composite(SHEET, (0, SH - SHEET.height + off))
    pos = (SHEET_POS[0], SH - SHEET.height + SHEET_POS[1]) if t > 0.45 else None
    return s, pos


def ios3(t, dur):
    return AGG, AGG_POS


def ios4(t, dur):
    sc = ease(t / 0.6) * (1 + 0.15 * math.sin(min(1, t / 0.6) * math.pi))
    im, _ = home(area_scale=min(1.0, sc) if t < 0.6 else 1.0)
    return im, None


# --- Android
def and1(t, dur):
    return SITO_AND, MENU_POS


def and2(t, dur):
    s = SITO_AND.copy()
    a = ease(t / 0.3)
    dd = DROPDOWN.copy()
    dd.putalpha(dd.getchannel("A").point(lambda v: int(v * a)))
    s.alpha_composite(dd, (SW - DROPDOWN.width - 12, 112))
    return s, ((SW - DROPDOWN.width - 12) + DROP_POS[0], 112 + DROP_POS[1]) if t > 0.3 else None


def and3(t, dur):
    s = scurisci(SITO_AND, 0.55)
    y = (SH - DIALOG.height) // 2
    s.alpha_composite(DIALOG, (30, y))
    return s, (30 + DIALOG_POS[0], y + DIALOG_POS[1])


def and4(t, dur):
    sc = ease(t / 0.6) * (1 + 0.15 * math.sin(min(1, t / 0.6) * math.pi))
    im, _ = home(android=True, area_scale=min(1.0, sc) if t < 0.6 else 1.0)
    return im, None


# --- Notifiche
def not1(t, dur):
    return HOME_IOS_FULL, AREA_POS_IOS


def not2(t, dur):
    s = scurisci(APP, 0.35 * ease((t - 0.3) / 0.5))
    off = int((NSHEET.height + 40) * (1 - ease((t - 0.3) / 0.5)))
    y = SH - NSHEET.height - 28 + off
    s.alpha_composite(NSHEET, (12, y))
    return s, (12 + NSHEET_POS[0], y + NSHEET_POS[1]) if t > 0.8 else None


def not3(t, dur):
    s = scurisci(APP, 0.5)
    y = SH - NSHEET.height - 28
    s.alpha_composite(scurisci(NSHEET, 0.3), (12, y))
    sc = 0.9 + 0.1 * ease(t / 0.3)
    al = ALERT.resize((int(ALERT.width * sc), int(ALERT.height * sc)), Image.LANCZOS)
    ax, ay = (SW - al.width) // 2, (SH - al.height) // 2 - 40
    s.alpha_composite(al, (ax, ay))
    return s, (ax + ALERT_POS[0] * sc, ay + ALERT_POS[1] * sc)


def not4(t, dur):
    s = APP.copy()
    off = int(-120 * (1 - ease(t / 0.4)))
    s.alpha_composite(TOAST, (30, 120 + off))
    return s, None


def sc_finale(fr, t, T):
    a = ease(t / 0.6)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    text_c(d, W // 2, 70, "FATTO!", F_TIT(150), GOLD2)
    text_c(d, W // 2, 250, "Ti avvisiamo noi quando", F_UI(44, 700), WHITE)
    text_c(d, W // 2, 306, "annunciamo un nuovo concerto", F_UI(44, 700), WHITE)
    q = QR_BIG.resize((440, 440), Image.LANCZOS)
    lay.alpha_composite(q, ((W - 440) // 2, 410))
    text_c(d, W // 2, 872, "area30.it", F_TIT(104), GOLD2)
    lg = logo(300)
    lay.alpha_composite(lg, ((W - lg.width) // 2, 1010))
    lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    fr.alpha_composite(lay)


SCENE = [
    (4.0, sc_intro),
    (6.0, sc_qr),
    scena_telefono(2, "INSTALLA L’APP", "iPhone", 2, [
        (3.2, "Apri area30.it con Safari e tocca Condividi", ios1),
        (4.2, "Scegli «Aggiungi alla schermata Home»", ios2),
        (3.6, "Lascia attivo «Apri come app web» e tocca Aggiungi", ios3),
        (2.6, "Ecco l’app AREA30 sul tuo telefono!", ios4),
    ])[::-1],
    scena_telefono(2, "INSTALLA L’APP", "Android", 2, [
        (3.0, "Apri area30.it con Chrome e tocca i tre puntini in alto", and1),
        (3.0, "Scegli «Installa app»", and2),
        (3.0, "Conferma con Installa", and3),
        (2.4, "Fatto: l’app è sul tuo telefono!", and4),
    ])[::-1],
    scena_telefono(3, "ATTIVA LE NOTIFICHE", None, 3, [
        (2.6, "Apri l’app AREA30 dalla schermata Home", not1),
        (3.6, "Tocca «Attiva le notifiche»", not2),
        (3.4, "Tocca Consenti", not3),
        (2.6, "Riceverai gli avvisi dei nuovi concerti", not4),
    ])[::-1],
    (6.5, sc_finale),
]
# (le scene telefono restituiscono (tot, f): sopra sono invertite in (f, tot); le riporto a (durata, funzione))
SCENE = [(s[1], s[0]) if callable(s[0]) else s for s in SCENE]

FADE = 0.35


def render():
    tot = sum(d for d, _ in SCENE)
    n = int(tot * FPS)
    print(f"durata {tot:.1f} s, {n} fotogrammi")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                           "-movflags", "+faststart", str(OUT_MP4)], stdin=subprocess.PIPE)
    starts = []
    acc = 0
    for d, _ in SCENE:
        starts.append(acc)
        acc += d
    for i in range(n):
        t = i / FPS
        k = max(j for j, s in enumerate(starts) if s <= t)
        dur, fn = SCENE[k]
        tl = t - starts[k]
        fr = BGIMG.copy()
        fn(fr, tl, dur)
        # dissolvenza tra le scene
        if tl < FADE and k > 0:
            a = 1 - tl / FADE
            fr = Image.blend(fr, Image.new("RGBA", (W, H), BG + (255,)), a * 0.85)
        if dur - tl < FADE * 0.5 and k == len(SCENE) - 1:
            pass
        ff.stdin.write(fr.convert("RGB").tobytes())
        if i % 300 == 0:
            print(f"  {i}/{n}")
    ff.stdin.close()
    ff.wait()
    print("ok", OUT_MP4)


def anteprime(cartella):
    cartella = Path(cartella)
    cartella.mkdir(exist_ok=True)
    acc = 0
    idx = 0
    for d, fn in SCENE:
        for frac in (0.15, 0.55, 0.9):
            fr = BGIMG.copy()
            fn(fr, d * frac, d)
            fr.convert("RGB").save(cartella / f"f{idx:02d}.jpg", quality=85)
            idx += 1
        acc += d
    print("anteprime", idx)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "anteprime":
        anteprime(QUI / "anteprime")
    else:
        render()
