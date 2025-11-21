#!/bin/bash
# LoRA Fine-Tuning Script
# Generated: 2025-11-21T02:28:02.067767
# Dataset: /Users/modini_red/CESAR.ai_Terry.Dells (Deploy)/cesar_ecosystem/training_data/lora_alpaca_20251121_022802.json

echo "🚀 Starting LoRA Fine-Tuning from DataBrain Curriculum"
echo "=================================================="

# Configuration
MODEL_BASE="qwen2.5:latest"  # Base model (update as needed)
DATASET="/Users/modini_red/CESAR.ai_Terry.Dells (Deploy)/cesar_ecosystem/training_data/lora_alpaca_20251121_022802.json"
OUTPUT_DIR="/Users/modini_red/CESAR.ai_Terry.Dells (Deploy)/cesar_ecosystem/lora_adapters/lora_20251121_022802"
EPOCHS=3
BATCH_SIZE=4
LEARNING_RATE=2e-4

mkdir -p "$OUTPUT_DIR"

# Option 1: Using Ollama's built-in fine-tuning (when available)
# ollama fine-tune $MODEL_BASE \
#     --dataset "$DATASET" \
#     --output "$OUTPUT_DIR" \
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
# with open("/Users/modini_red/CESAR.ai_Terry.Dells (Deploy)/cesar_ecosystem/training_data/lora_alpaca_20251121_022802.json") as f:
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
#         output_dir="/Users/modini_red/CESAR.ai_Terry.Dells (Deploy)/cesar_ecosystem/lora_adapters/lora_20251121_022802",
#         logging_steps=10,
#         save_steps=100
#     )
# )
#
# trainer.train()
# model.save_pretrained("/Users/modini_red/CESAR.ai_Terry.Dells (Deploy)/cesar_ecosystem/lora_adapters/lora_20251121_022802")
# PYTHON_SCRIPT

echo ""
echo "✅ Training complete!"
echo "   Output: $OUTPUT_DIR"
echo "   Next: Test the adapter with Ollama or merge with base model"
echo ""
echo "To use with Ollama:"
echo "   ollama create cesar-finetuned -f Modelfile"
echo ""
