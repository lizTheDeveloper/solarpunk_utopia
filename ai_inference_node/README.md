# AI Inference Node - Share Your Compute with the Mesh

This is a **dead simple** way to contribute AI inference to the mesh network. Just run one command and you're providing AI to your community!

## 🚀 Quick Start (2 minutes!)

```bash
cd ai_inference_node
./start_inference_node.sh
```

That's it! Your node is now serving AI to the mesh. 🎉

## What This Does

- **Runs AI models locally** using Ollama (or other backends)
- **Automatically registers** with the mesh network
- **Tracks contributions** in the gift economy
- **Handles requests** from other mesh nodes
- **Super simple** - one command to start

## Requirements

- **Ollama** (recommended): https://ollama.com
  - Install: `curl -fsSL https://ollama.com/install.sh | sh`
  - Or use OpenAI API, llama.cpp, or any compatible endpoint

- **Python 3.8+** (already on most systems)

## How It Works

### 1. Someone Needs AI
A mesh node needs to analyze offers, match needs, or generate a response.

### 2. Request Finds Your Node
The request is routed to available inference nodes (yours!)

### 3. You Provide the Answer
Your local AI model processes the request and returns the response.

### 4. Contribution Tracked
Your gift of compute is logged in the ValueFlows system.

## Configuration

Set environment variables before running:

```bash
# Node identification
export NODE_ID="my-inference-node"

# Backend selection
export INFERENCE_BACKEND="ollama"        # ollama, openai, llamacpp
export INFERENCE_URL="http://localhost:11434"
export DEFAULT_MODEL="llama3.2:3b"       # or llama3.2:1b for faster/lighter

# Resource limits
export MAX_CONCURRENT="5"                # Concurrent requests
export MAX_TOKENS="2048"                 # Max tokens per request
export TIMEOUT="120"                     # Request timeout (seconds)

# Mesh integration
export DTN_BUNDLE_URL="http://localhost:8000"
export REGISTER_WITH_MESH="true"
export TRACK_CONTRIBUTIONS="true"

# Port
export PORT="8005"
```

## Available Models (Ollama)

Lightweight (good for laptops):
```bash
ollama pull llama3.2:1b    # 1B params - very fast
ollama pull llama3.2:3b    # 3B params - balanced (default)
```

More capable (needs more RAM/GPU):
```bash
ollama pull llama3.1:8b    # 8B params - high quality
ollama pull mixtral:8x7b   # 47B params - best quality
```

Check available models:
```bash
ollama list
```

## Using Different Backends

### OpenAI API
```bash
export INFERENCE_BACKEND="openai"
export INFERENCE_URL="https://api.openai.com"
export OPENAI_API_KEY="sk-..."
export DEFAULT_MODEL="gpt-4o-mini"
```

### Local llama.cpp Server
```bash
# Start llama.cpp server first
./llama-server -m model.gguf -c 2048 --port 8080

# Then configure node
export INFERENCE_BACKEND="openai"  # llama.cpp uses OpenAI-compatible API
export INFERENCE_URL="http://localhost:8080"
export DEFAULT_MODEL="llama"
```

## API Endpoints

### Check Status
```bash
curl http://localhost:8005/status
```

Returns:
```json
{
  "node_id": "inference-node-abc123",
  "backend": "ollama",
  "available_models": ["llama3.2:3b", "llama3.1:8b"],
  "max_concurrent": 5,
  "current_load": 0,
  "total_served": 42,
  "uptime_seconds": 3600.5
}
```

### Run Inference
```bash
curl -X POST http://localhost:8005/inference \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is a gift economy?",
    "model": "llama3.2:3b",
    "requester_id": "alice"
  }'
```

Returns:
```json
{
  "response": "A gift economy is...",
  "model": "llama3.2:3b",
  "tokens_used": 150,
  "provider_node": "inference-node-abc123",
  "timestamp": "2025-01-15T12:34:56"
}
```

## Gift Economy Integration

Every inference request you serve is tracked as a contribution:

- **Provider**: Your node ID
- **Receiver**: The requester's ID
- **Resource**: AI inference (measured in tokens)
- **Value**: Compute resources you gifted

This builds your reputation and tracks the flow of gifts through the network.

No payment needed - it's a **gift**! 🎁

## Hardware Requirements

### Minimum (CPU only)
- **Model**: llama3.2:1b
- **RAM**: 4GB
- **Speed**: ~20 tokens/sec

### Recommended (good GPU)
- **Model**: llama3.2:3b or llama3.1:8b
- **RAM**: 8GB+
- **GPU**: 4GB VRAM+
- **Speed**: ~50-100 tokens/sec

### High Performance
- **Model**: mixtral:8x7b
- **RAM**: 32GB+
- **GPU**: 24GB VRAM+
- **Speed**: ~30-50 tokens/sec

## Troubleshooting

### Ollama not found
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Model download slow
Models are downloaded once, then cached. First pull takes time!

### Out of memory
Use a smaller model:
```bash
export DEFAULT_MODEL="llama3.2:1b"
```

### Port already in use
```bash
export PORT="8006"  # or any free port
```

## Security Notes

- This service listens on `0.0.0.0` (all interfaces) to serve the mesh
- No authentication by default (gift economy = open access)
- Set resource limits (`MAX_CONCURRENT`, `MAX_TOKENS`) to prevent abuse
- For production, consider adding rate limiting or auth

## Advanced Usage

### Run as Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/ai-inference-node.service
```

```ini
[Unit]
Description=Solarpunk AI Inference Node
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/solarpunk_utopia/ai_inference_node
ExecStart=/path/to/solarpunk_utopia/ai_inference_node/start_inference_node.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-inference-node
sudo systemctl start ai-inference-node
```

### Monitor Contributions

Check what you've provided:
```bash
curl http://localhost:8000/vf/events?provider_id=YOUR_NODE_ID&event_type=service_provided
```

### Multiple Models

Run multiple inference nodes on different ports with different models:

```bash
# Fast responses
PORT=8005 DEFAULT_MODEL="llama3.2:1b" ./start_inference_node.sh &

# Quality responses
PORT=8006 DEFAULT_MODEL="llama3.1:8b" ./start_inference_node.sh &
```

## Contributing

Want to improve the inference node? PRs welcome!

Ideas:
- GPU detection and auto-configuration
- Model auto-selection based on request complexity
- Queue management and priority system
- Response caching
- Multi-model routing
- Fine-tuned models for specific mesh tasks

## Philosophy

This is about **sharing abundance**. If you have a GPU sitting idle, why not share it with your community?

No blockchain, no tokens, no payment - just **people helping people**.

The mesh remembers your gifts. 🌱
