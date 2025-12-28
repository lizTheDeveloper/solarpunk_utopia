#!/bin/bash
# Local LLM Inference Setup for Termux
# Only runs on devices with 8GB+ RAM

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Local LLM Inference Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check RAM (cross-platform)
if [ "$(uname)" = "Darwin" ]; then
    # macOS
    TOTAL_RAM_BYTES=$(sysctl -n hw.memsize)
    TOTAL_RAM_GB=$((TOTAL_RAM_BYTES / 1024 / 1024 / 1024))
else
    # Linux/Termux
    TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
fi

echo -e "${BLUE}Detected RAM: ${TOTAL_RAM_GB}GB${NC}"
echo ""

if [ "$TOTAL_RAM_GB" -lt 8 ]; then
    echo -e "${YELLOW}Insufficient RAM for local inference (recommended 8GB+)${NC}"
    echo -e "${YELLOW}Using cloud API (Anthropic) instead${NC}"
    exit 0
fi

echo -e "${GREEN}✓ Sufficient RAM for local inference!${NC}"
echo ""

# Select model based on RAM
if [ "$TOTAL_RAM_GB" -ge 16 ]; then
    RECOMMENDED_MODEL="Qwen3-8B (best reasoning, ~6GB)"
    MODEL_SIZE="8B"
else
    RECOMMENDED_MODEL="Qwen3-7B (balanced, ~5GB)"
    MODEL_SIZE="7B"
fi

# Ask user if they want to install
echo -e "${YELLOW}Do you want to install local LLM inference?${NC}"
echo -e "This will:"
echo -e "  - Install llama.cpp with Python bindings (~500MB)"
echo -e "  - Download ${RECOMMENDED_MODEL}"
echo -e "  - Enable offline AI agent capabilities"
echo -e ""
echo -e "Recommended model: ${RECOMMENDED_MODEL}"
echo -e "Storage required: ~6GB"
echo -e "RAM usage: ~5-7GB when running"
echo ""
read -p "Install local inference? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Skipping local inference setup${NC}"
    exit 0
fi

# Check available storage
AVAILABLE_GB=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_GB" -lt 6 ]; then
    echo -e "${RED}Insufficient storage (need 6GB+, have ${AVAILABLE_GB}GB)${NC}"
    exit 1
fi

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"

if [ "$(uname)" = "Darwin" ]; then
    # macOS - use Metal acceleration
    if ! command -v brew &> /dev/null; then
        echo -e "${RED}Homebrew required for macOS installation${NC}"
        exit 1
    fi
    brew install cmake
else
    # Termux/Linux
    pkg install -y cmake clang python-numpy 2>/dev/null || \
    sudo apt-get install -y cmake build-essential python3-numpy || true
fi

# Activate venv
. venv/bin/activate

# Install inference backend
if [ "$(uname)" = "Darwin" ]; then
    # macOS - use MLX (much faster on Apple Silicon)
    echo -e "${BLUE}Installing MLX-LM (optimized for Apple Silicon)...${NC}"
    pip install mlx-lm==0.15.0
    USE_MLX=true
else
    # Linux/Termux - use llama.cpp
    echo -e "${BLUE}Installing llama-cpp-python (this may take 10-20 minutes)...${NC}"
    CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" \
        pip install llama-cpp-python==0.2.20
    USE_MLX=false
fi

# Create models directory
mkdir -p models

# Download model
if [ "$USE_MLX" = true ]; then
    # MLX uses HuggingFace models directly (no GGUF needed)
    if [ "$MODEL_SIZE" = "8B" ]; then
        echo -e "${BLUE}Using Qwen2.5-7B-Instruct (MLX optimized)${NC}"
        MODEL_NAME="mlx-community/Qwen2.5-7B-Instruct-4bit"
        MODEL_FILE="mlx-model"  # MLX downloads automatically
    else
        echo -e "${BLUE}Using Qwen2.5-7B-Instruct (MLX optimized)${NC}"
        MODEL_NAME="mlx-community/Qwen2.5-7B-Instruct-4bit"
        MODEL_FILE="mlx-model"
    fi
    echo -e "${YELLOW}Model will be downloaded automatically on first run${NC}"
