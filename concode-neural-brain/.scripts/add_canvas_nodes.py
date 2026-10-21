#!/usr/bin/env python3
"""
Add 20 missing vault notes to the Canvas map and wire edges to parent MOCs.

Placement strategy:
- Guild specs (11 nodes): new column at x=3150, fanning vertically around
  the Guild-Networks-MOC at y=1140.
- Math/Security/SDK/Diagnostics: placed at x=3150 adjacent to their MOC y.
- Edges connect each new node -> its parent MOC node.
- Additional edges connect guild specs -> their corresponding 02-Guilds/ nodes.
"""

import json, copy, sys

CANVAS_PATH = "CONCODE-Neural-Brain-Map.canvas"

with open(CANVAS_PATH) as f:
    canvas = json.load(f)

# Build lookup: file path -> node id
file_to_id = {n.get("file", ""): n["id"] for n in canvas["nodes"]}
existing_ids = {n["id"] for n in canvas["nodes"]}
existing_edge_keys = {(e["fromNode"], e["toNode"]) for e in canvas["edges"]}

W = 420
H = 300
DY = 360  # vertical spacing between rows

NEW_X = 3150  # new column to the right of x=2600


def make_id(file_path):
    """Generate a node ID from file path matching the existing convention."""
    return "node_" + file_path.replace("/", "_").replace("-", "_").replace(".md", "_md")


def add_node(file_path, x, y):
    nid = make_id(file_path)
    if nid in existing_ids:
        print(f"  SKIP node (already exists): {file_path}", file=sys.stderr)
        return nid
    node = {
        "id": nid,
        "type": "file",
        "file": file_path,
        "x": x,
        "y": y,
        "width": W,
        "height": H,
    }
    canvas["nodes"].append(node)
    existing_ids.add(nid)
    file_to_id[file_path] = nid
    print(f"  ADD node: {file_path}  x={x} y={y}")
    return nid


def add_edge(from_file, to_file, label=None):
    from_id = file_to_id.get(from_file) or make_id(from_file)
    to_id = file_to_id.get(to_file) or make_id(to_file)
    key = (from_id, to_id)
    if key in existing_edge_keys or (to_id, from_id) in existing_edge_keys:
        return
    edge = {
        "id": f"edge_{from_id}_to_{to_id}",
        "fromNode": from_id,
        "fromSide": "right",
        "toNode": to_id,
        "toSide": "left",
    }
    canvas["edges"].append(edge)
    existing_edge_keys.add(key)
    print(f"  ADD edge: {from_file} -> {to_file}")


# ============================================================
# 1. Guild Specs (11 nodes) -- fan around Guild-Networks-MOC y=1140
# ============================================================
print("\n=== Guild Specs ===")
GUILD_MOC_Y = 1140
guild_specs = [
    ("09-Guild-Networks/AI-ML-Spec.md", "02-Guilds/AI-ML-Guild.md"),
    ("09-Guild-Networks/QA-Spec.md", "02-Guilds/QA-Guild.md"),
    ("09-Guild-Networks/Security-Spec.md", "02-Guilds/Security-Guild.md"),
    ("09-Guild-Networks/Performance-Spec.md", "02-Guilds/Performance-Guild.md"),
    ("09-Guild-Networks/Database-Spec.md", "02-Guilds/Database-Guild.md"),
    ("09-Guild-Networks/UI-UX-Spec.md", "02-Guilds/UI-UX-Guild.md"),
    ("09-Guild-Networks/DevOps-Spec.md", "02-Guilds/DevOps-Guild.md"),
    ("09-Guild-Networks/API-Spec.md", "02-Guilds/API-Guild.md"),
    ("09-Guild-Networks/Fullstack-Spec.md", "02-Guilds/Fullstack-Guild.md"),
    ("09-Guild-Networks/Mobile-Spec.md", "02-Guilds/Mobile-Guild.md"),
    ("09-Guild-Networks/Blockchain-Spec.md", "02-Guilds/Blockchain-Guild.md"),
]

