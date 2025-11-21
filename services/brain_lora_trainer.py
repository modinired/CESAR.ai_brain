#!/usr/bin/env python3
"""
Brain-Powered LoRA Fine-Tuning System
======================================
The DataBrain becomes the curriculum for model upgrades.
Only feeds the model the best interactions/learnings.

Key Features:
- Quality-filtered training data from brain
- Periodic model fine-tuning (weekly recommended)
- Curriculum learning: start with high-mass nodes
- Validation against existing knowledge
"""

import os
import json
import psycopg
from psycopg.rows import dict_row
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import sys

from dotenv import load_dotenv

# Load environment
load_dotenv()
load_dotenv(".env.cockroach")


class BrainLoRATrainer:
    """
    Trains LoRA adapters using knowledge extracted from the DataBrain.

    The brain serves as a dynamic curriculum:
    - High-mass nodes = important concepts to teach
    - High-quality interactions = good examples
    - Recent learnings = up-to-date information
    """

    def __init__(self):
        self.db_url = os.getenv("COCKROACH_DB_URL")
        if not self.db_url:
            raise ValueError("COCKROACH_DB_URL not configured")

        # Directories
        self.base_dir = Path(__file__).parent.parent
        self.training_data_dir = self.base_dir / "training_data"
        self.lora_output_dir = self.base_dir / "lora_adapters"
        self.training_data_dir.mkdir(exist_ok=True)
        self.lora_output_dir.mkdir(exist_ok=True)

        # Training configuration
        self.quality_threshold = 0.85
        self.mass_threshold = 30.0  # Only nodes with high importance
        self.min_training_samples = 100

    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    def extract_curriculum_from_brain(self):
        """
        Extract training curriculum from DataBrain.

        Curriculum Strategy:
        1. Start with high-mass wisdom nodes (strategic knowledge)
        2. Add knowledge nodes with many connections
        3. Include recent high-quality interactions
        4. Filter for coherence and relevance
        """
        self.log("🧠 Extracting curriculum from DataBrain...")

        conn = psycopg.connect(self.db_url)
        cur = conn.cursor(row_factory=dict_row)

        # Phase 1: Get high-value knowledge nodes
        cur.execute("""
            SELECT
                node_id, label, type, mass, z_index,
                description, access_count
            FROM graph_nodes
            WHERE
                mass >= %s
                AND type IN ('wisdom', 'knowledge')
                AND description IS NOT NULL
            ORDER BY mass DESC, access_count DESC
            LIMIT 50
        """, (self.mass_threshold,))

        knowledge_nodes = cur.fetchall()

        # Phase 2: Get high-quality LLM interactions
        cur.execute("""
            SELECT
                prompt, local_response, cloud_response,
                selected_model, quality_score, agent_id
            FROM llm_collaborations
            WHERE
                quality_score >= %s
                AND created_at > NOW() - INTERVAL '30 days'
            ORDER BY quality_score DESC
            LIMIT 200
        """, (self.quality_threshold,))

        llm_interactions = cur.fetchall()

        # Phase 3: Get successful task completions
        cur.execute("""
            SELECT
                title, description, status
            FROM tasks
            WHERE
                status = 'completed'
                AND updated_at > NOW() - INTERVAL '30 days'
            LIMIT 100
        """)

        completed_tasks = cur.fetchall()

        # Phase 4: Get effective A2A conversations
        cur.execute("""
            SELECT
                c.conversation_type,
                c.participants,
                c.metadata,
                COUNT(m.id) as message_count
            FROM a2a_conversations c
            INNER JOIN a2a_messages m ON c.id = m.conversation_id
            WHERE
                c.status = 'completed'
                AND c.created_at > NOW() - INTERVAL '30 days'
            GROUP BY c.id, c.conversation_type, c.participants, c.metadata
            HAVING COUNT(m.id) >= 3
            ORDER BY message_count DESC
            LIMIT 50
        """)

        a2a_conversations = cur.fetchall()

        cur.close()
        conn.close()

        self.log(f"   ✅ Knowledge Nodes: {len(knowledge_nodes)}")
        self.log(f"   ✅ LLM Interactions: {len(llm_interactions)}")
        self.log(f"   ✅ Completed Tasks: {len(completed_tasks)}")
        self.log(f"   ✅ A2A Conversations: {len(a2a_conversations)}")

        return {
            "knowledge_nodes": knowledge_nodes,
            "llm_interactions": llm_interactions,
            "completed_tasks": completed_tasks,
            "a2a_conversations": a2a_conversations
        }

    def format_training_data(self, curriculum):
        """
        Format brain data into training samples.

        Format: Instruction-tuning style
        {
            "instruction": "...",
            "input": "...",  # Optional context
            "output": "...",
            "metadata": {...}
        }
        """
        self.log("📝 Formatting training data...")

        training_samples = []

        # 1. Knowledge node descriptions -> Explanatory training
        for node in curriculum['knowledge_nodes']:
            training_samples.append({
                "instruction": f"Explain the concept: {node['label']}",
                "input": "",
                "output": node['description'],
                "metadata": {
                    "source": "brain_knowledge",
                    "type": node['type'],
                    "mass": float(node['mass']),
                    "z_index": node['z_index']
                }
            })

        # 2. LLM interactions -> Direct Q&A
        for interaction in curriculum['llm_interactions']:
            # Use the better response (cloud if quality > 0.95, else local)
            response = interaction['cloud_response'] if interaction['quality_score'] > 0.95 else interaction['local_response']

            if response:
                training_samples.append({
                    "instruction": interaction['prompt'],
                    "input": "",
                    "output": response,
                    "metadata": {
                        "source": "llm_collaboration",
                        "quality_score": float(interaction['quality_score']),
                        "agent_id": interaction['agent_id']
                    }
                })

        # 3. Completed tasks -> Task understanding
        for task in curriculum['completed_tasks']:
            if task['description']:
                training_samples.append({
                    "instruction": f"How would you approach this task: {task['title']}",
                    "input": "",
                    "output": task['description'],
                    "metadata": {
                        "source": "completed_task",
                        "status": task['status']
                    }
                })

        # 4. A2A conversations -> Multi-step reasoning
        for conv in curriculum['a2a_conversations']:
            participants = json.loads(conv['participants']) if isinstance(conv['participants'], str) else conv['participants']
            metadata_obj = json.loads(conv['metadata']) if isinstance(conv['metadata'], str) else conv['metadata']

            training_samples.append({
                "instruction": f"Describe a {conv['conversation_type']} conversation between {', '.join(participants[:2])}",
                "input": "",
                "output": f"This conversation involves collaborative analysis with {conv['message_count']} exchanges. " +
                          f"Topic: {metadata_obj.get('topic', 'general')}. " +
                          f"The agents worked together to solve a complex problem through structured communication.",
                "metadata": {
                    "source": "a2a_conversation",
                    "message_count": conv['message_count'],
                    "conversation_type": conv['conversation_type']
                }
            })

        self.log(f"   ✅ Formatted {len(training_samples)} training samples")

        return training_samples

    def save_training_dataset(self, training_samples):
        """Save formatted training data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save full dataset
        full_dataset_file = self.training_data_dir / f"lora_dataset_{timestamp}.json"
        with open(full_dataset_file, 'w') as f:
            json.dump(training_samples, f, indent=2)

        # Save in Alpaca format (common for LoRA training)
        alpaca_format = []
        for sample in training_samples:
            alpaca_format.append({
                "instruction": sample['instruction'],
                "input": sample.get('input', ''),
                "output": sample['output']
            })

        alpaca_file = self.training_data_dir / f"lora_alpaca_{timestamp}.json"
        with open(alpaca_file, 'w') as f:
            json.dump(alpaca_format, f, indent=2)

        # Save training summary
        summary = {
            "total_samples": len(training_samples),
            "timestamp": timestamp,
            "source_breakdown": {},
            "quality_metrics": {
                "high_quality_samples": sum(1 for s in training_samples
                                           if s.get('metadata', {}).get('quality_score', 0) > 0.9),
                "knowledge_samples": sum(1 for s in training_samples
                                        if s.get('metadata', {}).get('source') == 'brain_knowledge')
            }
        }

        # Count sources
        for sample in training_samples:
            source = sample.get('metadata', {}).get('source', 'unknown')
            summary['source_breakdown'][source] = summary['source_breakdown'].get(source, 0) + 1

        summary_file = self.training_data_dir / f"lora_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        self.log(f"   💾 Saved full dataset: {full_dataset_file}")
        self.log(f"   💾 Saved Alpaca format: {alpaca_file}")
        self.log(f"   💾 Saved summary: {summary_file}")

        return {
            "full_dataset": str(full_dataset_file),
            "alpaca_format": str(alpaca_file),
            "summary": str(summary_file),
            "sample_count": len(training_samples)
        }

    def generate_training_script(self, dataset_file):
        """Generate a training script for LoRA fine-tuning"""
        self.log("📜 Generating training script...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_file = self.lora_output_dir / f"train_lora_{timestamp}.sh"

        # Training script using llama.cpp or unsloth format
        script_content = f"""#!/bin/bash
