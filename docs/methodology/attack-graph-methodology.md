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

Graph reachability is conditional on the supplied edges and assumptions. The
model does not automatically infer missing relationships, prove a vulnerability
or test a real organisation's controls. It does not implement AND/OR privilege
logic or require simultaneous independent prerequisites: compound prerequisites
must be encoded explicitly as scenario states or documented assumptions.
