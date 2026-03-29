"""
KDE-70: Retrain IR+Raman-Only Models — Production Candidate
RandomForest (primary) + CNN-1D (secondary) with compound-grouped 5-fold CV

This script trains two adhesive classification models on IR/Raman spectral
intensity data. The primary model (RandomForest) is deployed to production;
the CNN-1D serves as a secondary benchmark. Both use compound-grouped
cross-validation to prevent data leakage between chemically related samples.

Inputs:
  - adhesive_spectra_ir_raman_intensities.csv (wavenumber intensity features)
Outputs:
  - model_output/rf_ir_raman_production.joblib (production RF pipeline)
  - model_output/label_encoder.joblib (class label mapping)
  - model_output/cnn1d_ir_raman.pth (CNN-1D state dict)
  - model_output/evaluation_report.json (metrics summary)
"""
import pandas as pd
import numpy as np
import json
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GroupKFold
from sklearn.metrics import (
    accuracy_score, f1_score, classification_report,
    confusion_matrix, roc_auc_score
)
import warnings
warnings.filterwarnings('ignore')

# --- Config ---
DATA_FILE = "adhesive_spectra_ir_raman_intensities.csv"
OUTPUT_DIR = Path("model_output")
OUTPUT_DIR.mkdir(exist_ok=True)
N_FOLDS = 5        # 5-fold CV balances variance estimation vs compute cost
RANDOM_STATE = 42   # Fixed seed for reproducible train/test splits

# --- Load data ---
df = pd.read_csv(DATA_FILE)
print(f"Dataset: {len(df)} samples, {df['adhesive_class'].nunique()} classes, {df['compound_name'].nunique()} compounds")

# --- Feature engineering ---
# Extract wavenumber intensity columns (wn_400 through wn_4000).
# Each column represents absorbance/intensity at a specific wavenumber bin,
# covering the mid-IR (400-4000 cm^-1) range used in IR and Raman spectroscopy.
INTENSITY_COLS = [c for c in df.columns if c.startswith('wn_')]
print(f"Spectral features: {len(INTENSITY_COLS)} wavenumber bins ({INTENSITY_COLS[0]} to {INTENSITY_COLS[-1]})")

X = df[INTENSITY_COLS].copy()
y_labels = df['adhesive_class'].values
groups = df['compound_name'].values

label_enc = LabelEncoder()
y = label_enc.fit_transform(y_labels)
class_names = label_enc.classes_
n_classes = len(class_names)

print(f"Classes: {list(class_names)}")
print(f"Class distribution: {dict(zip(class_names, np.bincount(y)))}")

# --- Preprocessing pipeline ---
preprocessor = StandardScaler()

# ============================================================
# MODEL 1: RandomForest (Primary Production Candidate)
# ============================================================
print("\n" + "="*60)
print("RANDOMFOREST — Compound-Grouped 5-Fold CV")
print("="*60)

# Hyperparameters chosen via grid search on a held-out development set:
# - n_estimators=500: diminishing returns beyond this; 500 stabilizes OOB error
# - max_depth=None: let trees grow fully -- pruning via min_samples_* instead
# - min_samples_split=5, min_samples_leaf=2: regularization to reduce overfitting
#   on small per-compound groups without losing signal
# - class_weight='balanced': compensates for unequal adhesive class frequencies
rf_pipeline = Pipeline([
    ('scaler', StandardScaler()),    # Normalize intensity features to zero mean/unit var
    ('clf', RandomForestClassifier(
        n_estimators=500,
        max_depth=None,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight='balanced',
        random_state=RANDOM_STATE,
        n_jobs=-1                    # Use all CPU cores for parallel tree fitting
    ))
])

# GroupKFold ensures no compound appears in both train and test within a fold,
# preventing data leakage from chemically similar samples of the same compound.
gkf = GroupKFold(n_splits=N_FOLDS)
rf_fold_metrics = []
rf_all_y_true = []
rf_all_y_pred = []
rf_all_y_proba = []

