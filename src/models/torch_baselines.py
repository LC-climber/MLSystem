"""
PyTorch Baseline Models

Deep-learning system in the P1 comparison. LR and MLP (03_plan_p1_v2.md §5.4):
- LR : nn.Linear(in, num_classes), CrossEntropyLoss(weight=class_weights), Adam 1e-3
- MLP: [Linear-ReLU-Dropout(0.2)]x2 -> Linear, AdamW 1e-3, EarlyStopping patience=10

Wrapped in the BaseModel numpy-in/numpy-out interface so the shared CV loop drives
it identically to sklearn/Spark. Class imbalance handled via CrossEntropyLoss
weights (so, unlike sklearn MLP, the torch MLP *can* use balanced weights).
"""

from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
from sklearn.utils.class_weight import compute_class_weight
from sklearn.model_selection import train_test_split

from src.config import MLP_TORCH_CONFIG
from src.models.base import BaseModel
from src.utils.reproducibility import get_torch_device
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TorchBaseModel(BaseModel):
    """Shared training/predict logic for torch models; subclass sets the network."""

    system = "pytorch"
    optimizer_name = "adam"  # subclass overrides ("adam" | "adamw")

    def __init__(
        self,
        num_classes: int,
        class_weight: str = "balanced",
        seed: int = 42,
        epochs: int = 100,
        lr: float = 1e-3,
        batch_size: int = 128,
        patience: int = 0,
        weight_decay: float = 0.0,
    ):
        super().__init__(num_classes, class_weight, seed)
        self.epochs = epochs
        self.lr = lr
        self.batch_size = batch_size
        self.patience = patience
        self.weight_decay = weight_decay
        self.device = get_torch_device()
        self.in_dim_ = None
        self.peak_gpu_mem_gb = None

    def _build_network(self, in_dim: int) -> nn.Module:
        raise NotImplementedError

    def _make_optimizer(self, params):
        if self.optimizer_name == "adamw":
            return torch.optim.AdamW(params, lr=self.lr, weight_decay=self.weight_decay)
        return torch.optim.Adam(params, lr=self.lr)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "TorchBaseModel":
        torch.manual_seed(self.seed)
        self.in_dim_ = X.shape[1]
        self.model = self._build_network(self.in_dim_).to(self.device)

        # Balanced class weights for CrossEntropyLoss
        weight = None
        if self.class_weight == "balanced":
            classes = np.arange(self.num_classes)
            cw = compute_class_weight("balanced", classes=classes, y=y)
            weight = torch.tensor(cw, dtype=torch.float32, device=self.device)
        criterion = nn.CrossEntropyLoss(weight=weight)
        optimizer = self._make_optimizer(self.model.parameters())

        # Internal split for early stopping (MLP); LR (patience=0) trains all data
        if self.patience > 0:
            X_tr, X_va, y_tr, y_va = train_test_split(
                X, y, test_size=0.1, random_state=self.seed, stratify=y
            )
            X_va_t = torch.tensor(X_va, dtype=torch.float32, device=self.device)
            y_va_t = torch.tensor(y_va, dtype=torch.long, device=self.device)
        else:
            X_tr, y_tr = X, y
            X_va_t = y_va_t = None

        X_tr_t = torch.tensor(X_tr, dtype=torch.float32, device=self.device)
        y_tr_t = torch.tensor(y_tr, dtype=torch.long, device=self.device)
        n = X_tr_t.shape[0]

        if self.device == "cuda":
            torch.cuda.reset_peak_memory_stats()

        best_val, best_state, bad = float("inf"), None, 0
        for _ in range(self.epochs):
            self.model.train()
            perm = torch.randperm(n, device=self.device)
            for i in range(0, n, self.batch_size):
                idx = perm[i:i + self.batch_size]
                optimizer.zero_grad()
                loss = criterion(self.model(X_tr_t[idx]), y_tr_t[idx])
                loss.backward()
                optimizer.step()

            if self.patience > 0:
                self.model.eval()
                with torch.no_grad():
                    vloss = criterion(self.model(X_va_t), y_va_t).item()
                if vloss < best_val - 1e-4:
                    best_val = vloss
                    best_state = {k: v.detach().clone() for k, v in self.model.state_dict().items()}
                    bad = 0
                else:
                    bad += 1
                    if bad >= self.patience:
                        break

        if best_state is not None:
            self.model.load_state_dict(best_state)

        if self.device == "cuda":
            self.peak_gpu_mem_gb = torch.cuda.max_memory_allocated() / (1024 ** 3)

        return self

    @torch.no_grad()
    def _forward_logits(self, X: np.ndarray) -> torch.Tensor:
        self.model.eval()
        X_t = torch.tensor(X, dtype=torch.float32, device=self.device)
        return self.model(X_t)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._forward_logits(X).argmax(dim=1).cpu().numpy()

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return torch.softmax(self._forward_logits(X), dim=1).cpu().numpy()

    def get_params(self):
        return {
            **super().get_params(),
            "epochs": self.epochs,
            "lr": self.lr,
            "batch_size": self.batch_size,
            "patience": self.patience,
            "weight_decay": self.weight_decay,
            "optimizer": self.optimizer_name,
            "device": self.device,
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"state_dict": self.model.state_dict(), "in_dim": self.in_dim_}, path)


class TorchLogisticRegression(TorchBaseModel):
    """Linear softmax classifier (Adam, no early stopping)."""

    algorithm = "lr"
    optimizer_name = "adam"

    def _build_network(self, in_dim: int) -> nn.Module:
        return nn.Linear(in_dim, self.num_classes)


class TorchMLP(TorchBaseModel):
    """[Linear-ReLU-Dropout]x2 -> Linear (AdamW, early stopping)."""

    algorithm = "mlp"
    optimizer_name = "adamw"

    def __init__(self, num_classes, class_weight="balanced", seed=42):
        super().__init__(
            num_classes,
            class_weight,
            seed,
            epochs=MLP_TORCH_CONFIG["epochs"],
            lr=MLP_TORCH_CONFIG["lr"],
            batch_size=MLP_TORCH_CONFIG["batch_size"],
            patience=MLP_TORCH_CONFIG["early_stopping_patience"],
        )
        self.hidden_dims = MLP_TORCH_CONFIG["hidden_dims"]
        self.dropout = MLP_TORCH_CONFIG["dropout"]

    def _build_network(self, in_dim: int) -> nn.Module:
        layers, prev = [], in_dim
        for h in self.hidden_dims:
            layers += [nn.Linear(prev, h), nn.ReLU(), nn.Dropout(self.dropout)]
            prev = h
        layers.append(nn.Linear(prev, self.num_classes))
        return nn.Sequential(*layers)
