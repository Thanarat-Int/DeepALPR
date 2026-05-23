"""CRNN (CNN + BiLSTM + CTC) model for Thai license-plate OCR.

Compact by design so it trains on CPU in a reasonable time. Input is a
1x32x160 grayscale plate crop; output is a (timesteps, batch, classes) tensor
of log-probabilities for CTC decoding. Shared by training and inference.
"""
import torch
import torch.nn as nn


class CRNN(nn.Module):
    def __init__(self, num_classes: int, hidden: int = 128):
        super().__init__()
        # Convolutional feature extractor. Height 32 -> 1, width 160 -> 40.
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 32, 3, 1, 1), nn.BatchNorm2d(32), nn.ReLU(True),
            nn.MaxPool2d(2, 2),                                    # 32 x 16 x 80
            nn.Conv2d(32, 64, 3, 1, 1), nn.BatchNorm2d(64), nn.ReLU(True),
            nn.MaxPool2d(2, 2),                                    # 64 x  8 x 40
            nn.Conv2d(64, 128, 3, 1, 1), nn.BatchNorm2d(128), nn.ReLU(True),
            nn.MaxPool2d((2, 1), (2, 1)),                          # 128 x 4 x 40
            nn.Conv2d(128, 128, 3, 1, 1), nn.BatchNorm2d(128), nn.ReLU(True),
            nn.MaxPool2d((2, 1), (2, 1)),                          # 128 x 2 x 40
            nn.Conv2d(128, 128, (2, 1)), nn.BatchNorm2d(128), nn.ReLU(True),  # 128 x 1 x 40
        )
        # Bidirectional LSTM sequence model.
        self.rnn = nn.LSTM(128, hidden, num_layers=2,
                           bidirectional=True, dropout=0.1)
        self.fc = nn.Linear(hidden * 2, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.cnn(x)              # (B, 128, 1, W)
        x = x.squeeze(2)             # (B, 128, W)
        x = x.permute(2, 0, 1)       # (W, B, 128)
        x, _ = self.rnn(x)           # (W, B, 2*hidden)
        x = self.fc(x)               # (W, B, num_classes)
        return x.log_softmax(2)
