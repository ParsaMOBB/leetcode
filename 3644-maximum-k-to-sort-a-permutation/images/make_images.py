"""Render the animations for the 3644 write-up."""
import math, os, sys
from collections import deque
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

S = 2                      # supersampling factor
BG = (24, 24, 37)
SLOT = (49, 50, 68)
EDGE = (88, 91, 112)
DIM = (52, 54, 72)
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
def val_color(v, n):
    t = v / max(1, n - 1) * (len(STOPS) - 1)
    i = min(int(t), len(STOPS) - 2); f = t - i
    a, b = STOPS[i], STOPS[i + 1]
    return tuple(int(a[k] + (b[k] - a[k]) * f) for k in range(3))

def blend(c, k=0.35):
    return tuple(int(BG[i] + (c[i] - BG[i]) * k) for i in range(3))

def ease(t): return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t

SYM_CHARS = "→←↔⇔✓✗≠"
_sym = {}
def sym_font(f):
    if f.size not in _sym:
        _sym[f.size] = ImageFont.truetype(MENLO, int(f.size * 1.1), index=1)
    return _sym[f.size]


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new("RGB", (w * S, h * S), BG)
        self.d = ImageDraw.Draw(self.im)

    def text(self, x, y, s, f, fill, align="c"):
        """Text centred on (x, y); glyphs the main font lacks come from Menlo."""
        runs = []
        for ch in s:
            fnt = sym_font(f) if ch in SYM_CHARS else f
            if runs and runs[-1][1] is fnt: runs[-1][0] += ch
            else: runs.append([ch, fnt])
        total = sum(fn.getlength(t) for t, fn in runs)
        px = x * S - (total / 2 if align == "c" else (total if align == "r" else 0))
        for t, fn in runs:
            self.d.text((px, y * S), t, font=fn, fill=fill, anchor="lm")
            px += fn.getlength(t)

    def circle(self, x, y, r, fill=None, outline=None, width=2):
        self.d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S],
                       fill=fill, outline=outline, width=int(width * S))

    def line(self, a, b, fill, width=3, dash=0):
        if not dash:
            self.d.line([a[0] * S, a[1] * S, b[0] * S, b[1] * S], fill=fill, width=int(width * S))
            return
        L = math.dist(a, b); k = int(L / dash)
        for i in range(0, k, 2):
            p, q = i / k, min(1, (i + 1) / k)
            self.d.line([lerp(a[0], b[0], p) * S, lerp(a[1], b[1], p) * S,
                         lerp(a[0], b[0], q) * S, lerp(a[1], b[1], q) * S], fill=fill, width=int(width * S))

    def box(self, x, y, w, fill, outline=None, width=2, h=None):
        h = h or w
        self.d.rounded_rectangle([(x - w / 2) * S, (y - h / 2) * S, (x + w / 2) * S, (y + h / 2) * S],
                                 radius=8 * S, fill=fill, outline=outline, width=int(width * S))

    def chip(self, x, y, r, v, n, ring=None, ring_w=3, dim=False):
        c = val_color(v, n)
        if dim: c = blend(c, 0.45)
        self.circle(x, y, r, fill=c, outline=ring or (255, 255, 255), width=ring_w if ring else 2)
        self.text(x, y + 1, str(v), font(int(r * 0.9), mono=True), BG)

    def done(self):
        return self.im.resize((self.w, self.h), Image.LANCZOS)


class Row:
    """A horizontal array of boxes, centred on the canvas."""
    def __init__(self, n, W, y, bw, gap):
        self.n, self.y, self.bw, self.gap = n, y, bw, gap
        total = n * bw + (n - 1) * gap
        self.x0 = W / 2 - total / 2 + bw / 2
    def x(self, k): return self.x0 + k * (self.bw + self.gap)


def save_gif(frames, name):
    """frames: list of (image, duration_ms)."""
    ims = [f.convert("P", palette=Image.ADAPTIVE, colors=128) for f, _ in frames]
    ims[0].save(os.path.join(OUT, name), save_all=True, append_images=ims[1:],
                duration=[d for _, d in frames], loop=0, optimize=True, disposal=1)
    print("wrote", name, len(frames), "frames")


