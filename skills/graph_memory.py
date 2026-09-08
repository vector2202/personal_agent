import json
import os
from collections import deque
from enum import Enum
from typing import Type, Dict, Any, Optional, List
from pydantic import BaseModel, Field
from skills.base import BaseSkill

class GraphAction(str, Enum):
    INSERT = "INSERT"
    QUERY = "QUERY"
    RELATE = "RELATE"
    FIND_PATH = "FIND_PATH"
    SEARCH = "SEARCH"
    GET_ALL = "GET_ALL"

class GraphMemoryInput(BaseModel):
    action: GraphAction = Field(..., description="Action: INSERT, QUERY, RELATE, FIND_PATH, SEARCH, or GET_ALL.")
    entity: Optional[str] = Field(default=None, description="Primary entity/node name (e.g. 'Victor', 'ProjectAlpha').")
    relation: Optional[str] = Field(default=None, description="Relationship edge (e.g. 'PREFERS', 'BUILT_WITH', 'USES').")
    target_entity: Optional[str] = Field(default=None, description="Target entity/node in the relation or destination for FIND_PATH.")
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata key-value pairs for the entity.")
    query_term: Optional[str] = Field(default=None, description="Search term for the SEARCH action.")

class GraphRAGMemoryIndexer(BaseSkill):
    """
    Production-grade Knowledge Graph Memory.
    Stores structured triples (Subject, Relation, Object) locally with path traversal and subgraph extraction.
    """

    def __init__(self, storage_path: str = "memory_graph.json"):
        self.storage_path = storage_path
        self._ensure_storage()

    def _ensure_storage(self):
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"nodes": {}, "edges": []}, f, indent=2)

    def _load_graph(self) -> Dict[str, Any]:
        self._ensure_storage()
        with open(self.storage_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_graph(self, data: Dict[str, Any]):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @property
    def name(self) -> str:
        return "graph_rag_memory_indexer"

    @property
    def description(self) -> str:
        return (
            "Knowledge graph memory. Use to INSERT knowledge entities, RELATE concepts, "
            "QUERY entity connections, or FIND_PATH between two concepts."
        )

    @property
    def input_schema(self) -> Type[BaseModel]:
        return GraphMemoryInput

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        data = self.input_schema(**params)
        graph = self._load_graph()

        if data.action == GraphAction.INSERT:
            if not data.entity:
                return {"success": False, "error": "Entity is required for INSERT."}
            existing = graph["nodes"].get(data.entity, {})
            existing.update(data.attributes or {})
            graph["nodes"][data.entity] = existing
            self._save_graph(graph)
            return {"success": True, "message": f"Entity '{data.entity}' stored.", "data": existing}

        elif data.action == GraphAction.RELATE:
            if not data.entity or not data.relation or not data.target_entity:
                return {"success": False, "error": "entity, relation, and target_entity are required for RELATE."}
            
            if data.entity not in graph["nodes"]:
                graph["nodes"][data.entity] = {}
            if data.target_entity not in graph["nodes"]:
                graph["nodes"][data.target_entity] = {}

            edge = {
                "source": data.entity,
                "relation": data.relation.upper(),
                "target": data.target_entity
            }
            if edge not in graph["edges"]:
                graph["edges"].append(edge)
                self._save_graph(graph)

            return {"success": True, "message": f"Connected ({data.entity}) -[{data.relation}]-> ({data.target_entity})"}

        elif data.action == GraphAction.QUERY:
            if not data.entity:
                return {"success": False, "error": "Entity is required for QUERY."}
            
            node_data = graph["nodes"].get(data.entity)
            if node_data is None:
                return {"success": True, "found": False, "message": f"Entity '{data.entity}' not found in graph."}

            outgoing = [e for e in graph["edges"] if e["source"] == data.entity]
            incoming = [e for e in graph["edges"] if e["target"] == data.entity]
            
            return {
                "success": True,
                "found": True,
                "entity": data.entity,
                "attributes": node_data,
                "outgoing_relations": outgoing,
                "incoming_relations": incoming
            }

        elif data.action == GraphAction.FIND_PATH:
            if not data.entity or not data.target_entity:
                return {"success": False, "error": "Both entity and target_entity are required to find a path."}

            # BFS for shortest path
            start, goal = data.entity, data.target_entity
            adj = {}
            for e in graph["edges"]:
                adj.setdefault(e["source"], []).append((e["target"], e["relation"]))

            queue = deque([[start]])
            visited = {start}
            path_found = None

            while queue:
                path = queue.popleft()
                node = path[-1]
                if node == goal:
                    path_found = path
                    break
                for neighbor, rel in adj.get(node, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(path + [f"-({rel})->", neighbor])

            return {
                "success": True,
                "from": start,
                "to": goal,
                "path_found": path_found is not None,
                "path": path_found or []
            }

        elif data.action == GraphAction.SEARCH:
            term = (data.query_term or "").lower()
            matching_nodes = {k: v for k, v in graph["nodes"].items() if term in k.lower() or term in str(v).lower()}
            matching_edges = [e for e in graph["edges"] if term in e["source"].lower() or term in e["target"].lower() or term in e["relation"].lower()]

            return {
                "success": True,
                "query": term,
                "matching_nodes": matching_nodes,
                "matching_edges": matching_edges
            }

        elif data.action == GraphAction.GET_ALL:
            return {
                "success": True,
                "total_nodes": len(graph["nodes"]),
                "total_edges": len(graph["edges"]),
                "graph": graph
            }

        return {"success": False, "error": f"Unknown action '{data.action}'"}
