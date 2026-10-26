"""Render the images for the 1254 write-up."""
import math, os, random, sys
from collections import deque
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

S = 2                      # supersampling factor
BG = (24, 24, 37)
SLOT = (49, 50, 68)
EDGE = (88, 91, 112)
GOLD = (250, 204, 21)
TEXT = (226, 232, 240)
MUTED = (148, 163, 184)
GREEN = (74, 222, 128)

WATER = (34, 92, 150)
WAVE = (92, 160, 222)
LAND = (128, 168, 86)
LAND_DK = (100, 138, 62)
LAND_LT = (172, 206, 120)
OPEN_K = 0.5               # how much of the colour an open (border) land tile keeps

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

def blend(c, k=0.35):
    return tuple(int(BG[i] + (c[i] - BG[i]) * k) for i in range(3))

def ease(t): return t * t * (3 - 2 * t)

SYM_CHARS = "→←↓✓✗×−"
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

    def line(self, a, b, fill, width=3):
        self.d.line([a[0] * S, a[1] * S, b[0] * S, b[1] * S], fill=fill, width=int(width * S))

    def box(self, x, y, w, fill, outline=None, width=2, h=None, r=8):
        h = h or w
        self.d.rounded_rectangle([(x - w / 2) * S, (y - h / 2) * S, (x + w / 2) * S, (y + h / 2) * S],
                                 radius=r * S, fill=fill, outline=outline, width=int(width * S))

    def arrow(self, a, b, fill, width=3, head=10):
        self.line(a, b, fill, width)
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        p1 = (b[0] - head * math.cos(ang - 0.45), b[1] - head * math.sin(ang - 0.45))
        p2 = (b[0] - head * math.cos(ang + 0.45), b[1] - head * math.sin(ang + 0.45))
        self.d.polygon([(b[0] * S, b[1] * S), (p1[0] * S, p1[1] * S), (p2[0] * S, p2[1] * S)], fill=fill)

    def done(self):
        return self.im.resize((self.w, self.h), Image.LANCZOS)