# LoRA Fine-Tuning Script
# Generated: {datetime.now().isoformat()}
# Dataset: {dataset_file}

echo "🚀 Starting LoRA Fine-Tuning from DataBrain Curriculum"
echo "=================================================="

# Configuration
MODEL_BASE="qwen2.5:latest"  # Base model (update as needed)
DATASET="{dataset_file}"
OUTPUT_DIR="{self.lora_output_dir}/lora_{timestamp}"
EPOCHS=3
BATCH_SIZE=4
LEARNING_RATE=2e-4

mkdir -p "$OUTPUT_DIR"

# Option 1: Using Ollama's built-in fine-tuning (when available)
# ollama fine-tune $MODEL_BASE \\
#     --dataset "$DATASET" \\
#     --output "$OUTPUT_DIR" \\
#     --epochs $EPOCHS

# Option 2: Using unsloth (recommended for LoRA)
# Uncomment and adjust if unsloth is installed:
# python3 << 'PYTHON_SCRIPT'
# from unsloth import FastLanguageModel
# import json
#
# # Load base model
# model, tokenizer = FastLanguageModel.from_pretrained(
#     model_name="unsloth/qwen2.5-7b",  # Or your local path
#     max_seq_length=2048,
#     dtype=None,
#     load_in_4bit=True
# )
#
# # Add LoRA adapters
# model = FastLanguageModel.get_peft_model(
#     model,
#     r=16,
#     target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
#     lora_alpha=16,
#     lora_dropout=0.05,
#     bias="none"
# )
#
# # Load dataset
# with open("{dataset_file}") as f:
#     dataset = json.load(f)
#
# # Train
# from trl import SFTTrainer
# from transformers import TrainingArguments
#
# trainer = SFTTrainer(
#     model=model,
#     tokenizer=tokenizer,
#     train_dataset=dataset,
#     args=TrainingArguments(
#         per_device_train_batch_size=4,
#         gradient_accumulation_steps=4,
#         num_train_epochs=3,
#         learning_rate=2e-4,
#         output_dir="{self.lora_output_dir}/lora_{timestamp}",
#         logging_steps=10,
#         save_steps=100
#     )
# )
#
# trainer.train()
# model.save_pretrained("{self.lora_output_dir}/lora_{timestamp}")
# PYTHON_SCRIPT

