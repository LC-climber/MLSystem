"""
可配置的 PyTorch MLP 模型 - 用于 Optuna 超参数优化

这个版本允许自定义网络结构和训练超参数，而不是从 config 读取。
"""

import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
from src.models.base import BaseModel
from src.config import SEED


class ConfigurableTorchMLP(BaseModel):
    """
    可配置的 PyTorch MLP

    支持自定义:
    - 隐藏层维度
    - Dropout 概率
    - 学习率和权重衰减
    - Batch size 和训练轮数
    """

    algorithm = "mlp"

    def __init__(
        self,
        num_classes: int,
        hidden_dim_1: int = 128,
        hidden_dim_2: int = 64,
        dropout: float = 0.2,
        learning_rate: float = 0.001,
        weight_decay: float = 0.0001,
        batch_size: int = 128,
        max_epochs: int = 100,
        patience: int = 10,
        device: str = "cuda",
        seed: int = SEED,
    ):
        super().__init__(num_classes)

        self.num_classes = num_classes
        self.hidden_dim_1 = hidden_dim_1
        self.hidden_dim_2 = hidden_dim_2
        self.dropout = dropout
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.batch_size = batch_size
        self.max_epochs = max_epochs
        self.patience = patience
        self.device = device
        self.seed = seed

        self.model = None
        self.in_dim_ = None

        # 设置随机种子
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

    def _build_network(self, in_dim: int) -> nn.Module:
        """构建网络"""
        return nn.Sequential(
            nn.Linear(in_dim, self.hidden_dim_1),
            nn.ReLU(),
            nn.Dropout(self.dropout),
            nn.Linear(self.hidden_dim_1, self.hidden_dim_2),
            nn.ReLU(),
            nn.Dropout(self.dropout),
            nn.Linear(self.hidden_dim_2, self.num_classes),
        )

    def fit(self, X: np.ndarray, y: np.ndarray):
        """训练模型"""
        self.in_dim_ = X.shape[1]
        self.model = self._build_network(self.in_dim_).to(self.device)

        # 转换数据
        X_t = torch.tensor(X, dtype=torch.float32, device=self.device)
        y_t = torch.tensor(y, dtype=torch.long, device=self.device)

        # 计算类别权重
        class_counts = np.bincount(y, minlength=self.num_classes)
        class_weights = 1.0 / (class_counts + 1e-6)
        class_weights = class_weights / class_weights.sum() * self.num_classes
        class_weights_t = torch.tensor(class_weights, dtype=torch.float32, device=self.device)

        # 损失函数和优化器
        criterion = nn.CrossEntropyLoss(weight=class_weights_t)
        optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.learning_rate,
            weight_decay=self.weight_decay,
        )

        # 训练循环
        self.model.train()
        best_loss = float('inf')
        patience_counter = 0

        for epoch in range(self.max_epochs):
            # Shuffle
            perm = torch.randperm(len(X_t), device=self.device)

            epoch_loss = 0.0
            n_batches = 0

            for i in range(0, len(X_t), self.batch_size):
                idx = perm[i:i + self.batch_size]

                optimizer.zero_grad()
                outputs = self.model(X_t[idx])
                loss = criterion(outputs, y_t[idx])
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()
                n_batches += 1

            avg_loss = epoch_loss / n_batches

            # Early stopping
            if avg_loss < best_loss - 1e-4:
                best_loss = avg_loss
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= self.patience:
                    break

        return self

    @torch.no_grad()
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测类别"""
        self.model.eval()
        X_t = torch.tensor(X, dtype=torch.float32, device=self.device)
        logits = self.model(X_t)
        return logits.argmax(dim=1).cpu().numpy()

    @torch.no_grad()
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测概率"""
        self.model.eval()
        X_t = torch.tensor(X, dtype=torch.float32, device=self.device)
        logits = self.model(X_t)
        probs = torch.softmax(logits, dim=1)
        return probs.cpu().numpy()

    def get_params(self):
        """获取参数"""
        return {
            "algorithm": self.algorithm,
            "num_classes": self.num_classes,
            "hidden_dim_1": self.hidden_dim_1,
            "hidden_dim_2": self.hidden_dim_2,
            "dropout": self.dropout,
            "learning_rate": self.learning_rate,
            "weight_decay": self.weight_decay,
            "batch_size": self.batch_size,
            "max_epochs": self.max_epochs,
            "patience": self.patience,
            "device": self.device,
            "seed": self.seed,
        }

    def save(self, path: Path) -> None:
        """保存模型"""
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "state_dict": self.model.state_dict(),
            "in_dim": self.in_dim_,
            "params": self.get_params(),
        }, path)

    def load(self, path: Path):
        """加载模型"""
        checkpoint = torch.load(path, map_location=self.device)
        self.in_dim_ = checkpoint["in_dim"]
        self.model = self._build_network(self.in_dim_).to(self.device)
        self.model.load_state_dict(checkpoint["state_dict"])
        return self