def save_gif(frames, name):
    """frames: list of (image, duration_ms)."""
    # one palette for every frame, so flat colours (text, background) do not shift between frames
    sheet = Image.new("RGB", (frames[0][0].width, frames[0][0].height * 3))
    for k, idx in enumerate((0, len(frames) // 2, -1)):
        sheet.paste(frames[idx][0], (0, k * frames[0][0].height))
    pal = sheet.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    ims = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f, _ in frames]
    ims[0].save(os.path.join(OUT, name), save_all=True, append_images=ims[1:],
                duration=[d for _, d in frames], loop=0, optimize=True, disposal=1)
    print("wrote", name, len(frames), "frames")


# =========================================================================
# textured tiles
# =========================================================================
def tile(c, x, y, s, kind, seed, k=1.0, scale=1.0):
    """One cell centred on (x, y) with side s. kind: 'water' or 'land'.
    k < 1 darkens the tile towards the background (land joined to the border)."""
    col = (lambda q: blend(q, k)) if k < 1 else (lambda q: q)
    s = s * scale
    if s < 2: return
    rnd = random.Random(seed)
    h = s / 2 - 1
    if kind == "water":
        c.box(x, y, 2 * h, col(WATER), r=5 * scale)
        ph = rnd.uniform(0, 2 * math.pi)
        for fy in (-0.28, 0.08, 0.42):
            pts = []
            for t in range(13):
                px = x - h * 0.72 + t / 12 * h * 1.44
                py = y + fy * h + math.sin(ph + t / 12 * 2 * math.pi * 1.5) * h * 0.09
                pts.append((px * S, py * S))
            c.d.line(pts, fill=col(WAVE), width=max(1, int(1.6 * scale * S)), joint="curve")
            ph += 1.7
    else:
        c.box(x, y, 2 * h, col(LAND), r=5 * scale)
        for _ in range(7):
            px = x + rnd.uniform(-0.7, 0.7) * h
            py = y + rnd.uniform(-0.7, 0.7) * h
            r = rnd.uniform(0.05, 0.09) * h * 2
            c.circle(px, py, r, fill=col(LAND_DK if rnd.random() < 0.6 else LAND_LT))
        for _ in range(2):
            px = x + rnd.uniform(-0.5, 0.5) * h
            py = y + rnd.uniform(-0.3, 0.6) * h
            L = h * 0.32
            for a in (-0.5, 0, 0.5):
                c.line((px, py), (px + math.sin(a) * L, py - math.cos(a) * L), col(LAND_LT), 1.4 * scale)


def components(g):
    """4-connected components of land (0) cells; returns {cell: id} in scan order."""
    n, m = len(g), len(g[0])
    comp, cid = {}, 0
    for i in range(n):
        for j in range(m):
            if g[i][j] == 0 and (i, j) not in comp:
                comp[(i, j)] = cid
                q = deque([(i, j)])
                while q:
                    a, b = q.popleft()
                    for da, db in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        p = (a + da, b + db)
                        if 0 <= p[0] < n and 0 <= p[1] < m and g[p[0]][p[1]] == 0 and p not in comp:
                            comp[p] = cid; q.append(p)
                cid += 1
    return comp, cid

def pad(g):
    m = len(g[0])
    return [[0] * (m + 2)] + [[0] + row + [0] for row in g] + [[0] * (m + 2)]

def outline(c, cells, cx, cy, s, color, width=3):
    """Trace the outer boundary of a set of cells; cx(j), cy(i) give tile centres."""
    for (i, j) in cells:
        x, y, h = cx(j), cy(i), s / 2
        if (i - 1, j) not in cells: c.line((x - h, y - h), (x + h, y - h), color, width)
        if (i + 1, j) not in cells: c.line((x - h, y + h), (x + h, y + h), color, width)
        if (i, j - 1) not in cells: c.line((x - h, y - h), (x - h, y + h), color, width)
        if (i, j + 1) not in cells: c.line((x + h, y - h), (x + h, y + h), color, width)

def badge(c, x, y, k, r=10):
    c.circle(x, y, r, fill=GOLD, outline=BG, width=2)
    c.text(x, y + 1, str(k), font(int(r * 1.15), mono=True), BG)


# =========================================================================
# 1. the border: pad with land, then every open island joins one component
# =========================================================================
GRID = [
    [0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 1, 1, 0, 0, 1, 1, 1, 1, 0],
    [1, 1, 0, 0, 1, 1, 0, 1, 1, 1],
    [0, 1, 1, 1, 1, 0, 0, 0, 1, 1],
    [0, 0, 1, 0, 1, 1, 0, 1, 1, 0],
    [1, 1, 1, 0, 1, 1, 1, 1, 0, 0],
    [1, 0, 1, 1, 1, 0, 0, 1, 1, 1],
    [1, 1, 1, 1, 0, 0, 1, 1, 1, 1],
]

def border_gif():
    N, M = len(GRID), len(GRID[0])
    P = pad(GRID)
    W, H, CS = 620, 690, 46
    gx0 = W / 2 - (M + 2) * CS / 2 + CS / 2
    gy0 = 112
    cx = lambda j: gx0 + j * CS
    cy = lambda i: gy0 + i * CS
    ring = [(0, j) for j in range(M + 2)] + [(i, M + 1) for i in range(1, N + 2)] + \
           [(N + 1, j) for j in range(M, -1, -1)] + [(i, 0) for i in range(N, 0, -1)]
    comp, ncomp = components(P)
    closed = {}
    for p, k in comp.items():
        if k > 0: closed.setdefault(k, set()).add(p)

    # BFS layers of the border component, from (0, 0) as in the scan
    dist = {(0, 0): 0}; q = deque([(0, 0)])
    while q:
        a, b = q.popleft()
        for da, db in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            p = (a + da, b + db)
            if comp.get(p) == 0 and p not in dist:
                dist[p] = dist[(a, b)] + 1; q.append(p)
    maxd = max(dist.values())

    def frame(caption, cap_col=TEXT, shown=None, grow=None, fill_d=-1, lit=0, counter=None,
              frame_box=True):
        c = Canvas(W, H)
        c.text(W / 2, 34, "Pad the grid with a ring of land", font(20), TEXT)
        c.text(W / 2, 64, counter if counter else "0 = land   ·   1 = water", font(15, mono=counter is not None),
               GOLD if counter else MUTED)
        for i in range(N + 2):
            for j in range(M + 2):
                inner = 1 <= i <= N and 1 <= j <= M
                sc = 1
                if not inner and shown is not None:
                    k = ring.index((i, j))
                    if k >= shown:
                        if grow is None or k >= shown + grow[1]:
                            continue
                        sc = ease(grow[0])
                kind = "land" if P[i][j] == 0 else "water"
                d = dist.get((i, j))
                dark = d is not None and d <= fill_d
                tile(c, cx(j), cy(i), CS - 3, kind, seed=i * 97 + j, k=OPEN_K if dark else 1, scale=sc)
                if d is not None and d == fill_d and fill_d < maxd + 1:
                    c.box(cx(j), cy(i), CS - 3, None, GOLD, 2, r=5)
        c.box(W / 2, gy0 + (N + 1) * CS / 2, M * CS + 6, None, MUTED if frame_box else EDGE,
              2 if frame_box else 1.5, h=N * CS + 6, r=6)
        for k in range(1, lit + 1):
            outline(c, closed[k], cx, cy, CS, GOLD, 3)
            i, j = min(closed[k])
            badge(c, cx(j) - CS / 2 + 11, cy(i) - CS / 2 + 11, k + 1)

        # legend
        ly = gy0 + (N + 2) * CS - CS / 2 + 30
        items = [("water", 1, "water"), ("land", 1, "land"), ("land", OPEN_K, "joined to the border"),
                 ("land", 1, "closed island")]
        xs = [W / 2 - 250, W / 2 - 150, W / 2 - 50, W / 2 + 125]
        for (kind, k, label), x in zip(items, xs):
            tile(c, x, ly, 22, kind, seed=5, k=k)
            if label == "closed island":
                c.box(x, ly, 23, None, GOLD, 2, r=4)
            c.text(x + 18, ly, label, font(13, bold=False), MUTED, align="l")

        c.text(W / 2, H - 30, caption, font(17), cap_col)
        return c.done()

    R = len(ring)
    fr = [(frame("islands touching the boundary are not closed", shown=0), 2600)]
    STEP = 2
    for s in range(0, R, STEP):
        for t in (0.35, 0.7, 1.0):
            fr += [(frame("add a ring of land around the grid", shown=s, grow=(t, STEP)), 45)]
    fr += [(frame("add a ring of land around the grid", shown=R), 1200)]
    fr += [(frame("now count components: the scan starts at the corner", shown=R, frame_box=False,
                  counter="components: 1"), 1300)]
    for d in range(0, maxd + 1):
        fr += [(frame("the ring and every open island form one component", shown=R, fill_d=d,
                      frame_box=False, counter="components: 1"), 70)]
    fr += [(frame("the ring and every open island form one component", shown=R, fill_d=maxd + 1,
                  frame_box=False, counter="components: 1"), 2200)]
    for k in range(1, ncomp):
        fr += [(frame("a closed island never touches the ring", shown=R, fill_d=maxd + 1, lit=k,
                      frame_box=False, counter=f"components: {k + 1}"), 1100)]
    fr += [(frame(f"{ncomp} components − 1 = {ncomp - 1} closed islands ✓", GREEN, shown=R,
                  fill_d=maxd + 1, lit=ncomp - 1, frame_box=False,
                  counter=f"components: {ncomp}"), 4000)]
    save_gif(fr, "border.gif")


# =========================================================================
# 2. the three examples of the statement, after padding (static)
# =========================================================================
EXAMPLES = [
    [[1, 1, 1, 1, 1, 1, 1, 0], [1, 0, 0, 0, 0, 1, 1, 0], [1, 0, 1, 0, 1, 1, 1, 0],
     [1, 0, 0, 0, 0, 1, 0, 1], [1, 1, 1, 1, 1, 1, 1, 0]],
    [[0, 0, 1, 0, 0], [0, 1, 0, 1, 0], [0, 1, 1, 1, 0]],
    [[1, 1, 1, 1, 1, 1, 1], [1, 0, 0, 0, 0, 0, 1], [1, 0, 1, 1, 1, 0, 1], [1, 0, 1, 0, 1, 0, 1],
     [1, 0, 1, 1, 1, 0, 1], [1, 0, 0, 0, 0, 0, 1], [1, 1, 1, 1, 1, 1, 1]],
]

def draw_padded(c, g, x0, y0, cs, seed=0):
    """Draw pad(g) with its top-left tile centre at (x0, y0), coloured by component."""
    P = pad(g)
    comp, ncomp = components(P)
    cx = lambda j: x0 + j * cs
    cy = lambda i: y0 + i * cs
    for i in range(len(P)):
        for j in range(len(P[0])):
            kind = "land" if P[i][j] == 0 else "water"
            tile(c, cx(j), cy(i), cs - 2, kind, seed=seed + i * 97 + j,
                 k=OPEN_K if comp.get((i, j)) == 0 else 1)
    n, m = len(g), len(g[0])
    c.box(x0 + (m + 1) * cs / 2, y0 + (n + 1) * cs / 2, m * cs + 4, None, MUTED, 1.5, h=n * cs + 4, r=4)
    for k in range(1, ncomp):
        cells = {p for p, q in comp.items() if q == k}
        outline(c, cells, cx, cy, cs, GOLD, 2.5)
    return ncomp

def examples_png():
    W, H, CS = 860, 450, 26
    c = Canvas(W, H)
    c.text(W / 2, 34, "The examples after padding", font(20), TEXT)
    sizes = [(len(g) + 2, len(g[0]) + 2) for g in EXAMPLES]
    gap = 60
    total = sum(m * CS for _, m in sizes) + gap * (len(sizes) - 1)
    x = W / 2 - total / 2
    top = 80
    hmax = max(n for n, _ in sizes) * CS
    for e, (g, (n, m)) in enumerate(zip(EXAMPLES, sizes)):
        y0 = top + (hmax - n * CS) / 2
        nc = draw_padded(c, g, x + CS / 2, y0 + CS / 2, CS, seed=1000 * e)
        mid = x + m * CS / 2
        c.text(mid, top + hmax + 30, f"Example {e + 1}", font(16), TEXT)
        c.text(mid, top + hmax + 58, f"{nc} components − 1 = {nc - 1}", font(15, mono=True), GREEN)
        x += m * CS + gap
    c.text(W / 2, H - 26, "dark: the component of the ring   ·   gold: closed islands", font(14, bold=False), MUTED)
    c.done().save(os.path.join(OUT, "examples.png"))
    print("wrote examples.png")


# =========================================================================
# 3. one function per step (static)
# =========================================================================
def pipeline_png():
    g = EXAMPLES[1]
    n, m = len(g), len(g[0])
    W, H, CS = 900, 560, 28
    c = Canvas(W, H)
    c.text(W / 2, 34, "closedIsland, one step per function", font(20), TEXT)
    Y1, Y2 = 190, 420                          # centres of the two rows
    XA, XB, XC = 115, 420, 765                 # centres of the three grids in row 1

    def grid_at(xc, yc, rows, draw):
        x0 = xc - len(rows[0]) * CS / 2 + CS / 2
        y0 = yc - len(rows) * CS / 2 + CS / 2
        for i, row in enumerate(rows):
            for j, v in enumerate(row):
                draw(x0 + j * CS, y0 + i * CS, v, i * 97 + j)
        return x0, y0

    def as_int(x, y, v, sd):
        c.box(x, y, CS - 3, SLOT, EDGE, 1, r=5)
        c.text(x, y + 1, str(v), font(15, mono=True), TEXT)

    def as_cell(x, y, v, sd):
        tile(c, x, y, CS - 2, "land" if v == 0 else "water", seed=sd)

    def step_h(x0, x1, y, name, note):
        c.arrow((x0, y), (x1, y), EDGE, 3, 11)
        c.text((x0 + x1) / 2, y - 22, name, font(14, mono=True), GOLD)
        c.text((x0 + x1) / 2, y + 22, note, font(13, bold=False), MUTED)

    # row 1: int grid -> Cell grid -> padded grid
    c.text(XA, Y1 - n * CS / 2 - 24, "vector<vector<int>>", font(12, mono=True), MUTED)
    grid_at(XA, Y1, g, as_int)
    step_h(XA + m * CS / 2 + 14, XB - m * CS / 2 - 14, Y1, "convertGrid", "int → Cell")
    c.text(XB, Y1 - n * CS / 2 - 24, "vector<vector<Cell>>", font(12, mono=True), MUTED)
    grid_at(XB, Y1, g, as_cell)
    step_h(XB + m * CS / 2 + 14, XC - (m + 2) * CS / 2 - 14, Y1, "addLandBorderMargin",
           "N × M → (N+2) × (M+2)")
    c.text(XC, Y1 - (n + 2) * CS / 2 - 24, "padded", font(12, mono=True), MUTED)
    grid_at(XC, Y1, pad(g), as_cell)

    # down: count the components
    ya, yb = Y1 + (n + 2) * CS / 2 + 14, Y2 - (n + 2) * CS / 2 - 14
    c.arrow((XC, ya), (XC, yb), EDGE, 3, 11)
    c.text(XC - 20, (ya + yb) / 2 - 11, "countLandComponents", font(14, mono=True), GOLD, align="r")
    c.text(XC - 20, (ya + yb) / 2 + 13, "dfs  ·  isLand  ·  neighbors", font(13, bold=False), MUTED, align="r")
    nc = draw_padded(c, g, XC - (m + 2) * CS / 2 + CS / 2, Y2 - (n + 2) * CS / 2 + CS / 2, CS)
    c.text(XC, Y2 + (n + 2) * CS / 2 + 24, f"{nc} components", font(14, mono=True), TEXT)

    # left: subtract the ring
    XE = 470
    step_h(XC - (m + 2) * CS / 2 - 14, XE + 50, Y2, "− 1", "the ring's component")
    c.text(XE, Y2, str(nc - 1), font(34, mono=True), GREEN)
    c.text(XE, Y2 + (n + 2) * CS / 2 + 24, "closed island", font(14, mono=True), TEXT)

    # the top-level function reads as the same three steps
    code = ["auto cells = convertGrid(grid);",
            "addLandBorderMargin(cells);",
            "return countLandComponents(cells) - 1;"]
    bx, bw, bh = 30, 330, 110
    c.d.rounded_rectangle([bx * S, (Y2 - bh / 2) * S, (bx + bw) * S, (Y2 + bh / 2) * S],
                          radius=8 * S, fill=SLOT, outline=EDGE, width=int(1.5 * S))
    c.text(bx + 14, Y2 - 34, "closedIsland(grid)", font(12, mono=True), MUTED, align="l")
    for k, line in enumerate(code):
        c.text(bx + 14, Y2 - 6 + k * 22, line, font(11, mono=True), TEXT, align="l")
    c.done().save(os.path.join(OUT, "pipeline.png"))
    print("wrote pipeline.png")


border_gif()
examples_png()
pipeline_png()
