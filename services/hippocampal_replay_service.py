#!/usr/bin/env python3
"""
==================================================================================
🧠 CESAR.ai Hippocampal Replay Engine (Auto-Fine-Tuning Pipeline)
==================================================================================

PURPOSE
-------
Converts the "Living Data Brain" (Graph State) into "Muscle Memory" (Model Weights).
This service runs on a schedule (e.g. nightly) to create training data for LOCAL LLMs.

LOCAL MODEL TARGETS (CURRENT ECOSYSTEM)
---------------------------------------
- Qwen2.5 Coder (code-specialized local model)
- Llama 3 (general reasoning local model)

ARCHITECTURE
------------
1. CONNECT:
   - Fetches 'Wisdom' (Z >= 300) and high-mass nodes from Supabase
   - Integrates with existing memory_semantic table

2. FORMAT:
   - Converts Graph connections into Q&A Instruction Pairs (Alpaca-style schema)
   - Each pair includes metadata about which LOCAL MODELS it is intended for

3. EXPORT:
   - Generates per-model .jsonl files:
       ./replay_out/qwen2_5_coder_cortex_evolution_<DATE>.jsonl
       ./replay_out/llama_3_cortex_evolution_<DATE>.jsonl
   - Each line: {instruction, input, output, target_models, meta}

INTEGRATION WITH CESAR ECOSYSTEM
---------------------------------
- Uses existing database_async.py for Supabase connection
- Reads from memory_semantic and knowledge_graph_links tables
- Compatible with migration 010_synthetic_organism_visualization.sql
- Scheduled via cron or N8n workflow automation

==================================================================================
"""

import json
import os
import datetime
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

# CESAR Ecosystem imports
import asyncpg
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------------
# MODEL REGISTRY – LOCAL MODELS CURRENTLY IN THE ECOSYSTEM
# ---------------------------------------------------------------------------------

MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "qwen2_5_coder": {
        "description": "Local Qwen2.5 Coder model (code-focused)",
        "format": "alpaca",
        "max_seq_len": 4096,
        "specialization": "code_generation",
    },
    "llama_3": {
        "description": "Local Llama 3 base / instruct model",
        "format": "alpaca",
        "max_seq_len": 8192,
        "specialization": "general_reasoning",
    },
}


# ---------------------------------------------------------------------------------
# LIVING DATA BRAIN INTERFACE (Supabase-backed)
# ---------------------------------------------------------------------------------

