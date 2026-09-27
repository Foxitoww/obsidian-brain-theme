"""Generate theme.css for the Brain Obsidian theme: a holographic brain in the
middle of each note and a glowing neural network running around the frame.

Usage: python tools/build_theme.py"""
import math
import random
from pathlib import Path
from urllib.parse import quote

THEME_FILE = Path(__file__).resolve().parent.parent / "theme.css"

GLOW_GRADIENT = (
    "<radialGradient id='g'>"
    "<stop offset='0' stop-color='#eef2ff' stop-opacity='0.55'/>"
    "<stop offset='0.35' stop-color='#8fa4ff' stop-opacity='0.2'/>"
    "<stop offset='1' stop-color='#6d7dff' stop-opacity='0'/>"
    "</radialGradient>"
)


def as_css_url(svg):
    return f'url("data:image/svg+xml,{quote(svg, safe=" =:/,.")}")'


def frame_strip(side, length=640, depth=150, neuron_count=9, seed=1):
    """One edge of the frame: neurons crowd against the edge and thin out inwards."""
    rng = random.Random(seed)
    horizontal = side in ("top", "bottom")
    width, height = (length, depth) if horizontal else (depth, length)

    neurons = []
    for _ in range(neuron_count):
        along = rng.uniform(length * 0.04, length * 0.96)
        inward = depth * rng.random() ** 2 * 0.8 + 4   # squared: most neurons stay near the edge
        if side == "top":
            x, y = along, inward
        elif side == "bottom":
            x, y = along, depth - inward
        elif side == "left":
            x, y = inward, along
        else:
            x, y = depth - inward, along
        size = 1.25 - 0.6 * (inward / depth)            # neurons get smaller away from the edge
        neurons.append((x, y, size))

    paths = []
    for index, (x1, y1, _) in enumerate(neurons):
        nearest = sorted(
            (math.dist((x1, y1), (x2, y2)), x2, y2)
            for other, (x2, y2, _) in enumerate(neurons) if other != index
        )
        for _, x2, y2 in nearest[:2]:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            bend = rng.uniform(-0.3, 0.3) * math.dist((x1, y1), (x2, y2))
            angle = math.atan2(y2 - y1, x2 - x1) + math.pi / 2
            paths.append(
                f"M{x1:.0f} {y1:.0f}Q{mx + bend * math.cos(angle):.0f} "
                f"{my + bend * math.sin(angle):.0f} {x2:.0f} {y2:.0f}"
            )
        for _ in range(3):                                  # loose dendrites
            angle = rng.uniform(0, 2 * math.pi)
            reach = rng.uniform(12, 34)
            paths.append(
                f"M{x1:.0f} {y1:.0f}Q{x1 + reach * 0.5 * math.cos(angle + 0.6):.0f} "
                f"{y1 + reach * 0.5 * math.sin(angle + 0.6):.0f} "
                f"{x1 + reach * math.cos(angle):.0f} {y1 + reach * math.sin(angle):.0f}"
            )

    glows = "".join(
        f"<circle cx='{x:.0f}' cy='{y:.0f}' r='{10 * s:.1f}' fill='url(#g)'/>"
        f"<circle cx='{x:.0f}' cy='{y:.0f}' r='{1.4 * s:.1f}' fill='#f4f6ff' fill-opacity='0.7'/>"
        for x, y, s in neurons
    )
    return as_css_url(
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>"
        f"<defs>{GLOW_GRADIENT}</defs>"
        f"<path d='{''.join(paths)}' fill='none' stroke='#a9b6ff' stroke-opacity='0.2' "
        "stroke-width='1' stroke-linecap='round'/>"
        f"{glows}</svg>"
    )


# ---------- Brain geometry ----------