# =========================================================================
# 1. lemma: a connected component can be put in any order (peel leaves)
# =========================================================================
def lemma_gif():
    W, H = 560, 640
    P = {0: (110, 180), 1: (230, 255), 2: (125, 375), 3: (375, 235), 4: (470, 140), 5: (450, 370)}
    TREE = [(0, 1), (1, 2), (1, 3), (3, 4), (3, 5)]
    EXTRA = (2, 5)
    N = 6
    row = Row(N, W, 515, 54, 12)
    gc = (290, 260)

    def frame(vals, locked, caption, cap_col=TEXT, leaf=None, path=(), swap=None,
              extra="solid", final=False):
        c = Canvas(W, H)
        c.text(W / 2, 34, "Lemma: a connected component can be sorted", font(20), TEXT)
        c.text(W / 2, 62, "cells = vertices   ·   allowed swaps = edges", font(14, bold=False), MUTED)

        # edges
        if extra:
            c.line(P[EXTRA[0]], P[EXTRA[1]], EDGE, 3, dash=10 if extra == "dashed" else 0)
        pe = set(frozenset(e) for e in zip(path, path[1:]))
        for a, b in TREE:
            if a in locked or b in locked:
                c.line(P[a], P[b], DIM, 2, dash=6)
            elif frozenset((a, b)) in pe:
                c.line(P[a], P[b], GOLD, 6)
            else:
                c.line(P[a], P[b], EDGE, 4)

        # empty slots + cell labels
        for i, (x, y) in P.items():
            c.circle(x, y, 28, fill=SLOT, outline=EDGE, width=2)
            dx, dy = x - gc[0], y - gc[1]; L = math.hypot(dx, dy)
            c.text(x + dx / L * 50, y + dy / L * 50, f"cell {i}", font(13, bold=False), MUTED)
        if leaf is not None:
            x, y = P[leaf]
            c.circle(x, y, 37, outline=GOLD, width=3)

        # values on the graph
        t = ease(swap[0]) if swap else 0
        su, sv = (swap[1], swap[2]) if swap else (None, None)
        order = sorted(range(N), key=lambda i: i in (su, sv))
        for i in order:
            v = vals[i]
            x, y = P[i]
            if i == su: x, y = lerp(P[su][0], P[sv][0], t), lerp(P[su][1], P[sv][1], t)
            if i == sv: x, y = lerp(P[sv][0], P[su][0], t), lerp(P[sv][1], P[su][1], t)
            ring = GREEN if (i in locked or final) and not swap else None
            c.chip(x, y, 24, v, N, ring=ring, ring_w=4)

        # the same state as an array
        c.text(row.x(0) - row.bw / 2 - 30, row.y, "array", font(14, bold=False), MUTED, align="c")
        for i in order:
            v = vals[i]
            x, y = row.x(i), row.y
            if swap and i in (su, sv):
                j = sv if i == su else su
                x = lerp(row.x(i), row.x(j), t)
                y = row.y - math.sin(math.pi * t) * (36 if i < j else -36)
            done = (i in locked or final) and not swap
            c.box(x, y, row.bw, val_color(v, N), GREEN if done else (255, 255, 255), 4 if done else 2)
            c.text(x, y + 1, str(v), font(22, mono=True), BG)
        for i in range(N):
            c.text(row.x(i), row.y + row.bw / 2 + 16, str(i), font(13, bold=False), MUTED)

        c.text(W / 2, 612, caption, font(17), cap_col)
        return c.done()

    def tree_path(src, dst, alive):
        adj = {i: [] for i in alive}
        for a, b in TREE:
            if a in alive and b in alive:
                adj[a].append(b); adj[b].append(a)
        prev = {src: None}; q = deque([src])
        while q:
            u = q.popleft()
            for w in adj[u]:
                if w not in prev: prev[w] = u; q.append(w)
        p = [dst]
        while p[-1] != src: p.append(prev[p[-1]])
        return p[::-1]

    vals = [4, 5, 0, 2, 1, 3]
    locked = set()
    fr = []
    fr += [(frame(vals, locked, "an allowed swap = an edge between two cells"), 2200)]
    fr += [(frame(vals, locked, "only a spanning tree is needed: drop the dashed edge",
                  extra="dashed"), 2200)]
    for leaf in [0, 2, 4, 5, 1, 3]:
        alive = set(range(N)) - locked
        if len(alive) == 1:
            fr += [(frame(vals, locked, f"last cell: it can only hold {leaf} ✓", GREEN,
                          leaf=leaf, extra="dashed"), 1300)]
            locked.add(leaf)
            break
        src = vals.index(leaf)
        path = tree_path(src, leaf, alive)
        if len(path) == 1:
            fr += [(frame(vals, locked, f"leaf {leaf} already holds {leaf}", GOLD,
                          leaf=leaf, extra="dashed"), 1300)]
        else:
            fr += [(frame(vals, locked, f"leaf {leaf} wants value {leaf}: walk it along the path",
                          leaf=leaf, path=path, extra="dashed"), 1300)]
            for u, v in zip(path, path[1:]):
                for k in range(1, 15):
                    fr += [(frame(vals, locked, f"swap cells {u} and {v}", leaf=leaf, path=path,
                                  swap=(k / 14, u, v), extra="dashed"), 50)]
                vals[u], vals[v] = vals[v], vals[u]
                fr += [(frame(vals, locked, f"swap cells {u} and {v}", leaf=leaf, path=path,
                              extra="dashed"), 250)]
        locked.add(leaf)
        fr += [(frame(vals, locked, f"lock cell {leaf}: what is left is still a tree", leaf=leaf,
                      extra="dashed"), 1200)]
    fr += [(frame(vals, locked, "sorted ✓  every value reached its own cell", GREEN,
                  extra="dashed", final=True), 3500)]
    save_gif(fr, "lemma.gif")


