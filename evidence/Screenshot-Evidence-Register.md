# Screenshot Evidence Register

These are genuine application captures. Diagram exports and command logs are stored separately and are not called screenshots.

| Number | Filename | UTC time | Phase | Task and action | Expected | Actual | Requirement | Test | Commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | evidence/screenshots/planning/01-requirements-definition.png | 2026-09-10T14:36:51.039Z | 01 | Document functional requirements and acceptance criteria; Opened the published requirements file at the Phase 01 commit | SITAS requirements heading, requirement IDs and acceptance criteria visible | Requirement definition, FR-01 and FR-02 and their acceptance criteria visible in the GitHub document preview | FR-01, FR-02; requirements traceability | Manual visual verification; definition evidence, not executed acceptance testing | b219b3447817f37503cf225a9c2a127c105dcf07 |
| 21 | evidence/screenshots/github/21-github-repository-home.png | 2026-09-10T14:36:16.605Z | 01 | Verify the public SITAS repository after the Phase 01 push; Opened the dedicated Edge window and refreshed the repository home | Public repository with Phase 01 files and commit | Public repository, main branch, Phase 01 commit b219b34 and project folders visible | Repository and evidence traceability | Manual visual verification | b219b3447817f37503cf225a9c2a127c105dcf07 |

Capture methods and privacy-review notes are recorded in `screenshots/captures.json`.

Native terminal automation is unavailable under the installed computer-use tool's rules. Actual terminal output is preserved in `logs/`. For a terminal screenshot, run the exact command in the corresponding execution JSON, then capture the command, complete result and visible application title manually. Do not replace command evidence with a drawn terminal image.