# Side view, facing left like the inspiration picture: frontal lobe on the left,
# occipital lobe on the right, temporal lobe underneath.
CEREBRUM = [
    (150, 300), (118, 250), (112, 195), (130, 145), (168, 100), (222, 66), (290, 46),
    (360, 42), (425, 52), (485, 78), (535, 118), (568, 168), (580, 220), (572, 268),
    (548, 300), (505, 318), (455, 322), (420, 334), (392, 358), (348, 374), (295, 370),
    (245, 354), (205, 332), (172, 318),
]
CEREBELLUM = [(452, 330), (505, 312), (556, 322), (582, 352), (568, 386), (524, 402), (476, 394), (448, 364)]
BRAINSTEM = [(404, 340), (446, 350), (452, 398), (446, 448), (436, 490), (418, 490), (412, 448), (402, 398)]


def catmull_rom(points, closed, samples=0):
    """Smooth curve through the points: an SVG path, or `samples` points per segment."""
    count = len(points)
    segments = count if closed else count - 1
    get = (lambda i: points[i % count]) if closed else (lambda i: points[max(0, min(count - 1, i))])
    commands = [f"M{points[0][0]:.1f} {points[0][1]:.1f}"]
    sampled = []
    for i in range(segments):
        p0, p1, p2, p3 = get(i - 1), get(i), get(i + 1), get(i + 2)
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        commands.append(f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}")
        for step in range(samples):
            t = step / samples
            mt = 1 - t
            sampled.append((
                mt**3 * p1[0] + 3 * mt**2 * t * c1[0] + 3 * mt * t**2 * c2[0] + t**3 * p2[0],
                mt**3 * p1[1] + 3 * mt**2 * t * c1[1] + 3 * mt * t**2 * c2[1] + t**3 * p2[1],
            ))
    return sampled if samples else "".join(commands) + ("Z" if closed else "")


def inside(point, polygon):
    """Ray casting: is the point inside the polygon?"""
    x, y = point
    result = False
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            result = not result
    return result


def random_point(rng, polygon, box):
    while True:
        point = (rng.uniform(box[0], box[2]), rng.uniform(box[1], box[3]))
        if inside(point, polygon):
            return point


def spread_points(rng, polygon, box, count, min_distance):
    """Random points inside the polygon, never closer than min_distance to each other."""
    points = []
    for _ in range(count * 60):
        candidate = random_point(rng, polygon, box)
        if all(math.dist(candidate, other) >= min_distance for other in points):
            points.append(candidate)
            if len(points) == count:
                break
    return points


def scaled(polygon, center, factor):
    return [(center[0] + (x - center[0]) * factor, center[1] + (y - center[1]) * factor) for x, y in polygon]


