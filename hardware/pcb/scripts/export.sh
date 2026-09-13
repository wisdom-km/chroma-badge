#!/usr/bin/env bash
# Export manufacturing files from badge.kicad_sch / badge.kicad_pcb with kicad-cli (KiCad 9).
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=output
mkdir -p "$OUT/gerbers"

echo "== ERC / DRC"
kicad-cli sch erc --severity-error --format report -o "$OUT/erc_errors.rpt" badge.kicad_sch >/dev/null
kicad-cli pcb drc --severity-error --format report -o "$OUT/drc_final.rpt" badge.kicad_pcb >/dev/null || true
grep -E "Found" "$OUT/drc_final.rpt" || true

echo "== netlist + BOM"
kicad-cli sch export netlist -o "$OUT/badge.net" badge.kicad_sch >/dev/null
python3 scripts/check_netlist.py
kicad-cli sch export bom -o "$OUT/badge_bom.csv" \
  --fields "Reference,Value,Footprint,Description,LCSC,\${QUANTITY},\${DNP}" \
  --labels "Ref,Value,Footprint,Description,LCSC,Qty,DNP" \
  --group-by "Value,Footprint,LCSC" badge.kicad_sch >/dev/null

echo "== gerbers / drill / position"
rm -f "$OUT"/gerbers/*
kicad-cli pcb export gerbers --layers "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts" \
  --subtract-soldermask --no-protel-ext -o "$OUT/gerbers/" badge.kicad_pcb >/dev/null
kicad-cli pcb export drill --format excellon --excellon-separate-th --generate-map --map-format gerberx2 \
  -o "$OUT/gerbers/" badge.kicad_pcb >/dev/null
kicad-cli pcb export pos --side back --format csv --units mm --use-drill-file-origin -o "$OUT/badge_pos_back.csv" badge.kicad_pcb >/dev/null
(cd "$OUT/gerbers" && zip -q -r ../badge_gerbers.zip .)

echo "== 3D / drawings"
kicad-cli pcb export step --board-only --no-dnp -o "$OUT/badge_board_only.step" badge.kicad_pcb >/dev/null
kicad-cli pcb export step --no-dnp --subst-models -o "$OUT/badge_full.step" badge.kicad_pcb >/dev/null
kicad-cli sch export svg -o "$OUT/sch_svg" --no-background-color badge.kicad_sch >/dev/null
kicad-cli sch export pdf -o "$OUT/badge_schematic.pdf" badge.kicad_sch >/dev/null
kicad-cli pcb export svg --layers "B.Cu,B.SilkS,Edge.Cuts" --mirror --page-size-mode 2 --exclude-drawing-sheet -o "$OUT/pcb_back.svg" badge.kicad_pcb >/dev/null
kicad-cli pcb export svg --layers "F.Cu,F.SilkS,Edge.Cuts" --page-size-mode 2 --exclude-drawing-sheet -o "$OUT/pcb_front.svg" badge.kicad_pcb >/dev/null
kicad-cli pcb render --side bottom --width 2000 --height 1900 --quality high --background opaque -o "$OUT/render_back.png" badge.kicad_pcb >/dev/null
kicad-cli pcb render --side top --width 2000 --height 1900 --quality high --background opaque -o "$OUT/render_front.png" badge.kicad_pcb >/dev/null
rm -rf "$OUT/en" "$OUT/drc_tmp.json" "$OUT/drc_unrouted.rpt"
ls -la "$OUT"
