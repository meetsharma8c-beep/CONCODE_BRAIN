"""
CONCODE Neural Brain — Local Model Trainer & Deployer
Trains DistilBERT intent classifier and CodeT5 code repairer locally on Apple Silicon (Metal MPS),
and downloads the CodeLlama-7B GGUF quantized model into models/ directory.
"""

import os
import json
import torch
import numpy as np

# Enable MPS CPU fallback for Apple Silicon PyTorch ops
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoModelForSeq2SeqLM,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
)
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
from huggingface_hub import hf_hub_download

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")

def train_intent_classifier():
    print("=" * 60)
    print("  Training DistilBERT Intent Classifier (66M params)")
    print("=" * 60)
    
    output_dir = os.path.join(MODELS_DIR, "intent_classifier")
    config_file = os.path.join(output_dir, "config.json")
    safetensor_file = os.path.join(output_dir, "model.safetensors")
    if os.path.exists(config_file) and os.path.exists(safetensor_file):
        print(f"  DistilBERT intent classifier already deployed at {output_dir}\n")
        return

    intent_data_path = os.path.join(DATA_DIR, "intent_dataset.jsonl")
    if not os.path.exists(intent_data_path):
        raise FileNotFoundError(f"Missing {intent_data_path}")
        
    data = []
    with open(intent_data_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
                
    le = LabelEncoder()
    labels = le.fit_transform([d["label"] for d in data])
    label_names = list(le.classes_)
    num_labels = len(label_names)
    
    print(f"Total intent training examples: {len(data)}")
    print(f"Number of Guild Classes ({num_labels}): {label_names}")
    
    dataset = Dataset.from_dict({
        "text": [d["text"] for d in data],
        "label": labels.tolist()
    })
    
    split = dataset.train_test_split(test_size=0.1, seed=42)
    train_ds = split["train"]
    eval_ds = split["test"]
    
    model_name = "distilbert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=num_labels,
    )
    
    model.config.id2label = {i: name for i, name in enumerate(label_names)}
    model.config.label2id = {name: i for i, name in enumerate(label_names)}
    
    def tokenize_fn(examples):
        return tokenizer(examples["text"], truncation=True, max_length=128, padding="max_length")
        
    train_ds = train_ds.map(tokenize_fn, batched=True)
    eval_ds = eval_ds.map(tokenize_fn, batched=True)
    train_ds.set_format("torch", columns=["input_ids", "attention_mask", "label"])
    eval_ds.set_format("torch", columns=["input_ids", "attention_mask", "label"])
    
    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=-1)
        acc = accuracy_score(labels, preds)
        return {"accuracy": acc}
        
    output_dir = os.path.join(MODELS_DIR, "intent_classifier")
    os.makedirs(output_dir, exist_ok=True)
    
    use_mps = torch.backends.mps.is_available()
    device_arg = "mps" if use_mps else "cpu"
    print(f"Training on device: {device_arg}")
    
    training_args = TrainingArguments(
        output_dir=os.path.join(BASE_DIR, "outputs_intent"),
        num_train_epochs=3,
        per_device_train_batch_size=32,
        per_device_eval_batch_size=64,
        warmup_steps=30,
        weight_decay=0.01,
        learning_rate=5e-5,
        logging_steps=50,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        seed=42,
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        compute_metrics=compute_metrics,
    )
    
    trainer.train()
    results = trainer.evaluate()
    print(f"Intent Classifier evaluation accuracy: {results['eval_accuracy']:.4f}")
    
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Successfully saved DistilBERT intent model to: {output_dir}\n")

def train_code_repair():
    print("=" * 60)
    print("  Training CodeT5-small Code Repairer (60M params)")
    print("=" * 60)
    
    output_dir = os.path.join(MODELS_DIR, "code_repair")
    config_file = os.path.join(output_dir, "config.json")
    safetensor_file = os.path.join(output_dir, "model.safetensors")
    if os.path.exists(config_file) and os.path.exists(safetensor_file):
        print(f"  CodeT5 repair model already deployed at {output_dir}\n")
        return

    repair_data_path = os.path.join(DATA_DIR, "repair_dataset.jsonl")
    if not os.path.exists(repair_data_path):
        raise FileNotFoundError(f"Missing {repair_data_path}")
        
    data = []
    with open(repair_data_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
                
    print(f"Total repair dataset pairs: {len(data)}")
    
    dataset = Dataset.from_dict({
        "broken": [d["broken"] for d in data],
        "fixed": [d["fixed"] for d in data],
    })
    
    split = dataset.train_test_split(test_size=0.05, seed=42)
    train_ds = split["train"]
    eval_ds = split["test"]
    
    model_name = "Salesforce/codet5-small"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    
    def preprocess_fn(examples):
        inputs = ["fix code: " + code for code in examples["broken"]]
        model_inputs = tokenizer(inputs, max_length=256, truncation=True, padding="max_length")
        labels = tokenizer(text_target=examples["fixed"], max_length=256, truncation=True, padding="max_length")
        labels["input_ids"] = [
            [(l if l != tokenizer.pad_token_id else -100) for l in label]
            for label in labels["input_ids"]
        ]
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs
        
    train_ds = train_ds.map(preprocess_fn, batched=True, remove_columns=["broken", "fixed"])
    eval_ds = eval_ds.map(preprocess_fn, batched=True, remove_columns=["broken", "fixed"])
    
    output_dir = os.path.join(MODELS_DIR, "code_repair")
    os.makedirs(output_dir, exist_ok=True)
    
    use_mps = torch.backends.mps.is_available()
    
    training_args = TrainingArguments(
        output_dir=os.path.join(BASE_DIR, "outputs_repair"),
        num_train_epochs=2,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        warmup_steps=30,
        learning_rate=5e-4,
        logging_steps=50,
        eval_strategy="epoch",
        save_strategy="epoch",
        seed=42,
    )
    
    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=data_collator,
    )
    
    trainer.train()
    
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Successfully saved CodeT5 repair model to: {output_dir}\n")

def deploy_gguf_model():
    print("=" * 60)
    print("  Deploying CodeLlama GGUF Neural Weights")
    print("=" * 60)
    
    target_path = os.path.join(MODELS_DIR, "codellama-7b-concode.Q4_K_M.gguf")
    if os.path.exists(target_path) and os.path.getsize(target_path) > 1000000:
        print(f"CodeLlama GGUF already deployed at {target_path} ({os.path.getsize(target_path)/(1024**3):.2f} GB)")
        return

    print("Downloading CodeLlama-7B-Instruct GGUF (Q4_K_M) from HuggingFace...")
    downloaded_file = hf_hub_download(
        repo_id="TheBloke/CodeLlama-7B-Instruct-GGUF",
        filename="codellama-7b-instruct.Q4_K_M.gguf",
        local_dir=MODELS_DIR
    )
    
    if os.path.exists(downloaded_file):
        if downloaded_file != target_path:
            if os.path.exists(target_path):
                os.remove(target_path)
            os.rename(downloaded_file, target_path)
        print(f"Successfully deployed CodeLlama GGUF model to: {target_path}")

if __name__ == "__main__":
    train_intent_classifier()
    train_code_repair()
    deploy_gguf_model()