def brain():
    """A scientific hologram of a brain: ghostly silhouette with a glowing rim,
    wireframe mesh, point cloud, cross-section contours, scan lines, main grooves
    and a measuring reticle."""
    rng = random.Random(2026)
    cerebrum_polygon = catmull_rom(CEREBRUM, closed=True, samples=8)
    cerebrum_box = (112, 42, 580, 374)
    center = (348, 212)

    cerebrum = catmull_rom(CEREBRUM, closed=True)
    cerebellum = catmull_rom(CEREBELLUM, closed=True)
    brainstem = catmull_rom(BRAINSTEM, closed=True)
    silhouette = cerebrum + cerebellum + brainstem

    # Wireframe: vertices on the outline and spread inside, each linked to its nearest ones.
    rim_vertices = cerebrum_polygon[::6]
    inner_vertices = spread_points(rng, cerebrum_polygon, cerebrum_box, count=70, min_distance=34)
    vertices = rim_vertices + inner_vertices
    edges = set()
    for index, point in enumerate(vertices):
        nearest = sorted(range(len(vertices)), key=lambda other: math.dist(point, vertices[other]))[1:4]
        for other in nearest:
            edges.add((min(index, other), max(index, other)))
    wireframe = "".join(
        f"M{vertices[a][0]:.0f} {vertices[a][1]:.0f}L{vertices[b][0]:.0f} {vertices[b][1]:.0f}" for a, b in edges
    )
    nodes = "".join(
        f"<circle cx='{x:.0f}' cy='{y:.0f}' r='1.6' fill='#eef2ff' fill-opacity='0.7'/>" for x, y in vertices[::2]
    )
    node_glows = "".join(
        f"<circle cx='{x:.0f}' cy='{y:.0f}' r='{rng.uniform(9, 15):.0f}' fill='url(#g)'/>"
        for x, y in rng.sample(inner_vertices, 16)
    )

    # Point cloud: tiny particles filling the volume.
    cloud = "".join(
        f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rng.uniform(0.5, 1.1):.1f}' "
        f"fill-opacity='{rng.uniform(0.15, 0.6):.2f}'/>"
        for x, y in (random_point(rng, cerebrum_polygon, cerebrum_box) for _ in range(420))
    )

    # Cross-section contours, like the slices of a scan.
    contours = "".join(
        catmull_rom(scaled(CEREBRUM, center, factor), closed=True) for factor in (0.82, 0.64, 0.46, 0.28)
    )

    # Main grooves.
    central_sulcus = catmull_rom(
        [(372, 44), (360, 88), (372, 128), (352, 168), (362, 208), (342, 248), (350, 278)], closed=False)
    lateral_sulcus = catmull_rom(
        [(206, 310), (256, 290), (304, 296), (350, 274), (398, 266), (440, 244), (480, 248)], closed=False)

    # Cerebellum: fine folds that follow its lower curve.
    lower_curve = [(448, 364), (476, 394), (524, 402), (568, 386), (582, 352)]
    folia = "".join(
        catmull_rom([(x, y - 7 * row) for x, y in lower_curve], closed=False) for row in range(1, 12)
    )

    # Reticle: crosshair with graduations and corner brackets around the brain.
    left, top, right, bottom = 92, 22, 606, 500
    ticks = "".join(f"M{x} {center[1] - 4}V{center[1] + 4}" for x in range(left + 20, right - 10, 20))
    ticks += "".join(f"M{center[0] - 4} {y}H{center[0] + 4}" for y in range(top + 20, bottom - 10, 20))
    corner = 26
    brackets = (
        f"M{left} {top + corner}V{top}H{left + corner}M{right - corner} {top}H{right}V{top + corner}"
        f"M{right} {bottom - corner}V{bottom}H{right - corner}M{left + corner} {bottom}H{left}V{bottom - corner}"
    )
    crosshair = f"M{left} {center[1]}H{right}M{center[0]} {top}V{bottom}"

    return as_css_url(
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='80 10 540 500'>"
        "<defs>"
        f"{GLOW_GRADIENT}"
        "<linearGradient id='spectrum' gradientUnits='userSpaceOnUse' x1='120' y1='90' x2='590' y2='380'>"
        "<stop offset='0' stop-color='#d9a8ff'/>"
        "<stop offset='0.5' stop-color='#b9c2ff'/>"
        "<stop offset='1' stop-color='#7f9cff'/>"
        "</linearGradient>"
        "<radialGradient id='ghost' cx='0.45' cy='0.4' r='0.7'>"
        "<stop offset='0' stop-color='#b9c2ff' stop-opacity='0.1'/>"
        "<stop offset='0.7' stop-color='#8fa4ff' stop-opacity='0.04'/>"
        "<stop offset='1' stop-color='#d9a8ff' stop-opacity='0.12'/>"
        "</radialGradient>"
        "<pattern id='scan' width='6' height='6' patternUnits='userSpaceOnUse'>"
        "<path d='M0 0.5H6' stroke='#b9c2ff' stroke-opacity='0.09' stroke-width='1'/></pattern>"
        "<filter id='blur' x='-30%' y='-30%' width='160%' height='160%'>"
        "<feGaussianBlur stdDeviation='7'/></filter>"
        f"<clipPath id='whole'><path d='{silhouette}'/></clipPath>"
        f"<clipPath id='cortex'><path d='{cerebrum}'/></clipPath>"
        f"<clipPath id='little-brain'><path d='{cerebellum}'/></clipPath>"
        "</defs>"
        # The whole hologram is dimmed so the note text stays easy to read.
        "<g opacity='0.42'>"
        # Reticle, behind everything.
        f"<path d='{crosshair}' stroke='#b9c2ff' stroke-opacity='0.08' stroke-dasharray='2 6' fill='none'/>"
        f"<path d='{ticks}' stroke='#b9c2ff' stroke-opacity='0.16' fill='none'/>"
        f"<path d='{brackets}' stroke='#b9c2ff' stroke-opacity='0.35' stroke-width='1.4' fill='none'/>"
        # Ghostly body, glowing aura and scan lines.
        f"<path d='{silhouette}' fill='none' stroke='url(#spectrum)' stroke-opacity='0.45' "
        "stroke-width='14' filter='url(#blur)'/>"
        f"<path d='{silhouette}' fill='url(#ghost)'/>"
        "<g clip-path='url(#whole)'>"
        "<rect x='80' y='10' width='540' height='500' fill='url(#scan)'/>"
        f"<path d='{silhouette}' fill='none' stroke='url(#spectrum)' stroke-opacity='0.55' "
        "stroke-width='26' filter='url(#blur)'/>"
        "</g>"
        # Inside the cerebrum: slices, wireframe, grooves, point cloud.
        "<g clip-path='url(#cortex)' fill='none'>"
        f"<path d='{contours}' stroke='url(#spectrum)' stroke-opacity='0.16' stroke-dasharray='3 5'/>"
        f"<path d='{wireframe}' stroke='url(#spectrum)' stroke-opacity='0.28' stroke-width='0.8'/>"
        f"<path d='{central_sulcus}{lateral_sulcus}' stroke='#eef2ff' stroke-opacity='0.35' "
        "stroke-width='1.6' stroke-linecap='round'/>"
        f"<g fill='#eef2ff'>{cloud}</g>"
        "</g>"
        f"<g clip-path='url(#little-brain)'><path d='{folia}' fill='none' stroke='url(#spectrum)' "
        "stroke-opacity='0.4' stroke-width='1'/></g>"
        # Crisp glowing outline, then the lit nodes.
        f"<path d='{silhouette}' fill='none' stroke='url(#spectrum)' stroke-opacity='0.8' "
        "stroke-width='1.6' stroke-linejoin='round'/>"
        f"{node_glows}{nodes}"
        "</g></svg>"
    )


