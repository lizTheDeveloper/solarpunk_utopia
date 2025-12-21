"""ValueFlows Node entry point"""
from valueflows_node.app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
