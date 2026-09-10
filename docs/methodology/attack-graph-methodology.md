# Attack graph methodology

The environment represents preconditioned attack transitions. Nodes describe
fictional actors, identities, credential references, devices, sessions,
applications, privileges and protected assets. A directed edge states that the
source condition can lead to the target under its written assumptions.

The common environment is a catalogue of transitions. Each scenario selects an
explicit subset of edge IDs to make its assumptions reproducible. Display names
do not create permissions or determine security-control effects. Credential
nodes are descriptive references with no usable secret material.

`src/graph_engine.py` indexes nodes and edges by ID and builds sorted adjacency
lists. Parallel edges with different IDs remain distinct, even when their
endpoints match. Unknown references and duplicate identifiers are errors.
Read-only mappings prevent callers from changing indexes in place.

`Graph.has_cycle()` uses Kahn's topological elimination: remove nodes with zero
incoming edges, decrement the incoming counts of their neighbours and repeat.
If nodes remain after this process, the graph contains a cycle. The operation
takes O(V + E) time and O(V) additional memory. Cycles are valid modelling data;
pathfinding will use per-path visited nodes to avoid infinite traversal.

`python scripts/inspect_graph.py` prints the real graph summary and relationships.
Its phase log records the model that existed at the time of the command. Later
model changes do not alter that historical output.

## Path enumeration

`src/pathfinder.py` performs iterative depth-first search with a stack of adjacency
iterators. Each node is visited at most once within a particular path. On
backtracking, its visited marker is removed, so routes that share later nodes
are all discoverable. The target ends a path and is never expanded further.
Stable edge-ID traversal and a digest of ordered edge IDs provide reproducible
path identity, independent of graph insertion order.

Maximum depth counts edges (default 12, supported range 1-500). An outgoing
non-cycle branch beyond that depth is counted as depth-pruned and excluded from
scope. This does not prove that deeper paths are absent. Maximum result count
(default 10,000) and examined-edge budget (default 100,000) are resource limits;
exceeding either raises `SearchLimitError` instead of returning partial results.

Enumerating simple paths has exponential worst-case output size. The DFS stack
and current visited path require O(depth) space in addition to the graph and
stored result paths. Each path ID uses the first 16 hexadecimal characters of a
SHA-256 digest prefixed with `SITAS-AP-`; comparisons use the complete ordered
edge tuple, so display-digest truncation does not drive path matching.

`python scripts/inspect_paths.py` prints paths in the entire synthetic catalogue
for the selected source and target. The final analysis runner applies each
scenario's explicit edge selection before invoking the same pathfinder.

Graph reachability is conditional on the supplied edges and assumptions. The
model does not automatically infer missing relationships, prove a vulnerability
or test a real organisation's controls. It does not implement AND/OR privilege
logic or require simultaneous independent prerequisites: compound prerequisites
must be encoded explicitly as scenario states or documented assumptions.