CSS = """/* Brain — a dark theme inspired by glowing neural networks: deep black,
   a holographic brain behind each note, and lavender-blue neurons running
   around the frame.
   No !important, so user snippets (such as the difficulty colors) always keep priority. */

/* ---------- Shared variables ---------- */
body {
  --brain-blue: #8fa4ff;
  --brain-lavender: #b9c2ff;
  --brain-core: #eef2ff;

  --heading-spacing: 1.6em;
  --h1-weight: 700;
  --h2-weight: 650;
  --h3-weight: 600;

  --brain-brain: BRAIN;
  --brain-frame-top: FRAME_TOP;
  --brain-frame-bottom: FRAME_BOTTOM;
  --brain-frame-left: FRAME_LEFT;
  --brain-frame-right: FRAME_RIGHT;
}

/* ---------- Dark mode: the main look ---------- */
.theme-dark {
  --accent-h: 229;
  --accent-s: 100%;
  --accent-l: 78%;

  --background-primary: #030409;
  --background-primary-alt: #07090f;
  --background-secondary: #05060b;
  --background-secondary-alt: #0a0d17;
  --background-modifier-border: #1a1f33;

  --text-normal: #dfe3ee;
  --text-muted: #9098b0;
  --text-faint: #5a6079;
  --text-accent: var(--brain-blue);
  --text-accent-hover: var(--brain-core);
  --text-selection: rgba(143, 164, 255, 0.25);

  --h1-color: #f2f4ff;
  --h2-color: #c9d1ff;
  --h3-color: #aab7ff;
  --h4-color: #c3c9dc;
  --h5-color: #c3c9dc;
  --h6-color: #c3c9dc;

  --graph-line: rgba(154, 169, 255, 0.35);
  --graph-node: var(--brain-lavender);
  --graph-node-unresolved: #5a6079;
  --graph-node-focused: #ffffff;
  --graph-node-tag: #d7b8ff;
  --graph-node-attachment: var(--brain-blue);
  --graph-text: #dfe3ee;
}

/* ---------- Light mode: a softer, daylight version ---------- */
.theme-light {
  --accent-h: 232;
  --accent-s: 70%;
  --accent-l: 55%;

  --background-primary: #f7f8fc;
  --background-secondary: #eceef6;

  --text-normal: #1b1f33;
  --text-muted: #565d78;
  --text-accent: #4056d6;

  --graph-line: rgba(64, 86, 214, 0.3);
  --graph-node: #4056d6;
  --graph-node-focused: #1b1f33;
}

/* ---------- Behind every note: the brain in the middle, neurons around the frame ---------- */
.theme-dark .markdown-reading-view,
.theme-dark .markdown-source-view {
  background-image:
    var(--brain-frame-top),
    var(--brain-frame-bottom),
    var(--brain-frame-left),
    var(--brain-frame-right),
    var(--brain-brain),
    radial-gradient(ellipse at 50% 45%, rgba(143, 164, 255, 0.07), transparent 60%);
  background-repeat: repeat-x, repeat-x, repeat-y, repeat-y, no-repeat, no-repeat;
  background-position: top left, bottom left, top left, top right, center 45%, center;
  background-size: auto, auto, auto, auto, min(78%, 920px) auto, 100% 100%;
  /* A thin glowing frame. */
  box-shadow: inset 0 0 0 1px rgba(143, 164, 255, 0.12), inset 0 0 60px rgba(143, 164, 255, 0.08);
}

/* ---------- Glow: headings take the glow of their own color,
   so difficulty colors from the snippet keep glowing too ---------- */
.theme-dark :where(h1, h2, h3, .inline-title, .cm-header) {
  text-shadow:
    0 0 6px color-mix(in srgb, currentColor 35%, transparent),
    0 0 18px color-mix(in srgb, currentColor 25%, transparent);
}

/* Links look like firing synapses. */
.theme-dark :where(a, .internal-link, .cm-hmd-internal-link) {
  text-shadow: 0 0 8px rgba(143, 164, 255, 0.45);
  transition: text-shadow 0.2s ease, color 0.2s ease;
}
.theme-dark :where(a, .internal-link, .cm-hmd-internal-link):hover {
  text-shadow: 0 0 6px rgba(238, 242, 255, 0.8), 0 0 16px rgba(143, 164, 255, 0.7);
}

/* Horizontal rules become a signal running along a dendrite. */
.theme-dark :where(hr) {
  border: none;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--brain-blue), var(--brain-core), var(--brain-blue), transparent);
  box-shadow: 0 0 8px rgba(143, 164, 255, 0.5);
}

/* Tags glow softly. */
.theme-dark :where(.tag) {
  background-color: rgba(143, 164, 255, 0.08);
  border: 1px solid rgba(143, 164, 255, 0.35);
  box-shadow: 0 0 8px rgba(143, 164, 255, 0.25);
}

/* Code and quotes sit in dark, slightly see-through cells so the brain shows faintly behind. */
.theme-dark :where(pre, code) {
  background-color: rgba(10, 13, 23, 0.85);
}
.theme-dark :where(pre) {
  border: 1px solid #1a1f33;
  box-shadow: inset 0 0 22px rgba(143, 164, 255, 0.06);
}
.theme-dark :where(blockquote) {
  border-left-color: var(--brain-lavender);
  background: linear-gradient(90deg, rgba(143, 164, 255, 0.09), transparent);
}

/* Tables: faint glowing header. */
.theme-dark :where(th) {
  background-color: rgba(143, 164, 255, 0.1);
}
"""

css = (
    CSS.replace("BRAIN", brain())
    .replace("FRAME_TOP", frame_strip("top", seed=3))
    .replace("FRAME_BOTTOM", frame_strip("bottom", seed=5))
    .replace("FRAME_LEFT", frame_strip("left", seed=8))
    .replace("FRAME_RIGHT", frame_strip("right", seed=13))
)
THEME_FILE.write_text(css, encoding="utf-8", newline="\n")
print(f"Written {THEME_FILE} ({len(css)} characters)")
