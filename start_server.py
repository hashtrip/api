import uvicorn
from app.main import app


if __name__ == "__main__":
    # uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug", reload=False)
