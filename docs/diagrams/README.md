# SITAS diagrams

The `.drawio` files are the editable sources. They contain uncompressed mxGraph
XML with individual shapes, text cells and directed connectors, rather than an
embedded bitmap. Open a source in diagrams.net or the draw.io desktop application
to edit it.

| Source | Purpose |
| --- | --- |
| `sitas-high-level-architecture.drawio` | Synthetic inputs, validation, graph construction, iterative DFS, risk scoring, control simulation, comparison and report generation. |
| `sitas-individual-boundary.drawio` | SITAS standalone scope: internal modules, synthetic inputs, generated outputs and local execution constraints. |

## Repeatable PNG export

From the repository root, with Pillow installed:

```console
python scripts/export_diagrams.py
```

The command finds every `docs/diagrams/*.drawio` source and writes a PNG beside
it. Additional diagrams in this folder use the same command; there is no fixed
list of filenames in the exporter. To export one file or change resolution:

```console
python scripts/export_diagrams.py docs/diagrams/sitas-high-level-architecture.drawio --scale 2
```

The checked-in PNGs use the default scale of 1.5. If Pillow is missing, install
the development dependency with `python -m pip install Pillow`.

These PNGs are **diagram exports rendered by the project's Pillow script from
the authoritative draw.io XML**. They are not application screenshots and do
not represent a native diagrams.net export. The export process needs no browser,
network connection, credentials or external rendering service. A draw.io CLI was
not found on the development machine's PATH or in its common installation paths.

## Supported source conventions

The renderer supports one uncompressed `mxGraphModel` page per file, rectangle
and `shape=ellipse` vertices, rounded rectangles, separate text cells, font size
and colour, left/centre/right text alignment, explicit source/target anchors and
edge waypoints. `background=1` marks a containing rectangle to draw behind edges.
For a labelled connection, add a separate text cell instead of an edge label.

Use the existing diagrams as source examples when adding the next diagrams.
Compressed sources, unsupported shape names and labels that overflow their cell
geometry cause an explicit export error. The exporter reads source labels and
geometry directly; it does not keep a second hand-drawn copy of the layout.

The Pillow renderer covers this project's diagram subset and is not a complete
replacement for diagrams.net. Advanced editor features may need an update to the
renderer or a native diagrams.net export. After an edit, rerun the export and
visually inspect the resulting PNG for label visibility and connector placement.