# Center 11 nodes vertically around the MOC
start_y = GUILD_MOC_Y - (len(guild_specs) // 2) * DY
for i, (spec_file, guild_file) in enumerate(guild_specs):
    y = start_y + i * DY
    nid = add_node(spec_file, NEW_X, y)
    # Edge: spec -> Guild-Networks-MOC
    add_edge(spec_file, "09-Guild-Networks/Guild-Networks-MOC.md")
    # Edge: spec -> corresponding guild note (if it exists in canvas)
    if guild_file in file_to_id:
        add_edge(spec_file, guild_file)

# ============================================================
# 2. Math Foundations (4 notes) -- fan around Math-Foundations-MOC y=9060
# ============================================================
print("\n=== Mathematical Foundations ===")
MATH_MOC_Y = 9060
math_notes = [
    "13-Mathematical-Foundations/03-SwiGLU-Activation-Math.md",
    "13-Mathematical-Foundations/04-Cosine-Vector-Similarity-Math.md",
    "13-Mathematical-Foundations/05-Cross-Entropy-Sequence-Math.md",
    "13-Mathematical-Foundations/06-RMSNorm-Scaling-Math.md",
]
start_y = MATH_MOC_Y - (len(math_notes) // 2) * DY
for i, note in enumerate(math_notes):
    y = start_y + i * DY
    add_node(note, NEW_X, y)
    add_edge(note, "13-Mathematical-Foundations/Math-Foundations-MOC.md")

# ============================================================
# 3. Security Protocols (2 notes) -- below existing security nodes at y=5820
# ============================================================
print("\n=== Security Protocols ===")
SEC_MOC_Y = 5820
security_notes = [
    "11-Security-Protocols/03-Rate-Limiting-And-Throttling.md",
    "11-Security-Protocols/04-API-Key-Validation.md",
]
start_y = SEC_MOC_Y - DY
for i, note in enumerate(security_notes):
    y = start_y + i * DY
    add_node(note, NEW_X, y)
    add_edge(note, "11-Security-Protocols/Security-Protocols-MOC.md")

# ============================================================
# 4. Client SDKs (2 notes) -- around Client-SDK-MOC y=6540
# ============================================================
print("\n=== Client SDKs ===")
SDK_MOC_Y = 6540
sdk_notes = [
    "14-Client-SDK/02-Python-Client-SDK.md",
    "14-Client-SDK/03-WebSocket-Streaming-Client.md",
]
start_y = SDK_MOC_Y - DY
for i, note in enumerate(sdk_notes):
    y = start_y + i * DY
    add_node(note, NEW_X, y)
    add_edge(note, "14-Client-SDK/Client-SDK-MOC.md")

# ============================================================
# 5. Diagnostics (1 note) -- above Diagnostics-MOC y=7260
# ============================================================
print("\n=== Diagnostics ===")
DIAG_MOC_Y = 7260
add_node("15-Diagnostics/02-Out-Of-Memory-Prevention.md", NEW_X, DIAG_MOC_Y - DY)
add_edge("15-Diagnostics/02-Out-Of-Memory-Prevention.md", "15-Diagnostics/Diagnostics-MOC.md")


# ============================================================
# 6. Also connect existing spec/child nodes that have no edges to their MOCs
# ============================================================
print("\n=== Missing MOC edges for existing nodes ===")
moc_children = {
    "09-Guild-Networks/Guild-Networks-MOC.md": [
        "09-Guild-Networks/Debugger-Spec.md",
        "09-Guild-Networks/WebGL-Spec.md",
    ],
    "11-Security-Protocols/Security-Protocols-MOC.md": [
        "11-Security-Protocols/01-JWT-Token-Verification.md",
        "11-Security-Protocols/02-Input-Sanitization-And-Escaping.md",
    ],
    "13-Mathematical-Foundations/Math-Foundations-MOC.md": [
        "13-Mathematical-Foundations/01-Softmax-Temperature-Math.md",
        "13-Mathematical-Foundations/02-Rotary-Embedding-Complex-Math.md",
    ],
    "14-Client-SDK/Client-SDK-MOC.md": [
        "14-Client-SDK/01-JavaScript-Client-SDK.md",
    ],
    "15-Diagnostics/Diagnostics-MOC.md": [
        "15-Diagnostics/01-Model-Load-Failure-Recovery.md",
    ],
}
for moc, children in moc_children.items():
    for child in children:
        if child in file_to_id and moc in file_to_id:
            add_edge(child, moc)


# Write out
with open(CANVAS_PATH, "w") as f:
    json.dump(canvas, f, indent=2)

print(f"\nFinal: {len(canvas['nodes'])} nodes, {len(canvas['edges'])} edges")