# =========================================================================
# 2. the swap rule talks about values, so work on pos = nums^-1
# =========================================================================
def inverse_gif():
    W, H = 560, 500
    N = 6
    rn = Row(N, W, 170, 56, 12)
    rp = Row(N, W, 345, 56, 12)

    def frame(nums, caption, cap_col=TEXT, hl=(), swap=None, final=False):
        pos = [0] * N
        for i, v in enumerate(nums): pos[v] = i
        c = Canvas(W, H)
        c.text(W / 2, 34, "Swaps act on values: work on pos instead", font(20), TEXT)
        c.text(W / 2, 62, "k = 1", font(15, mono=True), GOLD)

        t = ease(swap[0]) if swap else 0
        a, b = swap[1:] if swap else (None, None)      # the two VALUES being swapped

        # nums: box i holds nums[i], coloured by the value
        c.text(W / 2, rn.y - 72, "nums[i]   (cell = index i)", font(14, bold=False), MUTED)
        ia, ib = (nums.index(a), nums.index(b)) if swap else (None, None)
        for i in sorted(range(N), key=lambda i: i in (ia, ib)):
            v = nums[i]; x, y = rn.x(i), rn.y
            if swap and i in (ia, ib):
                j = ib if i == ia else ia
                x = lerp(rn.x(i), rn.x(j), t)
                y = rn.y - math.sin(math.pi * t) * (34 if i < j else -34)
            c.box(x, y, rn.bw, val_color(v, N), GREEN if final else (255, 255, 255), 4 if final else 2)
            c.text(x, y + 1, str(v), font(22, mono=True), BG)
            if v in hl and not swap:
                c.box(x, y, rn.bw + 12, None, GOLD, 3)
        for i in range(N):
            c.text(rn.x(i), rn.y + 46, f"i={i}", font(12, bold=False), MUTED)

        # pos: cell v (coloured like value v) holds pos[v]; the cells stay put
        c.text(W / 2, rp.y - 72, "pos[v]   (cell = value v)", font(14, bold=False), MUTED)
        for v in range(N):
            c.box(rp.x(v), rp.y, rp.bw, SLOT, val_color(v, N), 4)
            if v in hl and not swap:
                c.box(rp.x(v), rp.y, rp.bw + 12, None, GOLD, 3)
        for v in range(N):
            x, y = rp.x(v), rp.y
            if swap and v in (a, b):
                u = b if v == a else a
                x = lerp(rp.x(v), rp.x(u), t)
                y = rp.y - math.sin(math.pi * t) * (34 if v < u else -34)
            c.text(x, y + 1, str(pos[v]), font(22, mono=True), GREEN if final else TEXT)
        for v in range(N):
            c.text(rp.x(v), rp.y + 46, f"v={v}", font(12, bold=False), val_color(v, N))

        c.text(W / 2, 455, caption, font(17), cap_col)
        return c.done()

    nums = [0, 3, 2, 5, 4, 1]
    fr = [(frame(nums, "pos[v] = the index where value v sits"), 2600)]
    for a, b in [(1, 3), (3, 5)]:
        fr += [(frame(nums, f"swap values {a} and {b}:  {a} & {b} = {a & b} = k ✓", hl=(a, b)), 1700)]
        for k in range(1, 19):
            fr += [(frame(nums, f"swap values {a} and {b}:  {a} & {b} = {a & b} = k ✓",
                          swap=(k / 18, a, b)), 50)]
        ia, ib = nums.index(a), nums.index(b)
        nums[ia], nums[ib] = nums[ib], nums[ia]
        fr += [(frame(nums, f"in pos it is just: swap cells {a} and {b}", GOLD, hl=(a, b)), 2000)]
    fr += [(frame(nums, "nums sorted  ⇔  pos sorted ✓", GREEN, final=True), 3500)]
    save_gif(fr, "inverse.gif")


