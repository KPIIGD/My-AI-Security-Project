# Korean PII Guardrail sidecar — real NER v3 (klue-roberta-large) on CPU.
#
# v0.2 패키지 소스/configs/NER 모델은 빌드에 COPY 하지 않고 compose volume 으로
# 마운트한다(빠른 반복 + 1.3GB 모델 이미지 미포함). 이미지는 런타임 의존성만 설치.
FROM python:3.12-slim

WORKDIR /app

# torch 는 CPU 전용 wheel 로 설치(이미지 축소). transformers/safetensors 는 NER 런타임.
RUN pip install --no-cache-dir \
        "fastapi>=0.110" "uvicorn[standard]>=0.29" \
        "transformers>=4.40.0" "safetensors>=0.4.0" "huggingface_hub>=0.23" \
 && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY app.py /app/app.py

# v0.2 패키지는 /pkg/src 에 마운트되어 PYTHONPATH 로 import. 모델은 로컬 마운트라 오프라인.
ENV PYTHONPATH=/pkg/src \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