else
    # GGUF for llama.cpp
    if [ "$MODEL_SIZE" = "8B" ]; then
        echo -e "${BLUE}Downloading Qwen3-8B Instruct (Q5_K_M quantized, ~6GB)...${NC}"
        MODEL_URL="https://huggingface.co/Qwen/Qwen3-8B-Instruct-GGUF/resolve/main/qwen3-8b-instruct-q5_k_m.gguf"
        MODEL_FILE="models/qwen3-8b-instruct-q5.gguf"
        MODEL_NAME="qwen3-8b-instruct"
    else
        echo -e "${BLUE}Downloading Qwen2.5-7B Instruct (Q4_K_M quantized, ~5GB)...${NC}"
        MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf"
        MODEL_FILE="models/qwen2.5-7b-instruct-q4.gguf"
        MODEL_NAME="qwen2.5-7b-instruct"
    fi

    echo -e "${YELLOW}This will take a while depending on your connection...${NC}"

    if [ ! -f "$MODEL_FILE" ]; then
        curl -L -o "$MODEL_FILE" "$MODEL_URL"
        echo -e "${GREEN}✓ Model downloaded${NC}"
    else
        echo -e "${YELLOW}Model already exists, skipping download${NC}"
    fi
fi

# Create inference server script
cat > local_inference_server.py << 'PYEOF'
#!/usr/bin/env python3
"""
Local LLM Inference Server
Runs a local inference endpoint compatible with OpenAI API format
Supports both MLX (macOS) and llama.cpp (Linux/Termux)
"""
import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Local LLM Inference Server")

# Detect backend
USE_MLX = sys.platform == "darwin"

if USE_MLX:
    # macOS - use MLX
    from mlx_lm import load, generate
    print("Using MLX backend (Apple Silicon optimized)")
    MODEL_NAME = os.getenv("MODEL_NAME", "mlx-community/Qwen2.5-7B-Instruct-4bit")
    print(f"Loading model: {MODEL_NAME}...")
    model, tokenizer = load(MODEL_NAME)
    print("MLX model loaded successfully!")
else:
    # Linux/Termux - use llama.cpp
    from llama_cpp import Llama
    print("Using llama.cpp backend")
    MODEL_PATH = os.getenv("MODEL_PATH", "models/qwen2.5-7b-instruct-q4.gguf")
    print(f"Loading model from {MODEL_PATH}...")
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=4096,  # Context window
        n_threads=4,  # Adjust based on CPU cores
        n_gpu_layers=0,  # CPU only (no GPU on most phones)
    )
    print("llama.cpp model loaded successfully!")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    max_tokens: int = 512
    temperature: float = 0.7

class ChatResponse(BaseModel):
    content: str
    model: str = "mistral-7b-instruct-q4"

@app.get("/health")
def health():
    return {"status": "healthy", "model": "mistral-7b-instruct-q4"}

@app.post("/v1/chat/completions")
def chat_completion(request: ChatRequest) -> ChatResponse:
    """OpenAI-compatible chat completion endpoint"""

    # Format messages for Qwen
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

    try:
        if USE_MLX:
            # MLX backend
            prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            response = generate(
                model,
                tokenizer,
                prompt=prompt,
                max_tokens=request.max_tokens,
                temp=request.temperature,
                verbose=False
            )
            response_text = response.strip()
        else:
            # llama.cpp backend
            response = llm.create_chat_completion(
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )
            response_text = response['choices'][0]['message']['content']

        return ChatResponse(content=response_text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {
        "service": "Local LLM Inference",
        "model": "mistral-7b-instruct-q4",
        "endpoint": "/v1/chat/completions",
        "compatible_with": "OpenAI API format"
    }

if __name__ == "__main__":
    print("Starting local inference server on port 8005...")
    uvicorn.run(app, host="0.0.0.0", port=8005)
PYEOF

chmod +x local_inference_server.py

# Update run_all_services.sh to include inference server
if ! grep -q "local_inference_server" run_all_services.sh; then
    # Add to run_all_services.sh
    sed -i.bak '/^# Start services$/a\
start_service "local_inference" "python local_inference_server.py" "8005"' run_all_services.sh
fi

# Create .env configuration
if [ ! -f ".env" ]; then
    touch .env
fi

if ! grep -q "USE_LOCAL_INFERENCE" .env; then
    cat >> .env << 'EOF'

# Local LLM Inference
USE_LOCAL_INFERENCE=true
LOCAL_INFERENCE_URL=http://localhost:8005/v1/chat/completions
LOCAL_INFERENCE_MODEL=mistral-7b-instruct-q4
EOF
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Local Inference Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Model: Mistral 7B Instruct (4-bit quantized)"
echo -e "  Endpoint: http://localhost:8005"
echo -e "  RAM Usage: ~4-6GB when running"
echo -e "  Context: 2048 tokens"
echo ""
echo -e "${YELLOW}To start inference server:${NC}"
echo -e "  python local_inference_server.py"
echo -e ""
echo -e "${YELLOW}Or it will start automatically with:${NC}"
echo -e "  ./run_all_services.sh"
echo ""
echo -e "${YELLOW}Test it:${NC}"
echo -e '  curl http://localhost:8005/health'
echo ""
echo -e "${GREEN}Your phone can now run AI agents locally! 🤖📱${NC}"
echo ""
