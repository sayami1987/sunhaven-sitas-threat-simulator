# SITAS Draw.io diagrams

These files contain editable, uncompressed mxGraph shapes and connectors. They are design drafts, **not completed native Draw.io work**. The required workflow is to create/refine them in Draw.io itself, save editable files and export PNGs from Draw.io. Custom programmatic PNG rendering has stopped following the project owner's clarification.

| Editable draft | Intended native PNG | Content |
| --- | --- | --- |
| `sitas-high-level-architecture.drawio` | `sitas-high-level-architecture.png` | Synthetic inputs, validation, graph, paths, risk, controls, comparison and reports |
| `sitas-attack-path-flow.drawio` | `sitas-attack-path-flow.png` | Baseline and controlled DFS, scoring, comparison and bounded search |
| `sitas-control-simulation.drawio` | `sitas-control-simulation.png` | Scenario 01 before/after MFA and a remaining-route caveat |
| `sitas-component-design.drawio` | `sitas-component-design.png` | Python modules, configuration, tests and outputs |
| `sitas-individual-boundary.drawio` | `sitas-individual-boundary.png` | SITAS standalone scope, inputs, modules and outputs |

No native PNG exports have been captured. Earlier custom-rendered PNGs and their renderer were preserved outside the public repository as development drafts. Original phase export logs remain historical evidence of that method. They must not be presented as native Draw.io exports or application screenshots.

## Native completion steps

1. Open Draw.io or diagrams.net and create/refine each diagram using editable shapes and connectors. Drafts can be opened as references; their layouts are not accepted final native work.
2. Check connections and labels against the implementation and actual scenario output.
3. Save the editable `.drawio` file under the exact name above.
4. Use Draw.io's PNG export command and save the matching `.png` beside it.
5. Capture each completed diagram in Draw.io under `evidence/screenshots/drawio/`. Record the real time, action and commit in the screenshot register.

Required native screens and screenshot filenames:

| Screen visible in Draw.io | Screenshot filename |
| --- | --- |
| Complete high-level architecture at readable zoom | `16-high-level-architecture.png` |
| Complete attack-path process flow at readable zoom | `17-attack-path-flow.png` |
| Before/after MFA control simulation | `18-control-simulation-diagram.png` |
| Software modules and their relationships | `19-component-design.png` |
| SITAS standalone scope diagram | `20-boundary-diagram.png` |

Native computer interaction stopped when the tool could not determine the current browser URL sufficiently to enforce its policy. No further UI actions were attempted after that stop. No Draw.io command-line executable was found in the inspected standard locations. Phase 9 remains partial until native authoring, exports and review are possible.
