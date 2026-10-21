FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    CONCODE_REQUIRE_API_KEY=1 \
    CMAKE_ARGS="-DGGML_CUDA=on" \
    FORCE_CMAKE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        cmake \
        curl \
        git \
        libgomp1 \
        ninja-build \
        python3 \
        python3-dev \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python3 -m pip install --upgrade pip setuptools wheel scikit-build-core \
    && python3 -m pip install -r /app/requirements.txt \
    && python3 -c "from llama_cpp import llama_cpp; assert llama_cpp.llama_supports_gpu_offload(), 'llama.cpp was built without CUDA offload'"

COPY src/ /app/src/
COPY data/guilds.yaml data/clarifying_questions.yaml data/empathy_templates.yaml /app/data/

EXPOSE 8000
CMD ["python3", "-m", "uvicorn", "src.service:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
