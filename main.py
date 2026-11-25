#!/usr/bin/env python3
"""Draw the front page of Wednesday 25 November 2026 as one image.

Pure standard library: the picture is rasterised into a byte buffer and
encoded as PNG by hand (zlib + struct), so the program runs anywhere
Python 3.13 runs, with no network, no fonts and no image files.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# --- palette ---------------------------------------------------------------
PAPER = (247, 242, 231)
CARD = (255, 253, 246)
INK = (26, 32, 54)
NAVY = (18, 32, 62)
GOLD = (201, 162, 39)
RED = (178, 44, 38)
TEAL = (13, 106, 106)
GREEN = (46, 125, 60)
ORANGE = (204, 102, 26)
SLATE = (52, 58, 74)
SKY = (70, 110, 160)
SEA = (36, 96, 140)
PALE = (190, 215, 230)
SAND = (232, 214, 176)
GREY = (96, 101, 112)
WHITE = (255, 255, 255)
DARK = (30, 34, 44)
BRICK = (176, 74, 58)

# --- 5x7 pixel font ---------------------------------------------------------
# Each glyph is 7 rows; each row is a 5-bit number, bit 4 = leftmost pixel.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x15, 0x0A),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ",": (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    ":": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    ";": (0, 0x0C, 0x0C, 0, 0x0C, 0x04, 0x08),
    "-": (0, 0, 0, 0x0E, 0, 0, 0),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0, 0x04),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    "%": (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "+": (0, 0x04, 0x04, 0x1F, 0x04, 0x04, 0),
    "=": (0, 0, 0x1F, 0, 0x1F, 0, 0),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    "\u2022": (0, 0x04, 0x0E, 0x0E, 0x0E, 0x04, 0),
}


class Canvas:
    """A plain RGB raster with a few drawing helpers."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            o = (y * self.w + x) * 3
            self.buf[o:o + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            o = (yy * self.w + x0) * 3
            self.buf[o:o + len(row)] = row

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.rect(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.rect(cx - dx, cy + dy, 2 * dx + 1, 1, c)

    def ring(self, cx, cy, r, c, t=2):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                if r - t <= d <= r:
                    self.set(xx, yy, c)

    def poly(self, pts, c):
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if (y1 <= y < y2) or (y2 <= y < y1):
                    xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.rect(int(xs[i]), y, int(xs[i + 1]) - int(xs[i]) + 1, 1, c)

    def frame(self, x, y, w, h, c, t=2):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)


def clean(text):
    return (text.upper()
            .replace("\u2014", "-").replace("\u2013", "-")
            .replace("\u2019", "'").replace("\u201c", '"')
            .replace("\u201d", '"'))


def draw_text(cv, x, y, text, scale, color):
    cx = x
    for ch in clean(text):
        g = FONT.get(ch)
        if g is None:
            cx += 6 * scale
            continue
        for r in range(7):
            bits = g[r]
            for col in range(5):
                if bits & (1 << (4 - col)):
                    cv.rect(cx + col * scale, y + r * scale, scale, scale, color)
        cx += 6 * scale
    return cx


def text_width(text, scale):
    return len(clean(text)) * 6 * scale


def draw_centered(cv, cx, y, text, scale, color):
    draw_text(cv, cx - text_width(text, scale) // 2, y, text, scale, color)


def wrap(text, scale, maxw):
    lines, cur = [], ""
    for word in clean(text).split():
        trial = (cur + " " + word).strip()
        if text_width(trial, scale) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def text_block(cv, x, y, text, scale, maxw, color, leading=None):
    lh = leading if leading is not None else 9 * scale
    for line in wrap(text, scale, maxw):
        draw_text(cv, x, y, line, scale, color)
        y += lh
    return y


# --- picture strips ---------------------------------------------------------

def scene_storefront(cv, x, y, w, h):
    """A supermarket front: sign band, striped awning, door, windows."""
    cv.rect(x, y, w, h, SAND)
    bx, bw = x + 14, w - 28
    cv.rect(bx, y + 34, bw, h - 44, BRICK)
    cv.rect(bx, y + 34, bw, 30, NAVY)
    draw_centered(cv, bx + bw // 2, y + 42, "MARKET", 3, WHITE)
    for i in range(9):
        col = WHITE if i % 2 == 0 else RED
        cv.rect(bx + 8 + i * (bw - 16) // 9, y + 70, (bw - 16) // 9, 22, col)
    cv.rect(bx, y + 70, bw, 4, INK)
    cv.rect(bx + 18, y + 108, 62, 66, PALE)
    cv.rect(bx + 20, y + 110, 58, 62, PALE)
    cv.vline(bx + 49, y + 110, 62, INK, 2)
    cv.hline(bx + 20, y + 141, 58, INK, 2)
    dx = bx + bw // 2 - 30
    cv.rect(dx, y + 108, 60, 66, DARK)
    cv.rect(dx + 4, y + 112, 52, 58, (64, 74, 96))
    cv.vline(dx + 30, y + 112, 58, DARK, 3)
    cv.rect(bx + bw - 80, y + 108, 62, 66, PALE)
    cv.vline(bx + bw - 49, y + 110, 62, INK, 2)
    cv.hline(bx + bw - 80, y + 141, 62, INK, 2)
    for fx, fc in ((bx + 52, INK), (bx + 118, RED), (bx + bw - 96, INK)):
        cv.disc(fx, y + h - 34, 7, fc)
        cv.rect(fx - 8, y + h - 26, 16, 24, fc)
    cv.disc(x + w - 26, y + 26, 17, RED)
    draw_centered(cv, x + w - 26, y + 17, "!", 3, WHITE)


def scene_satellite(cv, x, y, w, h):
    cv.rect(x, y, w, h, NAVY)
    for sx, sy in ((14, 12), (52, 30), (96, 10), (150, 26), (210, 12),
                   (250, 34), (34, 48), (180, 46), (120, 40)):
        cv.rect(x + sx, y + sy, 3, 3, WHITE)
    cx, cy = x + w // 2, y + h // 2 - 4
    cv.rect(cx - 58, cy - 8, 34, 16, SKY)
    cv.rect(cx + 24, cy - 8, 34, 16, SKY)
    cv.rect(cx - 20, cy - 12, 40, 24, GOLD)
    cv.line(cx + 14, cy - 12, cx + 30, cy - 18, WHITE, 2)
    cv.disc(cx + 32, cy - 18, 4, WHITE)
    # Earth as a cap along the bottom edge, clipped to the strip.
    cx, cy, r = x + 34, y + h + 16, 30
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                cv.set(xx, yy, SEA)


def scene_tanker(cv, x, y, w, h):
    cv.rect(x, y, w, h, PALE)
    cv.rect(x, y + 28, w, h - 28, SEA)
    cv.rect(x, y + 28, w, 2, WHITE)
    cv.poly([(x + 30, y + 34), (x + w - 30, y + 34),
             (x + w - 52, y + 16), (x + 52, y + 16)], DARK)
    for i, col in enumerate((RED, GOLD, TEAL)):
        cv.rect(x + 78 + i * 52, y + 4, 46, 12, col)
    cv.rect(x + w - 118, y + 6, 8, 10, DARK)
    cv.disc(x + w - 114, y + 3, 5, ORANGE)
    cv.disc(x + w - 114, y + 3, 3, RED)
    for mx in (44, 150, 252):
        cv.disc(x + mx, y + 44, 3, INK)
        cv.rect(x + mx - 5, y + 42, 10, 2, INK)
    cv.rect(x + 12, y + 46, 26, 2, WHITE)
    cv.rect(x + w - 40, y + 40, 26, 2, WHITE)


def scene_probe(cv, x, y, w, h):
    cv.rect(x, y, w, h, (226, 228, 232))
    bx, bw = x + 66, w - 132
    cv.rect(bx, y + 6, bw, 6, SLATE)
    cv.rect(bx + 10, y + 12, bw - 20, h - 24, SLATE)
    for i in range(4):
        cv.rect(bx + 18 + i * ((bw - 36) // 3), y + 16, 10, h - 30, WHITE)
    cv.rect(bx - 8, y + h - 8, bw + 16, 5, SLATE)
    cv.ring(x + w - 46, y + 20, 13, GOLD, 3)
    cv.line(x + w - 35, y + 30, x + w - 20, y + 45, GOLD, 4)


def scene_chip(cv, x, y, w, h):
    cv.rect(x, y, w, h, DARK)
    cx, cy = x + w // 2, y + h // 2
    for i in range(5):
        cv.rect(cx - 22 + i * 11, cy - 26, 5, 6, GOLD)
        cv.rect(cx - 22 + i * 11, cy + 20, 5, 6, GOLD)
        cv.rect(cx - 26, cy - 22 + i * 11, 6, 5, GOLD)
        cv.rect(cx + 20, cy - 22 + i * 11, 6, 5, GOLD)
    cv.rect(cx - 20, cy - 20, 40, 40, (16, 18, 26))
    cv.frame(cx - 20, cy - 20, 40, 40, GOLD, 2)
    cv.rect(cx - 9, cy - 9, 18, 18, TEAL)


def scene_globe(cv, x, y, w, h):
    cv.rect(x, y, w, h, PALE)
    cx, cy = x + 52, y + h // 2
    cv.disc(cx, cy, 22, SEA)
    cv.disc(cx - 7, cy - 7, 8, GREEN)
    cv.rect(cx - 2, cy - 10, 11, 6, GREEN)
    cv.disc(cx + 7, cy + 9, 7, GREEN)
    cv.rect(cx - 22, cy + 2, 44, 3, (120, 160, 190))
    cv.ring(x + w - 42, cy, 17, RED, 4)
    cv.line(x + w - 54, cy - 12, x + w - 30, cy + 12, RED, 4)


# --- page -------------------------------------------------------------------

def tile(cv, x, y, w, h, tag, tag_color, headline, body, scene):
    cv.rect(x, y, w, h, INK)
    cv.rect(x + 2, y + 2, w - 4, h - 4, CARD)
    cv.rect(x + 2, y + 2, w - 4, 30, tag_color)
    draw_text(cv, x + 14, y + 10, tag, 2, WHITE)
    scene(cv, x + 10, y + 38, w - 20, 52)
    after = text_block(cv, x + 14, y + 100, headline, 3, w - 28, INK, 22)
    text_block(cv, x + 14, after + 6, body, 2, w - 28, SLATE, 14)


def build():
    cv = Canvas(W, H, PAPER)

    # Masthead.
    cv.rect(0, 0, W, 172, NAVY)
    draw_centered(cv, W // 2, 20, "MAKE.FUN - ONE DAY IN ONE IMAGE", 2, GOLD)
    draw_centered(cv, W // 2, 52, "WORLD NEWS", 8, WHITE)
    draw_centered(cv, W // 2, 124, "WEDNESDAY 25 NOVEMBER 2026", 3, GOLD)
    cv.rect(0, 172, W, 4, GOLD)

    # Lead story: Cartagena hostage standoff.
    lx, ly, lw, lh = 24, 184, 976, 286
    cv.rect(lx, ly, lw, lh, INK)
    cv.rect(lx + 2, ly + 2, lw - 4, lh - 4, CARD)
    cv.rect(lx + 2, ly + 2, lw - 4, 6, RED)
    draw_text(cv, lx + 24, ly + 22, "COLOMBIA - LEAD STORY", 2, RED)
    draw_text(cv, lx + 24, ly + 52, "HOSTAGES SEIZED", 5, INK)
    draw_text(cv, lx + 24, ly + 94, "IN CARTAGENA", 5, INK)
    text_block(cv, lx + 24, ly + 152,
               "ARMED MEN TOOK AT LEAST 30 PEOPLE HOSTAGE IN A "
               "CARTAGENA SUPERMARKET AFTER A FAILED CASH-TRUCK "
               "ROBBERY. FIVE ELDERLY WOMEN WERE FREED.",
               2, 592, SLATE, 16)
    draw_text(cv, lx + 24, ly + 226, "AT LEAST 30 HELD - 5 FREED", 2, RED)
    scene_storefront(cv, lx + 640, ly + 16, 312, 254)

    # Row one: space, Hormuz, China.
    tile(cv, 24, 486, 312, 240, "SPACE - NATO", NAVY,
         "NATO VOWS TO GUARD SPACE",
         "REPORTS SAY RUSSIA IS READYING A NUCLEAR-ARMED "
         "SATELLITE FOR LAUNCH, MAYBE IN DECEMBER.",
         scene_satellite)
    tile(cv, 356, 486, 312, 240, "HORMUZ - ENERGY", TEAL,
         "MINES HIT TANKERS IN HORMUZ",
         "THREE OIL TANKERS HIT BY NAVAL MINES; A HOUTHI DRONE "
         "STRUCK A RIYADH TOWER, HURTING 11.",
         scene_tanker)
    tile(cv, 688, 486, 312, 240, "CHINA - POLITICS", RED,
         "SHANGHAI CHIEF UNDER PROBE",
         "BEIJING OPENS A SHOCK CORRUPTION INQUIRY INTO "
         "SHANGHAI PARTY LEADER CHEN JINING.",
         scene_probe)

    # Row two: tech, climate, also today.
    tile(cv, 24, 742, 312, 226, "TECH - USA", DARK,
         "HUAWEI GUILTY IN US TRIAL",
         "A US JURY FOUND HUAWEI GUILTY OF STEALING TRADE "
         "SECRETS, BUT CLEARED IT OF RACKETEERING.",
         scene_chip)
    tile(cv, 356, 742, 312, 226, "CLIMATE - SUMMIT", GREEN,
         "CLIMATE SUMMIT ENDS IN FAILURE",
         "MORE THAN 190 NATIONS LEFT THE TURKEY SUMMIT WITH "
         "NO FINAL AGREEMENT.",
         scene_globe)

    ax, ay, aw, ah = 688, 742, 312, 226
    cv.rect(ax, ay, aw, ah, INK)
    cv.rect(ax + 2, ay + 2, aw - 4, ah - 4, CARD)
    cv.rect(ax + 2, ay + 2, aw - 4, 30, GREY)
    draw_text(cv, ax + 14, ay + 10, "ALSO TODAY", 2, WHITE)
    by = ay + 44
    for item in ("SEOUL - EDUCATION MINISTER QUITS OVER "
                 "EXAM-CHEATING SCANDAL",
                 "CANBERRA - AUSTRALIA SIGNS SECURITY PACT "
                 "WITH SOLOMON ISLANDS",
                 "THE HAGUE - COURT KEEPS DUTCH CLIMATE "
                 "TARGETS BINDING"):
        by = text_block(cv, ax + 14, by, "\u2022 " + item, 2, aw - 28,
                        SLATE, 15)
        by += 8

    # Footer.
    draw_centered(cv, W // 2, 994,
                  "DRAWN FROM REPORTS OF WEDNESDAY 25 NOVEMBER 2026 - MAKE.FUN",
                  2, GREY)
    return cv


def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.buf[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(build())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
