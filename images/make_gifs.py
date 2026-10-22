"""Render necklace animations for the LeetCode write-up."""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

S = 2                      # supersampling factor
W, H = 520, 648
ROW = 530            # logical panel size
BG = (24, 24, 37)
STRING = (88, 91, 112)
GOLD = (250, 204, 21)
TEXT = (226, 232, 240)
MUTED = (148, 163, 184)
GREEN = (74, 222, 128)
RED = (248, 113, 113)

AV = "/System/Library/Fonts/Avenir Next.ttc"
MENLO = "/System/Library/Fonts/Menlo.ttc"
_fc = {}
def font(size, bold=True, mono=False):
    key = (size, bold, mono)
    if key not in _fc:
        if mono:
            _fc[key] = ImageFont.truetype(MENLO, size * S, index=1 if bold else 0)
        else:
            _fc[key] = ImageFont.truetype(AV, size * S, index=2 if bold else 5)
    return _fc[key]

STOPS = [(56, 189, 248), (129, 140, 248), (232, 121, 249), (251, 113, 133), (251, 191, 36)]
def bead_color(v, n):
    t = v / max(1, n - 1) * (len(STOPS) - 1)
    i = min(int(t), len(STOPS) - 2); f = t - i
    a, b = STOPS[i], STOPS[i + 1]
    return tuple(int(a[k] + (b[k] - a[k]) * f) for k in range(3))

def ease(t): return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t

SYM_CHARS = "↻↺→✓✗"
_sym = {}
def sym_font(f):
    if f.size not in _sym:
        _sym[f.size] = ImageFont.truetype(MENLO, int(f.size * 1.2), index=1)
    return _sym[f.size]

def text_c(d, xy, s, f, fill):
    """Centered text; glyphs the main font lacks are drawn with Apple Symbols."""
    runs = []
    for ch in s:
        fnt = sym_font(f) if ch in SYM_CHARS else f
        if runs and runs[-1][1] is fnt: runs[-1][0] += ch
        else: runs.append([ch, fnt])
    total = sum(fn.getlength(t) for t, fn in runs)
    x = xy[0] * S - total / 2
    for t, fn in runs:
        d.text((x, xy[1] * S), t, font=fn, fill=fill, anchor="lm")
        x += fn.getlength(t)


