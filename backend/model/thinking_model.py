"""
ThinkCode AI — PyTorch Thinking Model
Self-trainable neural network for evaluating code + thinking quality.
No external APIs. Fully local.

Architecture:
    Input (25 features)
        ↓
    FC Layer 1: 25 → 64  (BatchNorm + ReLU + Dropout 0.3)
        ↓
    FC Layer 2: 64 → 32  (BatchNorm + ReLU + Dropout 0.2)
        ↓
    FC Layer 3: 32 → 16  (ReLU)
        ↙           ↘
    Score Head      Approach Head
    16 → 1          16 → 4
    Sigmoid×100     Softmax
    (0-100 score)   (4 approach classes)

Approach classes:
    0 = brute_force
    1 = basic
    2 = optimized
    3 = optimal
"""

import torch
import torch.nn as nn

INPUT_SIZE = 25
APPROACH_CLASSES = 4
APPROACH_LABELS = ["brute_force", "basic", "optimized", "optimal"]


class ThinkingModel(nn.Module):

    def __init__(self, input_size=INPUT_SIZE, hidden1=64, hidden2=32, hidden3=16):
        super(ThinkingModel, self).__init__()

        # Shared feature extraction layers
        self.shared = nn.Sequential(
            # Layer 1
            nn.Linear(input_size, hidden1),
            nn.BatchNorm1d(hidden1),
            nn.ReLU(),
            nn.Dropout(0.3),

            # Layer 2
            nn.Linear(hidden1, hidden2),
            nn.BatchNorm1d(hidden2),
            nn.ReLU(),
            nn.Dropout(0.2),

            # Layer 3
            nn.Linear(hidden2, hidden3),
            nn.ReLU(),
        )

        # Score head: predicts thinking score (0-100)
        self.score_head = nn.Sequential(
            nn.Linear(hidden3, 1),
            nn.Sigmoid()  # Output: 0-1, multiply by 100
        )

        # Approach head: classifies coding approach
        self.approach_head = nn.Sequential(
            nn.Linear(hidden3, APPROACH_CLASSES)
            # No Softmax here — CrossEntropyLoss includes it
        )

    def forward(self, x):
        shared = self.shared(x)
        score = self.score_head(shared) * 100     # Scale to 0-100
        approach_logits = self.approach_head(shared)
        return score, approach_logits

    def predict_score(self, x):
        """Returns just the thinking score (0-100)."""
        self.eval()
        with torch.no_grad():
            score, _ = self.forward(x)
        return score.item()

    def predict_approach(self, x):
        """Returns the predicted approach label."""
        self.eval()
        with torch.no_grad():
            _, logits = self.forward(x)
            idx = torch.argmax(logits, dim=1).item()
        return APPROACH_LABELS[idx]