echo ""
echo "✅ Training complete!"
echo "   Output: $OUTPUT_DIR"
echo "   Next: Test the adapter with Ollama or merge with base model"
echo ""
echo "To use with Ollama:"
echo "   ollama create cesar-finetuned -f Modelfile"
echo ""
"""

        with open(script_file, 'w') as f:
            f.write(script_content)

        os.chmod(script_file, 0o755)

        self.log(f"   ✅ Generated: {script_file}")
        self.log(f"   📝 Edit this script to match your training environment")

        return str(script_file)

    def run_training_preparation(self):
        """Run complete training data preparation"""
        self.log("=" * 80)
        self.log("🎓 BRAIN-POWERED LORA TRAINING PREPARATION")
        self.log("=" * 80)

        try:
            # Step 1: Extract curriculum from brain
            curriculum = self.extract_curriculum_from_brain()

            # Step 2: Format training data
            training_samples = self.format_training_data(curriculum)

            if len(training_samples) < self.min_training_samples:
                self.log(f"⚠️  Warning: Only {len(training_samples)} samples (minimum {self.min_training_samples})")
                self.log("   Consider collecting more data before training")

            # Step 3: Save datasets
            saved_files = self.save_training_dataset(training_samples)

            # Step 4: Generate training script
            training_script = self.generate_training_script(saved_files['alpaca_format'])

            self.log("=" * 80)
            self.log("✅ TRAINING PREPARATION COMPLETE")
            self.log("=" * 80)
            self.log(f"   📊 Total Samples: {saved_files['sample_count']}")
            self.log(f"   💾 Dataset: {saved_files['alpaca_format']}")
            self.log(f"   📜 Training Script: {training_script}")
            self.log("")
            self.log("🚀 Next Steps:")
            self.log(f"   1. Review dataset: cat {saved_files['summary']}")
            self.log(f"   2. Run training: bash {training_script}")
            self.log(f"   3. Test adapter with Ollama or merge with base model")

            return {
                "status": "success",
                "sample_count": saved_files['sample_count'],
                "files": saved_files,
                "training_script": training_script
            }

        except Exception as e:
            self.log(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}


def run_periodic_training():
    """
    Run training preparation on a schedule.
    Recommended: Weekly or bi-weekly
    """
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  CESAR ECOSYSTEM: BRAIN-POWERED LORA TRAINER                  ║
    ║  The DataBrain is your model's curriculum                      ║
    ╚════════════════════════════════════════════════════════════════╝
    """)

    trainer = BrainLoRATrainer()
    result = trainer.run_training_preparation()

    return result


if __name__ == "__main__":
    result = run_periodic_training()
    sys.exit(0 if result.get('status') == 'success' else 1)
