# RESOURCES

## 開発環境

- Python 3.14.5
- pip 26.1.1
- NVIDIA CUDA 13.1 / RTX 4070

## 依存パッケージ

- `torch`, `torchvision`（CUDA版、`--extra-index-url`必須）
- `ultralytics`（SAM 2.1）
- `transformers`（Grounding DINO）
- `fastapi`, `uvicorn[standard]`, `python-multipart`
- `pillow`, `opencv-python`, `numpy`

## モデル

- SAM 2.1-L: `https://github.com/ultralytics/assets/releases/download/v8.4.0/sam2.1_l.pt`
- Grounding DINO: `IDEA-Research/grounding-dino-base`（HF Hub）

## 本番環境（予定）

- `C:\Vyrezchik\`
