"""Step D: QLoRA fine-tune of Gemma 2 2B on the SFT splits (4 GB-frugal, resumable)."""

import os

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")

import argparse
import json
import time
from pathlib import Path

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForSeq2Seq,
    Trainer,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

from app import config
from app.finetune.build_dataset import tokenize_example

OOM_LADDER = """
CUDA OUT OF MEMORY — climb the Section E ladder, re-run the smoke each time:
  1. Close other GPU users; confirm nvidia-smi baseline < 600 MiB.
  2. --max-len 384, then 256 (most effective; activations scale with seq len).
  3. --grad-accum 32 (stabilizes; keeps effective batch while batch stays 1).
  4. LoRA r=8 (edit LoraConfig in load_model_and_tokenizer; halves adapter mem).
  5. Last resort: target only ["q_proj", "v_proj"] (smallest adapter).
Record the working rung in train_summary.json and docs/PLAN.md.
"""


def load_model_and_tokenizer():
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    tokenizer = AutoTokenizer.from_pretrained(config.BASE_MODEL)
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        config.BASE_MODEL,
        quantization_config=bnb,
        device_map={"": 0},
        attn_implementation="eager",   # required for stable Gemma 2 training
        torch_dtype=torch.bfloat16,
        use_cache=False,               # required with gradient checkpointing
    )
    model = prepare_model_for_kbit_training(
        model, use_gradient_checkpointing=True
    )

    lora = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],  # attention only
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()   # expect well under 1% trainable
    return model, tokenizer


def build_trainer(model, tokenizer, train_ds, eval_ds, args):
    targs = TrainingArguments(
        output_dir=str(config.DATA_DIR / "checkpoints" / "gemma2-faraday"),
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=args.grad_accum,      # default 16
        num_train_epochs=args.epochs,                     # default 2
        max_steps=args.max_steps,                         # -1 unless smoke
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        max_grad_norm=0.3,
        bf16=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="paged_adamw_8bit",
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=args.eval_steps,                       # default 100
        save_strategy="steps",
        save_steps=args.save_steps,                       # default 100
        save_total_limit=2,
        group_by_length=True,
        dataloader_pin_memory=False,
        report_to="none",
    )
    collator = DataCollatorForSeq2Seq(
        tokenizer, padding=True, label_pad_token_id=-100
    )
    return Trainer(
        model=model,
        args=targs,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=collator,
        processing_class=tokenizer,   # transformers >=4.46; use tokenizer= if older
    )


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="QLoRA-train Gemma 2 2B.")
    parser.add_argument("--epochs", type=float, default=2)
    parser.add_argument("--grad-accum", type=int, default=16)
    parser.add_argument("--max-steps", type=int, default=-1)
    parser.add_argument("--eval-steps", type=int, default=100)
    parser.add_argument("--save-steps", type=int, default=100)
    parser.add_argument("--max-len", type=int, default=512)
    args = parser.parse_args()

    from datasets import Dataset

    train_rows = _read_jsonl(config.DATA_DIR / "sft_train.jsonl")
    eval_rows = _read_jsonl(config.DATA_DIR / "sft_eval.jsonl")
    train_ds = Dataset.from_list(train_rows)
    eval_ds = Dataset.from_list(eval_rows)

    model, tokenizer = load_model_and_tokenizer()
    train_ds = train_ds.map(
        lambda ex: tokenize_example(ex, tokenizer, args.max_len),
        remove_columns=train_ds.column_names,
    )
    eval_ds = eval_ds.map(
        lambda ex: tokenize_example(ex, tokenizer, args.max_len),
        remove_columns=eval_ds.column_names,
    )

    trainer = build_trainer(model, tokenizer, train_ds, eval_ds, args)

    output_dir = Path(config.DATA_DIR / "checkpoints" / "gemma2-faraday")
    resume = bool(output_dir.exists() and any(output_dir.glob("checkpoint-*")))

    torch.cuda.reset_peak_memory_stats()
    start = time.perf_counter()
    try:
        result = trainer.train(resume_from_checkpoint=True if resume else None)
    except torch.cuda.OutOfMemoryError:
        print(OOM_LADDER)
        raise
    wall = time.perf_counter() - start

    config.ADAPTER_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(config.ADAPTER_DIR))
    tokenizer.save_pretrained(str(config.ADAPTER_DIR))

    eval_metrics = trainer.evaluate()
    eval_loss = eval_metrics.get("eval_loss")
    train_loss = result.training_loss
    peak_vram = torch.cuda.max_memory_allocated() / 1e9
    trainable, total = model.get_nb_trainable_parameters()
    trainable_pct = 100.0 * trainable / total
    peft_cfg = model.peft_config["default"]

    summary = {
        "final_train_loss": train_loss,
        "final_eval_loss": eval_loss,
        "global_steps": trainer.state.global_step,
        "peak_vram_gb": round(peak_vram, 3),
        "trainable_pct": round(trainable_pct, 4),
        "wall_seconds": round(wall, 1),
        "rung": {
            "max_len": args.max_len,
            "grad_accum": args.grad_accum,
            "lora_r": peft_cfg.r,
            "lora_targets": list(peft_cfg.target_modules),
        },
        "args": vars(args),
    }
    with open(config.ADAPTER_DIR / "train_summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    print(
        f"trainable% {trainable_pct:.4f} | peak VRAM {peak_vram:.2f} GB | "
        f"train_loss {train_loss:.4f} | eval_loss {eval_loss:.4f} | "
        f"steps {trainer.state.global_step} | wall {wall / 60:.1f} min"
    )
    print(f"adapter saved -> {config.ADAPTER_DIR}")


if __name__ == "__main__":
    main()