for fold, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups)):
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    rf_pipeline.fit(X_train, y_train)
    y_pred = rf_pipeline.predict(X_test)
    y_proba = rf_pipeline.predict_proba(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average='macro')
    f1_weighted = f1_score(y_test, y_pred, average='weighted')

    train_compounds = set(groups[train_idx])
    test_compounds = set(groups[test_idx])
    assert len(train_compounds & test_compounds) == 0, "Data leakage detected!"

    rf_fold_metrics.append({
        'fold': fold + 1,
        'accuracy': acc,
        'f1_macro': f1_macro,
        'f1_weighted': f1_weighted,
        'train_size': len(train_idx),
        'test_size': len(test_idx),
        'test_compounds': sorted(test_compounds)
    })
    rf_all_y_true.extend(y_test)
    rf_all_y_pred.extend(y_pred)
    rf_all_y_proba.extend(y_proba)

    print(f"  Fold {fold+1}: Acc={acc:.4f}, F1_macro={f1_macro:.4f}, F1_weighted={f1_weighted:.4f} "
          f"(train={len(train_idx)}, test={len(test_idx)}, test_compounds={len(test_compounds)})")

# Overall RF metrics
rf_all_y_true = np.array(rf_all_y_true)
rf_all_y_pred = np.array(rf_all_y_pred)
rf_all_y_proba = np.array(rf_all_y_proba)

rf_overall_acc = accuracy_score(rf_all_y_true, rf_all_y_pred)
rf_overall_f1_macro = f1_score(rf_all_y_true, rf_all_y_pred, average='macro')
rf_overall_f1_weighted = f1_score(rf_all_y_true, rf_all_y_pred, average='weighted')

try:
    rf_overall_auc = roc_auc_score(rf_all_y_true, rf_all_y_proba, multi_class='ovr', average='macro')
except:
    rf_overall_auc = None

print(f"\n  OVERALL RF: Acc={rf_overall_acc:.4f}, F1_macro={rf_overall_f1_macro:.4f}, "
      f"F1_weighted={rf_overall_f1_weighted:.4f}, AUC_macro={rf_overall_auc:.4f}" if rf_overall_auc else "")

print(f"\n  Per-class report (RF):")
rf_report = classification_report(rf_all_y_true, rf_all_y_pred, target_names=class_names, digits=4)
print(rf_report)

rf_cm = confusion_matrix(rf_all_y_true, rf_all_y_pred)
print("  Confusion Matrix (RF):")
print(f"  {'':>18s} " + " ".join(f"{c[:8]:>8s}" for c in class_names))
for i, row in enumerate(rf_cm):
    print(f"  {class_names[i]:>18s} " + " ".join(f"{v:>8d}" for v in row))

# Feature importance
rf_pipeline.fit(X, y)  # Retrain on full data for production model
feature_names = INTENSITY_COLS
importances = rf_pipeline.named_steps['clf'].feature_importances_
feat_imp = sorted(zip(feature_names, importances), key=lambda x: -x[1])
print(f"\n  Top 10 Features (RF):")
for name, imp in feat_imp[:10]:
    print(f"    {name}: {imp:.4f}")

# Save production RF model
joblib.dump(rf_pipeline, OUTPUT_DIR / "rf_ir_raman_production.joblib")
joblib.dump(label_enc, OUTPUT_DIR / "label_encoder.joblib")
print(f"\n  Production RF model saved: {OUTPUT_DIR / 'rf_ir_raman_production.joblib'}")

# ============================================================
# MODEL 2: CNN-1D (Secondary)
# ============================================================
print("\n" + "="*60)
print("CNN-1D — Compound-Grouped 5-Fold CV")
print("="*60)

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# Preprocess all data once — scale intensity features
X_processed = preprocessor.fit_transform(X.values)
n_features = X_processed.shape[1]
print(f"  Input features: {n_features}")

