"""
Architecture Diagram Engine

Generates Mermaid architecture diagrams from synthesized architecture.
"""


def _first_present(node_ids, *candidates):

    for candidate in candidates:
        if candidate in node_ids:
            return candidate

    return None


def generate_architecture_diagram(spec):

    architecture = spec.get("architecture", {})

    components = architecture.get("components", [])

    nodes = []
    edges = []

    # basic nodes
    for component in components:

        name = component.get("name")

        node_id = name.replace("-", "_")

        nodes.append((node_id, name))

    # naive connections
    # (later this can become smarter)

    node_ids = {node_id for node_id, _ in nodes}

    frontend = _first_present(node_ids, "frontend")
    application = _first_present(node_ids, "api", "cms")
    database = _first_present(node_ids, "database")
    object_storage = _first_present(node_ids, "object_storage")
    worker = _first_present(node_ids, "worker")
    cdn = _first_present(node_ids, "cdn")

    def add_edge(source, target):
        if not source or not target:
            return

        edge = (source, target)

        if edge not in edges:
            edges.append(edge)

    add_edge(frontend, application)
    add_edge(application, database)
    add_edge(application, object_storage)
    add_edge(worker, database)
    add_edge(cdn, frontend)

    diagram = {
        "nodes": nodes,
        "edges": edges,
    }

    return diagram
