# AI Inference on the Mesh - Quick Start

Share your GPU/CPU with the community - **automatically enabled** during setup! 🚀

## For Providers (Share Your Compute)

### Automatic Setup (Recommended)

When you run `./setup.sh`, AI inference is automatically configured if Ollama is installed:

```bash
./setup.sh
```

It will:
- ✅ Install AI inference dependencies
- ✅ Download lightweight model (llama3.2:1b - ~1.3GB)
- ✅ Configure priority system (Local > Community > Network)
- ✅ Start automatically with other services

### Manual Setup

```bash
# 1. Install Ollama (one-time setup)
curl -fsSL https://ollama.com/install.sh | sh

# 2. Start sharing!
cd ai_inference_node
./start_inference_node.sh
```

**That's it!** Your node is now providing AI to the mesh network.

### Priority System (Default)

Your device automatically prioritizes requests:

1. **LOCAL (Highest)** - Your own device/apps get first priority
2. **COMMUNITY (Medium)** - Your community members get second priority
3. **NETWORK (Lowest)** - Everyone else gets remaining capacity

This ensures your local use is never blocked by network requests! The mesh will track your contributions in the gift economy. No payment needed - just sharing! 🎁

### What You're Running

- **Local AI models** (llama3.2:3b by default - lightweight!)
- **Auto-registers** with mesh on startup
- **Tracks contributions** via ValueFlows
- **Handles requests** from other nodes automatically

### Resource Requirements

- **Minimum**: 4GB RAM (CPU-only, ~20 tokens/sec)
- **Recommended**: 8GB RAM + 4GB VRAM (~50-100 tokens/sec)
- **Models**: Auto-downloads on first run (2-7GB)

### Configuration

Edit these before running:

```bash
export DEFAULT_MODEL="llama3.2:1b"    # Lighter/faster
export MAX_CONCURRENT="10"             # More requests
export PORT="8003"                     # Different port
```

See `ai_inference_node/README.md` for full options.

## For Users (Request AI from Mesh)

Use AI inference from any mesh node:

```python
from ai_inference_node.client import InferenceClient

async with InferenceClient(requester_id="alice") as client:
    response = await client.infer(
        prompt="What is a gift economy?",
        temperature=0.7,
    )
    print(response)
```

The client:
- **Auto-discovers** available nodes
- **Picks the best** one (lowest load)
- **Handles failover** if nodes go down
- **Tracks usage** for gift economy

### Test It

```bash
cd ai_inference_node
python test_inference.py
```

## Integration with Existing Agents

The 14 AI agents in `agents/` can now use mesh inference instead of external APIs!

Example:
```python
# agents/matchmaking_agent.py

from ai_inference_node.client import InferenceClient

async def analyze_offer(offer):
    async with InferenceClient(requester_id="matchmaking-agent") as client:
        response = await client.infer(
            prompt=f"Analyze this offer: {offer.title}\n{offer.description}",
            system_prompt="You are a matchmaking agent for a gift economy.",
            model="llama3.2:3b"
        )
        return response
```

**No API keys needed!** Use the compute people are gifting to the mesh.

## Why This is Cool

### Traditional Approach
- Pay OpenAI/Anthropic for every request
- Centralized control
- Privacy concerns
- Costs scale with usage

### Mesh Approach
- **Free** - people gift their idle compute
- **Decentralized** - no single point of failure
- **Private** - data stays on the mesh
- **Abundant** - more nodes = more capacity

### Gift Economy Tracking

Every inference request creates a gift record:
- **Giver**: Your inference node
- **Receiver**: The requesting agent
- **Gift**: Compute resources (measured in tokens)

This builds **reputation** and tracks the flow of abundance through the network.

## Advanced: Run on Android

1. Install Termux
2. Install Ollama for Android
3. Run the inference node:

```bash
pkg install python
cd solarpunk_utopia/ai_inference_node
./start_inference_node.sh
```

Now your **phone** is providing AI to the mesh while it charges at night! ⚡️

## Monitoring

Check your contributions:

```bash
# Node status
curl http://localhost:8005/status

# Your gift history
curl http://localhost:8000/vf/events?provider_id=YOUR_NODE_ID
```

## Troubleshooting

### "Ollama not found"
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### "Out of memory"
Use a smaller model:
```bash
export DEFAULT_MODEL="llama3.2:1b"
```

### "Port already in use"
```bash
export PORT="8006"
```

## Philosophy

This is about **technological abundance**. GPUs sit idle most of the time. Why not share them?

The mesh makes AI inference a **common good**, not a commodity. No blockchain, no payment, no artificial scarcity.

Just people helping people. 🌱

---

**Full docs**: `ai_inference_node/README.md`
