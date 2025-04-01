# debug_app.py
from backend.app.main import app
import uvicorn

if __name__ == "__main__":
    # Print all registered routes
    print("Registered routes:")
    for route in app.routes:
        print(f"  {route.path} [{', '.join(route.methods)}]")

    # Start the app for manual testing
    uvicorn.run(app, host="127.0.0.1", port=8000)
