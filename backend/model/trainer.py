"""
ThinkCode AI — Model Trainer
Trains the PyTorch thinking model on collected data.

Usage:
    python -m model.trainer                  # Train with all available data
    python -m model.trainer --epochs 100     # Custom epochs
    python -m model.trainer --seed-only      # Use only manually labeled seed data
    python -m model.trainer --eval           # Just evaluate saved model

The trained model is saved to: model/thinking_model.pth
"""

import os
import json
import argparse
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split

from model.feature_extractor import extract_features
from model.thinking_model import ThinkingModel, APPROACH_LABELS
from model.data_collector import get_all_training_data, create_seed_data, get_stats

MODEL_PATH = os.path.join(os.path.dirname(__file__), "thinking_model.pth")
APPROACH_TO_IDX = {label: i for i, label in enumerate(APPROACH_LABELS)}


# ── Dataset ────────────────────────────────────────────────────────────────────

class ThinkingDataset(Dataset):

    def __init__(self, samples: list):
        self.samples = samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        s = self.samples[idx]

        # Extract 25 features
        features = extract_features(
            s.get("code", ""),
            s.get("thinking_text", "")
        )

        x = torch.tensor(features, dtype=torch.float32)

        # Score label (0-100 → normalized 0-1 for training stability)
        score = torch.tensor(
            [s.get("thinking_score", 50) / 100.0],
            dtype=torch.float32
        )

        # Approach label (integer index)
        approach_str = s.get("approach", "basic")
        approach_idx = APPROACH_TO_IDX.get(approach_str, 1)
        approach = torch.tensor(approach_idx, dtype=torch.long)

        return x, score, approach


# ── Training ───────────────────────────────────────────────────────────────────

def train(epochs=150, batch_size=8, lr=0.001, seed_only=False):
    print("\n🧠 ThinkCode AI — Model Trainer")
    print("=" * 40)

    # ── Load data ──────────────────────────────────────────────────────────────
    print("\n📊 Loading training data...")

    stats = get_stats()
    print(f"   Total submissions : {stats['total_submissions']}")
    print(f"   Labeled           : {stats['labeled']}")
    print(f"   Unlabeled         : {stats['unlabeled']}")

    all_data = get_all_training_data()

    if seed_only:
        all_data = [s for s in all_data if s.get("labeled", False)]
        print(f"   Using labeled only: {len(all_data)} samples")

    if len(all_data) < 4:
        print("\n⚠️  Not enough training data! Creating seed data first...")
        create_seed_data()
        all_data = get_all_training_data()

    print(f"\n✅ Training on {len(all_data)} samples")

    dataset = ThinkingDataset(all_data)

    # ── Train/val split ────────────────────────────────────────────────────────
    val_size = max(1, int(len(dataset) * 0.2))
    train_size = len(dataset) - val_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    # ── Model ──────────────────────────────────────────────────────────────────
    model = ThinkingModel()

    # Load existing weights if available (continue training)
    if os.path.exists(MODEL_PATH):
        model.load_state_dict(torch.load(MODEL_PATH, weights_only=True))
        print("📂 Loaded existing model weights — continuing training")
    else:
        print("🆕 Training from scratch")

    # ── Loss functions ─────────────────────────────────────────────────────────
    score_loss_fn = nn.MSELoss()
    approach_loss_fn = nn.CrossEntropyLoss()

    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, patience=15, factor=0.5, min_lr=1e-5
    )

    # ── Training loop ──────────────────────────────────────────────────────────
    print(f"\n🚀 Training for {epochs} epochs...\n")
    best_val_loss = float("inf")

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0

        for x, score, approach in train_loader:
            optimizer.zero_grad()

            pred_score, pred_approach = model(x)

            # Score loss (normalize score back to 0-1 for loss comparison)
            s_loss = score_loss_fn(pred_score / 100.0, score)

            # Approach classification loss
            a_loss = approach_loss_fn(pred_approach, approach)

            # Combined loss (equal weight)
            loss = s_loss + a_loss
            loss.backward()

            # Gradient clipping for stability
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            total_loss += loss.item()

        # ── Validation ─────────────────────────────────────────────────────────
        model.eval()
        val_loss = 0.0
        val_score_mae = 0.0
        val_approach_correct = 0

        with torch.no_grad():
            for x, score, approach in val_loader:
                pred_score, pred_approach = model(x)
                s_loss = score_loss_fn(pred_score / 100.0, score)
                a_loss = approach_loss_fn(pred_approach, approach)
                val_loss += (s_loss + a_loss).item()

                # Score MAE (in 0-100 range)
                val_score_mae += torch.abs(pred_score.squeeze() - score.squeeze() * 100).mean().item()

                # Approach accuracy
                preds = torch.argmax(pred_approach, dim=1)
                val_approach_correct += (preds == approach).float().mean().item()

        avg_val_loss = val_loss / max(len(val_loader), 1)
        avg_val_mae = val_score_mae / max(len(val_loader), 1)
        avg_approach_acc = val_approach_correct / max(len(val_loader), 1)

        scheduler.step(avg_val_loss)

        # Save best model
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), MODEL_PATH)

        # Print progress every 10 epochs
        if epoch % 10 == 0 or epoch == 1:
            print(f"   Epoch {epoch:4d}/{epochs} | "
                  f"Train Loss: {total_loss/len(train_loader):.4f} | "
                  f"Val Loss: {avg_val_loss:.4f} | "
                  f"Score MAE: {avg_val_mae:.1f} | "
                  f"Approach Acc: {avg_approach_acc:.2%}")

    print(f"\n✅ Training complete!")
    print(f"   Best val loss : {best_val_loss:.4f}")
    print(f"   Model saved   : {MODEL_PATH}")
    return model


def evaluate():
    """Quick evaluation of the saved model on all training data."""
    if not os.path.exists(MODEL_PATH):
        print("❌ No saved model found. Train first.")
        return

    print("\n📊 Evaluating saved model...")
    model = ThinkingModel()
    model.load_state_dict(torch.load(MODEL_PATH, weights_only=True))
    model.eval()

    data = get_all_training_data()
    if not data:
        print("No data to evaluate on.")
        return

    total_mae = 0.0
    approach_correct = 0

    for s in data:
        features = extract_features(s.get("code", ""), s.get("thinking_text", ""))
        x = torch.tensor([features], dtype=torch.float32)

        with torch.no_grad():
            pred_score, pred_approach = model(x)

        predicted_score = pred_score.item()
        actual_score = s.get("thinking_score", 50)
        total_mae += abs(predicted_score - actual_score)

        pred_approach_label = APPROACH_LABELS[torch.argmax(pred_approach).item()]
        if pred_approach_label == s.get("approach", "basic"):
            approach_correct += 1

    print(f"\n   Samples evaluated : {len(data)}")
    print(f"   Score MAE         : {total_mae / len(data):.1f} points")
    print(f"   Approach Accuracy : {approach_correct / len(data):.2%}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ThinkCode AI Model Trainer")
    parser.add_argument("--epochs", type=int, default=150)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seed-only", action="store_true")
    parser.add_argument("--eval", action="store_true")
    args = parser.parse_args()

    if args.eval:
        evaluate()
    else:
        train(
            epochs=args.epochs,
            batch_size=args.batch_size,
            lr=args.lr,
            seed_only=args.seed_only
        )