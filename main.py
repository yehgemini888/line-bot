import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    # Zeabur expects the app to bind to 0.0.0.0 and the provided PORT
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=False)