class Necklace:
    """Beads never move. Only the clasp (gap) and the reading direction change."""

    def __init__(self, nums, title=""):
        self.beads = list(nums)
        self.n = len(nums)
        self.g, self.d = 0, 1
        self.ops = 0
        self.title = title
        self.cx, self.cy, self.R = W / 2, 292, 150
        self.br = max(14, min(30, math.pi * self.R / self.n * 0.62))

    # --- model ---------------------------------------------------------
    def order(self, g=None, d=None):
        g = self.g if g is None else g
        d = self.d if d is None else d
        slots = [(g + k) % self.n for k in range(self.n)] if d == 1 else \
                [(g - 1 - k) % self.n for k in range(self.n)]
        return [self.beads[s] for s in slots]

    def sorted_now(self):
        return self.order() == sorted(self.beads)

    # --- geometry ------------------------------------------------------
    def slot_ang(self, s):  return -90 + s * 360 / self.n
    def gap_ang(self, g):   return -90 + (g - 0.5) * 360 / self.n
    def pt(self, ang, r):
        a = math.radians(ang)
        return self.cx + r * math.cos(a), self.cy + r * math.sin(a)

    def box_x(self, k):
        bw = self.box_w()
        total = self.n * bw + (self.n - 1) * 8
        return W / 2 - total / 2 + bw / 2 + k * (bw + 8)
    def box_w(self): return min(54, (W - 90 - (self.n - 1) * 8) / self.n)

    # --- drawing -------------------------------------------------------
    def draw(self, gap, sweep, boxes, caption, cap_col=TEXT, done=False, links=None):
        im = Image.new("RGB", (W * S, H * S), BG)
        d = ImageDraw.Draw(im)
        n, R, br = self.n, self.R, self.br

        # header
        text_c(d, (W / 2, 34), self.title, font(22), TEXT)
        text_c(d, (W / 2, 64), f"operations: {self.ops}", font(15, mono=True),
               GREEN if done else MUTED)

        # string
        cx, cy = self.cx * S, self.cy * S
        d.ellipse([cx - R * S, cy - R * S, cx + R * S, cy + R * S], outline=STRING, width=4 * S)
        if links:
            for s, col in links:   # colour the string between slot s and s+1
                a0, a1 = self.slot_ang(s), self.slot_ang(s + 1)
                d.arc([cx - R * S, cy - R * S, cx + R * S, cy + R * S], a0, a1, fill=col, width=7 * S)

        # reading-start glow (slides with the clasp, flips with direction)
        ga = self.gap_ang(gap)
        gx, gy = self.pt(ga + sweep * 180 / n, R)
        rr = br + 7
        d.ellipse([(gx - rr) * S, (gy - rr) * S, (gx + rr) * S, (gy + rr) * S],
                  outline=GOLD, width=3 * S)

        # beads
        for s in range(n):
            x, y = self.pt(self.slot_ang(s), R)
            c = bead_color(self.beads[s], n)
            d.ellipse([(x - br) * S, (y - br) * S, (x + br) * S, (y + br) * S],
                      fill=c, outline=(255, 255, 255), width=2 * S)
            text_c(d, (x, y + 1), str(self.beads[s]), font(int(br * 0.85), mono=True), BG)

        # clasp '#'
        x, y = self.pt(ga, R)
        k = 9
        d.polygon([((x) * S, (y - k) * S), ((x + k) * S, y * S), (x * S, (y + k) * S),
                   ((x - k) * S, y * S)], fill=GOLD, outline=BG)
        lx, ly = self.pt(ga, R + br + 22)
        text_c(d, (lx, ly), "#", font(22, mono=True), GOLD)

        # direction arrow (inside the ring)
        ar = R - br - 24
        span = 80 * sweep
        if abs(span) > 6:
            a0, a1 = (ga, ga + span) if span > 0 else (ga + span, ga)
            # stop the arc short so the head sits at the tip
            a0s, a1s = (a0, a1 - 8) if span > 0 else (a0 + 8, a1)
            d.arc([cx - ar * S, cy - ar * S, cx + ar * S, cy + ar * S], a0s, a1s,
                  fill=GOLD, width=5 * S)
            tip_a = ga + span
            tx, ty = self.pt(tip_a, ar)
            sg = 1 if span > 0 else -1
            ta = math.radians(tip_a)
            tvx, tvy = -math.sin(ta) * sg, math.cos(ta) * sg   # tangent
            nvx, nvy = math.cos(ta), math.sin(ta)               # normal
            L, Wd = 16, 9
            bx, by = tx - tvx * L, ty - tvy * L
            d.polygon([(tx * S, ty * S), ((bx + nvx * Wd) * S, (by + nvy * Wd) * S),
                       ((bx - nvx * Wd) * S, (by - nvy * Wd) * S)], fill=GOLD)
        label = "↻ clockwise" if sweep > 0.05 else ("↺ counter-clockwise" if sweep < -0.05 else "")
        text_c(d, (self.cx, self.cy), label, font(15, bold=False), MUTED)

        # array row
        y0 = ROW
        bw = self.box_w()
        text_c(d, (self.box_x(0) - bw / 2 - 18, y0), "#", font(20, mono=True), GOLD)
        for v, x, y in sorted(boxes, key=lambda b: b[2]):  # lifted boxes drawn last
            c = bead_color(v, n)
            d.rounded_rectangle([(x - bw / 2) * S, (y - bw / 2) * S, (x + bw / 2) * S, (y + bw / 2) * S],
                                radius=8 * S, fill=c,
                                outline=GREEN if done else (255, 255, 255), width=(4 if done else 2) * S)
            text_c(d, (x, y + 1), str(v), font(int(bw * 0.42), mono=True), BG)

        text_c(d, (W / 2, 618), caption, font(17), cap_col)
        return im.resize((W, H), Image.LANCZOS)

    def boxes_static(self):
        return [(v, self.box_x(k), ROW) for k, v in enumerate(self.order())]

    # --- animation -----------------------------------------------------
    def hold(self, frames, caption, col=TEXT):
        done = self.sorted_now()
        img = self.draw(self.g, self.d, self.boxes_static(), caption, col, done=done)
        return [img] * frames

    def rotate(self, caption, steps=15):
        out, before = [], self.order()
        n, step = self.n, self.box_w() + 8
        self.ops += 1
        for i in range(1, steps + 1):
            t = ease(i / steps)
            boxes = []
            for k, v in enumerate(before):
                if k == 0:
                    boxes.append((v, lerp(self.box_x(0), self.box_x(n - 1), t), ROW + math.sin(math.pi * t) * 44))
                else:
                    boxes.append((v, self.box_x(k) - step * t, ROW))
            out.append(self.draw(self.g + self.d * t, self.d, boxes, caption))
        self.g = (self.g + self.d) % n
        return out

    def reverse(self, caption, steps=17):
        out, before = [], self.order()
        n = self.n
        self.ops += 1
        for i in range(1, steps + 1):
            t = ease(i / steps)
            boxes = []
            for k, v in enumerate(before):
                x = lerp(self.box_x(k), self.box_x(n - 1 - k), t)
                mid = (n - 1) / 2
                lift = 32 if k < mid else (-32 if k > mid else 0)
                boxes.append((v, x, ROW - math.sin(math.pi * t) * lift))
            out.append(self.draw(self.g, lerp(self.d, -self.d, t), boxes, caption))
        self.d = -self.d
        return out