# 1D-CNN architecture: three conv blocks with increasing filter counts (64->128->128),
# decreasing kernel sizes (7->5->3) to capture progressively finer spectral features.
# BatchNorm + MaxPool after each block. AdaptiveAvgPool collapses the spatial dimension
# before a two-layer MLP head with 40% dropout for regularization.
class CNN1D(nn.Module):
    def __init__(self, n_features, n_classes):
        super().__init__()
        self.net = nn.Sequential(
            nn.Unflatten(1, (1, n_features)),         # (batch, features) -> (batch, 1, features)
            nn.Conv1d(1, 64, kernel_size=7, padding=3),   # Wide kernel captures broad spectral peaks
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(64, 128, kernel_size=5, padding=2),  # Medium kernel for mid-range patterns
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(128, 128, kernel_size=3, padding=1), # Narrow kernel for fine spectral detail
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),                       # Global average pool -> (batch, 128, 1)
            nn.Flatten(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.4),                               # 40% dropout to prevent overfitting
            nn.Linear(64, n_classes)
        )

    def forward(self, x):
        return self.net(x)

device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
print(f"  Device: {device}")

cnn_fold_metrics = []
cnn_all_y_true = []
cnn_all_y_pred = []
cnn_all_y_proba = []

for fold, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups)):
    X_train_t = torch.FloatTensor(X_processed[train_idx]).to(device)
    y_train_t = torch.LongTensor(y[train_idx]).to(device)
    X_test_t = torch.FloatTensor(X_processed[test_idx]).to(device)
    y_test_np = y[test_idx]

    # Class weights for imbalance
    class_counts = np.bincount(y[train_idx], minlength=n_classes).astype(float)
    class_weights = torch.FloatTensor(1.0 / (class_counts + 1e-6)).to(device)
    class_weights = class_weights / class_weights.sum() * n_classes

    model = CNN1D(n_features, n_classes).to(device)
    # AdamW with weight decay 1e-3 for L2 regularization; lr=5e-4 found via sweep
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-4, weight_decay=1e-3)
    criterion = nn.CrossEntropyLoss(weight=class_weights)  # Weighted loss for class imbalance
    # Cosine annealing decays lr to near-zero over 300 epochs for smooth convergence
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=300)

    train_ds = TensorDataset(X_train_t, y_train_t)
    train_dl = DataLoader(train_ds, batch_size=32, shuffle=True)

    model.train()
    for epoch in range(300):
        for xb, yb in train_dl:
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()
        scheduler.step()

    model.eval()
    with torch.no_grad():
        logits = model(X_test_t)
        proba = torch.softmax(logits, dim=1).cpu().numpy()
        preds = logits.argmax(dim=1).cpu().numpy()

    acc = accuracy_score(y_test_np, preds)
    f1_macro = f1_score(y_test_np, preds, average='macro')
    f1_weighted = f1_score(y_test_np, preds, average='weighted')

    cnn_fold_metrics.append({
        'fold': fold + 1, 'accuracy': acc,
        'f1_macro': f1_macro, 'f1_weighted': f1_weighted
    })
    cnn_all_y_true.extend(y_test_np)
    cnn_all_y_pred.extend(preds)
    cnn_all_y_proba.extend(proba)

    print(f"  Fold {fold+1}: Acc={acc:.4f}, F1_macro={f1_macro:.4f}, F1_weighted={f1_weighted:.4f}")

cnn_all_y_true = np.array(cnn_all_y_true)
cnn_all_y_pred = np.array(cnn_all_y_pred)
cnn_all_y_proba = np.array(cnn_all_y_proba)

cnn_overall_acc = accuracy_score(cnn_all_y_true, cnn_all_y_pred)
cnn_overall_f1_macro = f1_score(cnn_all_y_true, cnn_all_y_pred, average='macro')
cnn_overall_f1_weighted = f1_score(cnn_all_y_true, cnn_all_y_pred, average='weighted')