# =========================================================================
# 3. the AND of all misplaced values (static)
# =========================================================================
NUMS12 = [0, 1, 11, 6, 4, 5, 2, 10, 8, 9, 3, 7]

def and_png():
    W, H = 560, 520
    N = len(NUMS12)
    mis = [v for i, v in enumerate(NUMS12) if v != i]
    k = 0b1111
    for v in mis: k &= v
    c = Canvas(W, H)
    c.text(W / 2, 34, "k = AND of every misplaced value", font(20), TEXT)
    c.text(W / 2, 62, "nums = [0, 1, 11, 6, 4, 5, 2, 10, 8, 9, 3, 7]", font(13, mono=True), MUTED)

    RH, top = 40, 130
    xs = [260 + j * 56 for j in range(4)]                 # bit 3 .. bit 0
    # highlight the surviving column
    for j in range(4):
        if k >> (3 - j) & 1:
            span = len(mis) * RH + 4
            c.box(xs[j], top + span / 2, 46, (30, 64, 46), GREEN, 2, h=span + RH)
    for j, b in enumerate([8, 4, 2, 1]):
        c.text(xs[j], top - 30, str(b), font(14, bold=False), MUTED)
    for r, v in enumerate(mis):
        y = top + r * RH
        c.chip(130, y, 16, v, N)
        c.text(165, y, "=", font(16, bold=False), MUTED)
        for j in range(4):
            bit = v >> (3 - j) & 1
            c.text(xs[j], y, str(bit), font(20, mono=True), TEXT if bit else blend(TEXT, 0.35))
    y = top + len(mis) * RH
    c.line((100, y - RH / 2 + 2), (W - 80, y - RH / 2 + 2), EDGE, 2)
    y += 4
    c.text(130, y, "AND", font(16), GOLD)
    c.text(165, y, "=", font(16, bold=False), MUTED)
    for j in range(4):
        bit = k >> (3 - j) & 1
        c.text(xs[j], y, str(bit), font(20, mono=True), GREEN if bit else RED)
    c.text(xs[3] + 60, y, f"= {k}", font(20, mono=True), GREEN)

    c.text(W / 2, 450, "a bit survives only if every misplaced value has it", font(16), TEXT)
    c.text(W / 2, 482, "fixed values (0, 1, 4, 5, 8, 9) are not in the AND", font(14, bold=False), MUTED)
    c.done().save(os.path.join(OUT, "and_table.png"))
    print("wrote and_table.png")


