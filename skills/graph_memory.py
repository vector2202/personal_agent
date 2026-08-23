import json
import os
from enum import Enum
from typing import Type, Dict, Any, Optional, List
from pydantic import BaseModel, Field
from skills.base import BaseSkill

class GraphAction(str, Enum):
    INSERT = "INSERT"
    QUERY = "QUERY"
    RELATE = "RELATE"
    GET_ALL = "GET_ALL"

class GraphMemoryInput(BaseModel):
    action: GraphAction = Field(..., description="Action to perform: INSERT, QUERY, RELATE, or GET_ALL.")
    entity: Optional[str] = Field(default=None, description="Primary entity/node name (e.g. 'Victor', 'ProjectAlpha').")
    relation: Optional[str] = Field(default=None, description="Relationship edge (e.g. 'PREFERS', 'BUILT_WITH', 'USES').")
    target_entity: Optional[str] = Field(default=None, description="Target entity/node in the relation.")
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata key-value pairs for the entity.")

class GraphRAGMemoryIndexer(BaseSkill):
    """
    Persistent Knowledge Graph Memory. Stores structured triples (Subject, Relation, Object)
    locally in a JSON file without token inflation or full-file context dumps.
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
        return "Manages long-term structured memory triples (nodes and relationships) in a knowledge graph."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return GraphMemoryInput

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        data = self.input_schema(**params)
        graph = self._load_graph()

        if data.action == GraphAction.INSERT:
            if not data.entity:
                return {"success": False, "error": "Entity is required for INSERT."}
            graph["nodes"][data.entity] = data.attributes or {}
            self._save_graph(graph)
            return {"success": True, "message": f"Entity '{data.entity}' inserted.", "entity": data.entity}

        elif data.action == GraphAction.RELATE:
            if not data.entity or not data.relation or not data.target_entity:
                return {"success": False, "error": "entity, relation, and target_entity are required for RELATE."}
            
            # Ensure nodes exist
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

            return {"success": True, "message": f"Created relation: ({data.entity}) -[{data.relation}]-> ({data.target_entity})"}

        elif data.action == GraphAction.QUERY:
            if not data.entity:
                return {"success": False, "error": "Entity is required for QUERY."}
            
            entity_nodes = {data.entity: graph["nodes"].get(data.entity, {})}
            connected_edges = [
                e for e in graph["edges"]
                if e["source"] == data.entity or e["target"] == data.entity
            ]
            
            return {
                "success": True,
                "entity": data.entity,
                "node_data": entity_nodes.get(data.entity),
                "connections": connected_edges
            }

        elif data.action == GraphAction.GET_ALL:
            return {
                "success": True,
                "total_nodes": len(graph["nodes"]),
                "total_edges": len(graph["edges"]),
                "graph": graph
            }

        return {"success": False, "error": f"Unknown action '{data.action}'"}