def save_gif(frames, name, last_hold=60):
    durs = [50] * len(frames)
    durs[-1] = 50 * last_hold
    pal = [f.convert("P", palette=Image.ADAPTIVE, colors=128) for f in frames]
    pal[0].save(os.path.join(OUT, name), save_all=True, append_images=pal[1:],
                duration=durs, loop=0, optimize=True, disposal=1)
    print("wrote", name, len(frames), "frames")


def run(neck, script):
    fr = []
    for op, cap in script:
        if op == "R": fr += neck.rotate(cap)
        elif op == "V": fr += neck.reverse(cap)
        elif op == "H": fr += neck.hold(cap[1], cap[0], cap[2] if len(cap) > 2 else TEXT)
    return fr


# 1. intro: what the two operations really do -----------------------------
nk = Necklace(list(range(6)), "The array is a necklace")
fr = run(nk, [
    ("H", ("beads never move — only the clasp # does", 40)),
    ("R", "Rotate Left: clasp slides 1 bead forward"),
    ("H", ("Rotate Left: clasp slides 1 bead forward", 10)),
    ("R", "Rotate Left: clasp slides 1 bead forward"),
    ("H", ("Rotate Left: clasp slides 1 bead forward", 18)),
    ("V", "Reverse: flip the reading direction"),
    ("H", ("Reverse: flip the reading direction", 22)),
    ("R", "now 'forward' means counter-clockwise"),
    ("H", ("now 'forward' means counter-clockwise", 10)),
    ("R", "now 'forward' means counter-clockwise"),
    ("H", ("now 'forward' means counter-clockwise", 18)),
    ("R", "now 'forward' means counter-clockwise"),
    ("H", ("now 'forward' means counter-clockwise", 18)),
    ("V", "Reverse: flip the reading direction"),
    ("H", ("the necklace itself never changes!", 20, GOLD)),
])
save_gif(fr, "intro.gif")

# 2. examples ------------------------------------------------------------
nk = Necklace([0, 2, 1], "Example 1:  nums = [0, 2, 1]")
fr = run(nk, [
    ("H", ("start", 25)),
    ("R", "Rotate Left"), ("H", ("Rotate Left", 18)),
    ("V", "Reverse"), ("H", ("sorted in 2 operations ✓", 20, GREEN)),
])
save_gif(fr, "example1.gif")

nk = Necklace([1, 0, 2], "Example 2:  nums = [1, 0, 2]")
fr = run(nk, [
    ("H", ("start", 25)),
    ("V", "Reverse"), ("H", ("Reverse", 18)),
    ("R", "Rotate Left"), ("H", ("sorted in 2 operations ✓", 20, GREEN)),
])
save_gif(fr, "example2.gif")

# 3. two routes race, side by side ----------------------------------------
nums = [2, 3, 4, 5, 6, 7, 0, 1]
A = Necklace(nums, "Route A: walk forward")
B = Necklace(nums, "Route B: flip, walk back, flip")
fa = run(A, [("H", ("clasp must reach the gap 7 | 0", 30))] +
            [("R", "Rotate Left")] * 6 + [("H", ("6 operations", 1, MUTED))])
fb = run(B, [("H", ("clasp must reach the gap 7 | 0", 30)),
             ("V", "Reverse")] + [("R", "Rotate Left")] * 2 +
            [("V", "Reverse"), ("H", ("4 operations — winner ✓", 1, GREEN))])
m = max(len(fa), len(fb))
fa += [fa[-1]] * (m - len(fa)); fb += [fb[-1]] * (m - len(fb))
combo = []
for a, b in zip(fa, fb):
    c = Image.new("RGB", (2 * W + 4, H), (49, 50, 68))
    c.paste(a, (0, 0)); c.paste(b, (W + 4, 0))
    combo.append(c)
save_gif(combo, "routes.gif")

# 4. valid vs impossible (static) -----------------------------------------
def links_for(nk):
    n, out = nk.n, []
    for s in range(n):
        a, b = nk.beads[s], nk.beads[(s + 1) % n]
        out.append((s, GREEN if (b - a) % n in (1, n - 1) else RED))
    return out

good = Necklace([2, 3, 0, 1], "nums = [2, 3, 0, 1]")
bad = Necklace([2, 0, 1, 3], "nums = [2, 0, 1, 3]")
ia = good.draw(0, 1, good.boxes_static(), "neighbours all differ by 1 (mod n)  →  sortable ✓", GREEN,
               links=links_for(good))
ib = bad.draw(0, 1, bad.boxes_static(), "2–0 and 1–3 are broken  →  answer -1 ✗", RED,
              links=links_for(bad))
c = Image.new("RGB", (2 * W + 4, H), (49, 50, 68))
c.paste(ia, (0, 0)); c.paste(ib, (W + 4, 0))
c.save(os.path.join(OUT, "valid_vs_invalid.png"))
print("wrote valid_vs_invalid.png")