try:
    cnn_overall_auc = roc_auc_score(cnn_all_y_true, cnn_all_y_proba, multi_class='ovr', average='macro')
except:
    cnn_overall_auc = None

print(f"\n  OVERALL CNN-1D: Acc={cnn_overall_acc:.4f}, F1_macro={cnn_overall_f1_macro:.4f}, "
      f"F1_weighted={cnn_overall_f1_weighted:.4f}")

print(f"\n  Per-class report (CNN-1D):")
cnn_report = classification_report(cnn_all_y_true, cnn_all_y_pred, target_names=class_names, digits=4)
print(cnn_report)

cnn_cm = confusion_matrix(cnn_all_y_true, cnn_all_y_pred)
print("  Confusion Matrix (CNN-1D):")
print(f"  {'':>18s} " + " ".join(f"{c[:8]:>8s}" for c in class_names))
for i, row in enumerate(cnn_cm):
    print(f"  {class_names[i]:>18s} " + " ".join(f"{v:>8d}" for v in row))

# Save CNN model
torch.save(model.state_dict(), OUTPUT_DIR / "cnn1d_ir_raman.pth")

# ============================================================
# SUMMARY REPORT
# ============================================================
print("\n" + "="*60)
print("SUMMARY — IR+Raman Production Model Evaluation")
print("="*60)

# Production readiness thresholds: >=85% accuracy AND >=80% macro-F1
# These targets were set by the ML team based on domain expert requirements
targets_met_rf = rf_overall_acc >= 0.85 and rf_overall_f1_macro >= 0.80
targets_met_cnn = cnn_overall_acc >= 0.85 and cnn_overall_f1_macro >= 0.80

summary = {
    "dataset": {
        "file": DATA_FILE,
        "total_samples": len(df),
        "modalities": ["IR", "FTIR", "Raman"],
        "classes": list(class_names),
        "class_distribution": {c: int(v) for c, v in zip(class_names, np.bincount(y))},
        "unique_compounds": int(df['compound_name'].nunique()),
        "cv_method": "compound-grouped 5-fold",
    },
    "random_forest": {
        "overall_accuracy": round(rf_overall_acc, 4),
        "f1_macro": round(rf_overall_f1_macro, 4),
        "f1_weighted": round(rf_overall_f1_weighted, 4),
        "auc_macro": round(rf_overall_auc, 4) if rf_overall_auc else None,
        "targets_met": targets_met_rf,
        "fold_metrics": rf_fold_metrics,
        "model_file": "rf_ir_raman_production.joblib",
    },
    "cnn_1d": {
        "overall_accuracy": round(cnn_overall_acc, 4),
        "f1_macro": round(cnn_overall_f1_macro, 4),
        "f1_weighted": round(cnn_overall_f1_weighted, 4),
        "auc_macro": round(cnn_overall_auc, 4) if cnn_overall_auc else None,
        "targets_met": targets_met_cnn,
        "fold_metrics": [{k: v for k, v in fm.items()} for fm in cnn_fold_metrics],
        "model_file": "cnn1d_ir_raman.pth",
    },
    "recommendation": "RandomForest" if rf_overall_f1_macro >= cnn_overall_f1_macro else "CNN-1D",
}

print(f"\n  RandomForest:  Acc={rf_overall_acc:.4f}  F1={rf_overall_f1_macro:.4f}  Targets={'MET ✓' if targets_met_rf else 'NOT MET ✗'}")
print(f"  CNN-1D:        Acc={cnn_overall_acc:.4f}  F1={cnn_overall_f1_macro:.4f}  Targets={'MET ✓' if targets_met_cnn else 'NOT MET ✗'}")
print(f"\n  Production Recommendation: {summary['recommendation']}")

with open(OUTPUT_DIR / "evaluation_report.json", 'w') as f:
    json.dump(summary, f, indent=2, default=str)

print(f"\n  Full report saved: {OUTPUT_DIR / 'evaluation_report.json'}")
print("  Done.")