# =========================================================================
# 4. k itself is a hub: sort the example by swapping only through k
# =========================================================================
def hub_gif():
    W, H = 600, 690
    N = len(NUMS12)
    K = 2
    sup = [v for v in range(N) if v & K == K and v != K]          # 3 6 7 10 11
    iso = [v for v in range(N) if v & K != K]                     # 0 1 4 5 8 9
    hub = (W / 2, 255)
    P = {K: hub}
    for j, v in enumerate(sup):
        a = math.radians(-90 + j * 360 / len(sup))
        P[v] = (hub[0] + 135 * math.cos(a), hub[1] + 135 * math.sin(a))
    for j, v in enumerate(iso):
        P[v] = (W / 2 + (j - (len(iso) - 1) / 2) * 62, 465)
    real = [(a, b) for a in [K] + sup for b in [K] + sup if a < b and a & b == K]
    row = Row(N, W, 565, 38, 7)

    def frame(nums, caption, cap_col=TEXT, edge=None, swap=None, hl_iso=False, final=False):
        c = Canvas(W, H)
        c.text(W / 2, 34, "k = 2: every misplaced value is adjacent to k", font(20), TEXT)
        c.text(W / 2, 62, "edge a — b  ⇔  a & b = 2", font(14, mono=True), MUTED)

        for a, b in real:
            if edge and {a, b} == set(edge):
                c.line(P[a], P[b], GOLD, 7)
            elif K in (a, b):
                c.line(P[a], P[b], EDGE, 4)
            else:
                c.line(P[a], P[b], DIM, 2)
        if edge:
            c.line(P[edge[0]], P[edge[1]], GOLD, 7)

        c.text(W / 2, 425, "x & 2 ≠ 2  →  no edges at all", font(13, bold=False),
               GOLD if hl_iso else MUTED)
        for v in range(N):
            x, y = P[v]
            home = nums[v] == v
            if v in iso:
                c.chip(x, y, 19, v, N, ring=GREEN if home else RED, ring_w=3, dim=True)
            else:
                ring = GOLD if edge and v in edge else (GREEN if home else None)
                c.chip(x, y, 26 if v == K else 23, v, N, ring=ring, ring_w=4)
        if hl_iso:
            c.box(W / 2, 465, len(iso) * 62 + 10, None, GOLD, 2, h=56)

        t = ease(swap[0]) if swap else 0
        a, b = swap[1:] if swap else (None, None)
        ia, ib = (nums.index(a), nums.index(b)) if swap else (None, None)
        for i in sorted(range(N), key=lambda i: i in (ia, ib)):
            v = nums[i]; x, y = row.x(i), row.y
            if swap and i in (ia, ib):
                j = ib if i == ia else ia
                x = lerp(row.x(i), row.x(j), t)
                y = row.y - math.sin(math.pi * t) * (30 if i < j else -30)
            home = v == i and not swap
            col = val_color(v, N) if v not in iso else blend(val_color(v, N), 0.45)
            c.box(x, y, row.bw, col, GREEN if home else (255, 255, 255), 3 if home else 2)
            c.text(x, y + 1, str(v), font(16, mono=True), BG)
        for i in range(N):
            c.text(row.x(i), row.y + 33, str(i), font(11, bold=False), MUTED)

        c.text(W / 2, 655, caption, font(17), cap_col)
        return c.done()

    nums = list(NUMS12)
    fr = [(frame(nums, "values that do not contain k = 2 are isolated", hl_iso=True), 2400)]
    fr += [(frame(nums, "so they must already be in place", GREEN, hl_iso=True), 2000)]
    fr += [(frame(nums, "every other value contains k, hence is adjacent to k"), 2600)]
    while nums != sorted(nums):
        p = nums.index(K)
        other = p if p != K else next(v for i, v in enumerate(nums) if v != i and v != K)
        cap = f"swap {K} ↔ {other}   ({K} & {other} = {K & other} ✓)"
        fr += [(frame(nums, cap, edge=(K, other)), 900)]
        for s in range(1, 17):
            fr += [(frame(nums, cap, edge=(K, other), swap=(s / 16, K, other)), 50)]
        ia, ib = nums.index(K), nums.index(other)
        nums[ia], nums[ib] = nums[ib], nums[ia]
        fr += [(frame(nums, f"{other} is in place", GREEN), 700)]
    fr += [(frame(nums, "sorted ✓  answer: k = 2", GREEN, final=True), 3500)]
    save_gif(fr, "hub_sort.gif")


lemma_gif()
inverse_gif()
and_png()
hub_gif()