class BrainInterface:
    """
    Interface to the Living Data Brain (Supabase-backed Knowledge Graph).

    Integrates with CESAR's existing PostgreSQL/Supabase schema:
    - memory_semantic: Core knowledge nodes
    - knowledge_graph_links: Relationships between nodes
    """

    def __init__(self, db_connection_string: str):
        self.db_url = db_connection_string
        self.conn: Optional[asyncpg.Connection] = None

    async def connect(self):
        """Establish async database connection"""
        self.conn = await asyncpg.connect(self.db_url)

    async def disconnect(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()

    async def fetch_high_value_memories(self) -> List[Dict[str, Any]]:
        """
        Fetches nodes that have 'solidified' into facts.

        Criteria:
            1. Layer = Wisdom or Knowledge (node_type in ['wisdom', 'knowledge'])
            2. Mass/confidence > 50 (Highly verified/used)
            3. Access count > 5 (Frequently referenced)
        """
        if not self.conn:
            raise RuntimeError("Database not connected. Call connect() first.")

        query = """
            SELECT
                m.id::text,
                m.concept as label,
                m.node_type as type,
                m.summary as description,
                m.confidence_score,
                m.access_count,
                ARRAY_AGG(DISTINCT linked.concept) FILTER (WHERE linked.concept IS NOT NULL) as neighbors,
                ARRAY_AGG(DISTINCT l.link_strength) FILTER (WHERE l.link_strength IS NOT NULL) as link_strengths
            FROM memory_semantic m
            LEFT JOIN knowledge_graph_links l ON m.id = l.source_memory_id
            LEFT JOIN memory_semantic linked ON l.target_memory_id = linked.id
            WHERE m.node_type IN ('wisdom', 'knowledge')
              AND m.confidence_score >= 0.5
              AND m.access_count >= 5
            GROUP BY m.id, m.concept, m.node_type, m.summary, m.confidence_score, m.access_count
            ORDER BY m.confidence_score DESC, m.access_count DESC
            LIMIT 100
        """

        rows = await self.conn.fetch(query)

        memories = []
        for row in rows:
            memories.append({
                "id": row["id"],
                "label": row["label"],
                "type": row["type"],
                "description": row["description"] or f"High-value {row['type']} node: {row['label']}",
                "neighbors": row["neighbors"] or [],
                "confidence_score": float(row["confidence_score"]),
                "access_count": row["access_count"],
                "link_strengths": [float(s) for s in (row["link_strengths"] or [])]
            })

        return memories


# ---------------------------------------------------------------------------------
# DATASET GENERATOR
# ---------------------------------------------------------------------------------

class DatasetGenerator:
    """
    Turns Knowledge Graph nodes into instruction-tuning pairs
    suitable for Qwen2.5 Coder and Llama 3 fine-tuning.

    Follows Alpaca instruction format for maximum compatibility.
    """

    def __init__(self, target_models: List[str]):
        # Validate models against registry
        for m in target_models:
            if m not in MODEL_REGISTRY:
                raise ValueError(f"Unknown model ID in registry: {m!r}")
        self.target_models = target_models
        self.training_pairs: List[Dict[str, Any]] = []

    def generate_instruction_tuning(self, nodes: List[Dict[str, Any]]) -> None:
        """
        Converts Graph Nodes into LLM training examples.
        Focus: teach the models to REASON over the graph, not just memorize text.

        Training Strategies:
        1. Direct Recall: "What is X?" -> Description
        2. Relational Reasoning: "How does X relate to Y?" -> Graph traversal
        3. Multi-hop Inference: "Given X, what can we infer about Z?" -> Chain reasoning
        """
        for node in nodes:
            node_id = node.get("id")
            label = node.get("label", "Unknown Concept")
            description = node.get("description", "").strip()
            neighbors = node.get("neighbors") or []
            node_type = node.get("type", "knowledge")
            confidence = node.get("confidence_score", 0.0)

            # Common metadata for training monitoring
            meta = {
                "node_id": node_id,
                "node_type": node_type,
                "neighbors": neighbors,
                "confidence_score": confidence,
                "created_at": datetime.datetime.now().isoformat(),
            }

            # 1. Direct Recall Training (All Models) ---------------------------------------
            self.training_pairs.append({
                "instruction": f"Explain the strategic context of '{label}'.",
                "input": "",
                "output": description,
                "target_models": self.target_models,
                "meta": meta,
            })

            # 2. Relational / Graph Reasoning Training (All Models) ------------------------
            if neighbors:
                neighbors_str = ", ".join(neighbors)
                relational_output = (
                    f"The concept '{label}' is fundamentally linked to: "
                    f"{neighbors_str}. These factors should be analyzed "
                    f"concurrently when reasoning about '{label}'. "
                    f"This relationship has a confidence score of {confidence:.2f}."
                )

                self.training_pairs.append({
                    "instruction": f"Identify the key factors influencing '{label}'.",
                    "input": "Use the internal Knowledge Graph relationships.",
                    "output": relational_output,
                    "target_models": self.target_models,
                    "meta": meta,
                })

            # 3. Code-Specific Training (Qwen2.5 Coder Only) ------------------------------
            if "qwen2_5_coder" in self.target_models and any(
                kw in label.lower() for kw in ["code", "api", "function", "class", "implementation"]
            ):
                code_output = (
                    f"When implementing features related to '{label}', "
                    f"consider the following context: {description}. "
                    f"Key dependencies include: {neighbors_str if neighbors else 'none identified'}."
                )

                self.training_pairs.append({
                    "instruction": f"Generate implementation guidance for '{label}'.",
                    "input": "Provide code-specific recommendations.",
                    "output": code_output,
                    "target_models": ["qwen2_5_coder"],
                    "meta": {**meta, "specialization": "code"},
                })

            # 4. Strategic Reasoning (Llama 3 Only) ---------------------------------------
            if "llama_3" in self.target_models and node_type == "wisdom":
                strategic_output = (
                    f"From a strategic perspective, '{label}' represents: {description}. "
                    f"This insight was derived from analysis of {len(neighbors)} related factors "
                    f"and has been validated with {confidence:.0%} confidence."
                )

                self.training_pairs.append({
                    "instruction": f"Provide strategic analysis of '{label}'.",
                    "input": "Frame this as executive-level strategic insight.",
                    "output": strategic_output,
                    "target_models": ["llama_3"],
                    "meta": {**meta, "specialization": "strategy"},
                })

    def save_per_model_jsonl(self, out_dir: str) -> Dict[str, str]:
        """
        Exports one JSONL file per local model.

        Returns:
            Dict mapping model_id -> file_path for downstream processing
        """
        os.makedirs(out_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d")

        output_files = {}

        for model_id in self.target_models:
            filename = os.path.join(
                out_dir, f"{model_id}_cortex_evolution_{timestamp}.jsonl"
            )

            # Filter pairs relevant to this model
            model_pairs = [
                p for p in self.training_pairs
                if model_id in p["target_models"]
            ]

            with open(filename, "w", encoding="utf-8") as f:
                for entry in model_pairs:
                    # Clone and narrow metadata to this specific model
                    entry_for_model = dict(entry)
                    entry_for_model["target_models"] = [model_id]
                    json.dump(entry_for_model, f, ensure_ascii=False)
                    f.write("\n")

            output_files[model_id] = filename

            print(
                f"✅ HIPPOCAMPAL REPLAY COMPLETE for {model_id}: "
                f"{len(model_pairs)} memories -> {filename}"
            )

        return output_files


# ---------------------------------------------------------------------------------
# EXECUTION PIPELINE
# ---------------------------------------------------------------------------------

async def run_hippocampal_replay(
    db_url: str,
    output_dir: str = "./replay_out",
    target_models: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Main execution pipeline for hippocampal replay.

    Args:
        db_url: PostgreSQL/Supabase connection string
        output_dir: Directory for JSONL output files
        target_models: List of model IDs to generate data for (default: all)

    Returns:
        Dictionary with execution stats and output file paths
    """
    print("🧠 Initiating CESAR.ai Hippocampal Replay (Memory Consolidation Mode)...")
    print(f"Target Directory: {output_dir}")

    # 1. Interface with the Living Brain (Supabase-backed)
    brain = BrainInterface(db_url)
    await brain.connect()

    try:
        memories = await brain.fetch_high_value_memories()
        print(f"📊 Retrieved {len(memories)} high-value memories from Knowledge Graph")

        # 2. Generate training data for specified models
        if target_models is None:
            target_models = list(MODEL_REGISTRY.keys())

        generator = DatasetGenerator(target_models=target_models)
        generator.generate_instruction_tuning(memories)

        print(f"🔄 Generated {len(generator.training_pairs)} training pairs")

        # 3. Export JSONL datasets per model
        output_files = generator.save_per_model_jsonl(output_dir)

        print("\n✨ HIPPOCAMPAL REPLAY COMPLETE")
        print("📁 Output Files:")
        for model_id, filepath in output_files.items():
            print(f"   {model_id}: {filepath}")

        print("\n🚀 Ready for LoRA / Unsloth fine-tuning on Qwen2.5 Coder & Llama 3")

        return {
            "status": "success",
            "memories_processed": len(memories),
            "training_pairs_generated": len(generator.training_pairs),
            "output_files": output_files,
            "models": target_models,
            "timestamp": datetime.datetime.now().isoformat(),
        }

    finally:
        await brain.disconnect()


# ---------------------------------------------------------------------------------
# CLI ENTRY POINT
# ---------------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    # Get database URL from environment or command line
    db_url = os.getenv("DATABASE_URL")
    if not db_url and len(sys.argv) > 1:
        db_url = sys.argv[1]

    if not db_url:
        print("❌ ERROR: DATABASE_URL not set")
        print("Usage: python hippocampal_replay_service.py [DATABASE_URL]")
        sys.exit(1)

    # Run async pipeline
    result = asyncio.run(run_hippocampal_replay(db_url))

    # Print summary
    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print(json.dumps(result, indent=2))
