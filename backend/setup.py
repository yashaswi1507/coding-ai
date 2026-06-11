"""
ThinkCode AI — First-time Setup Script
Run this once before starting the server.

    python setup.py

What it does:
    1. Creates seed training data (10 labeled samples)
    2. Trains the PyTorch model (150 epochs)
    3. Saves model to backend/model/thinking_model.pth
    4. Ready to run: uvicorn main:app --reload
"""

import os
import sys

# Make sure we're in the backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ".")

print("\n" + "="*50)
print("  ThinkCode AI — First-Time Setup")
print("="*50)

print("\n📦 Step 1: Creating seed training data...")
from model.data_collector import create_seed_data, get_stats
create_seed_data()
stats = get_stats()
print(f"   ✅ {stats['labeled']} labeled samples ready")

print("\n🧠 Step 2: Training the thinking model...")
print("   This takes ~30 seconds on CPU. Grab a chai ☕\n")
from model.trainer import train
train(epochs=150, batch_size=4)

print("\n✅ Setup complete!")
print("\n🚀 Start the server:")
print("   uvicorn main:app --reload")
print("\n🌐 API docs: http://localhost:8000/docs")
print("="*50 + "\n")