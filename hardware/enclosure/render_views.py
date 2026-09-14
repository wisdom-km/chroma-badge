"""Headless enclosure previews (FreeCAD + matplotlib Agg).

Run:  D:\\FreeCAD\\bin\\freecadcmd.exe render_views.py
PNGs go to hardware/enclosure/output/
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
OUT = os.path.join(HERE, "output")
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "pcb", "scripts")))
import design as D  # noqa: E402

# Rebuild solids from the same functions as the CAD (importing badge_enclosure runs main()).
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "badge_enclosure_lib", os.path.join(HERE, "badge_enclosure.py")
)
# Load source, strip the trailing main() call.
with open(os.path.join(HERE, "badge_enclosure.py"), encoding="utf-8") as f:
    src = f.read()
if src.rstrip().endswith("main()"):
    src = src.rstrip()[: -len("main()")].rstrip() + "\n"
_mod = importlib.util.module_from_spec(_spec)
exec(compile(src, "badge_enclosure.py", "exec"), _mod.__dict__)


def tess(shape, lin=0.6):
    pts, faces = shape.tessellate(lin)
    return [[pts[i] for i in face] for face in faces]


def add(ax, shape, color, alpha=0.92, lin=0.7):
    ax.add_collection3d(
        Poly3DCollection(
            tess(shape, lin),
            facecolors=color,
            edgecolors=(0, 0, 0, 0.12),
            linewidths=0.08,
            alpha=alpha,
        )
    )


def finish(ax, shapes, elev, azim, title, path, size=(10.5, 8.0)):
    xs, ys, zs = [], [], []
    for s in shapes:
        b = s.BoundBox
        xs += [b.XMin, b.XMax]
        ys += [b.YMin, b.YMax]
        zs += [b.ZMin, b.ZMax]
    cx, cy, cz = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2
    span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)) * 0.62
    ax.set_xlim(cx - span, cx + span)
    ax.set_ylim(cy - span, cy + span)
    ax.set_zlim(cz - span, cz + span)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title, fontsize=11, pad=8)
    fig = ax.get_figure()
    fig.set_size_inches(*size)
    fig.tight_layout()
    fig.savefig(path, dpi=140, facecolor="white")
    plt.close(fig)
    print("wrote", path)


def main():
    os.makedirs(OUT, exist_ok=True)
    frame = _mod.front_frame()
    cover = _mod.back_cover()
    panel = _mod.panel_body()
    usb = _mod.usb_body()
    batt = _mod.battery_body()

    # Front: frame + panel only (cover would z-fight through the window in mpl 3D)
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    add(ax, frame, "#3a3d42", 0.95, 0.85)
    add(ax, panel, "#e6e4d8", 1.0, 0.9)
    finish(ax, [frame], 28, -55, "BADGE-42C front  ~94x93x6.3 mm  (window + USB + lanyard)",
           os.path.join(OUT, "enclosure_iso_front.png"))

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    add(ax, frame, "#3a3d42", 0.9, 0.85)
    add(ax, cover, "#6a6e76", 0.97, 0.75)
    finish(ax, [frame], -32, 60, "BADGE-42C back  (cover, RST/BOOT holes)",
           os.path.join(OUT, "enclosure_iso_back.png"))

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    add(ax, frame, "#3a3d42", 0.97, 0.75)
    finish(ax, [frame], 30, -55, "Front frame  (AA window, USB cutout, lanyard slot)",
           os.path.join(OUT, "enclosure_frame.png"))

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    add(ax, cover, "#5a5e66", 0.97, 0.65)
    finish(ax, [cover], 28, -50, "Back cover  (button / LED holes, snap tongues)",
           os.path.join(OUT, "enclosure_cover.png"))

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    add(ax, frame, "#3a3d42", 0.95, 0.9)
    add(ax, cover, "#5a5e66", 0.95, 0.9)
    add(ax, panel, "#e6e4d8", 1.0, 1.0)
    add(ax, usb, "#888888", 1.0, 0.5)
    finish(ax, [frame], 4, 0, "Side  ~6.3 mm thick, USB on the bottom edge",
           os.path.join(OUT, "enclosure_side.png"), size=(11.0, 6.5))

    print(f"outer ~94 x 93 x 6.3 mm; panel {D.BOARD_W:.0f}x{D.PANEL_H}x{D.PANEL_T}; PCB {D.BOARD_W:.0f}x{D.BOARD_H}x{D.BOARD_THICKNESS}")


main()
