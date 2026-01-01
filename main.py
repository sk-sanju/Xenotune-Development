from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from music_loop import generate_and_upload_loop, generate_music, upload_to_firebase
import threading

app = FastAPI()

# Allow CORS for local dev or frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global shared state
music_state = {
    "mode": "focus",
    "user_id": None,
    "current_slot": "M1",  # M1 or M2
    "replace_requested": False,
}

stop_flag = {"value": False}
thread = None

@app.post("/generate")
async def generate_music_endpoint(request: Request, background_tasks: BackgroundTasks):
    """
    Starts music generation loop for a given user and mode.
    Uploads M1.mp3 to Firebase initially.
    """
    global thread, stop_flag, music_state

    payload = await request.json()
    user_id = payload.get("user_id")
    mode = payload.get("mode", "focus")

    if not user_id:
        return JSONResponse(content={"error": "user_id is required"}, status_code=400)

    # Update shared state
    music_state["user_id"] = user_id
    music_state["mode"] = mode
    music_state["current_slot"] = "M1"
    music_state["replace_requested"] = False
    stop_flag["value"] = False

    # Generate and upload M1.mp3 immediately
    local_path = generate_music(mode)
    if not local_path:
        return JSONResponse(content={"error": "Music generation failed."}, status_code=500)

    firebase_path = f"users/{user_id}/M1.mp3"
    download_url = upload_to_firebase(local_path, firebase_path)

    # Start background loop to handle replacements
    def run_loop():
        generate_and_upload_loop(music_state, stop_flag)

    thread = threading.Thread(target=run_loop)
    thread.start()

    return {
        "status": "success",
        "mode": mode,
        "download_url": download_url,
        "message": f"{mode.capitalize()} music generated and uploaded as M1.mp3."
    }

@app.post("/replace")
async def replace_music():
    """
    Signals the music loop to regenerate the inactive slot.
    """
    if not music_state["user_id"]:
        return JSONResponse(content={"error": "Music not started. Call /generate first."}, status_code=400)

    music_state["replace_requested"] = True

    return {
        "status": "queued",
        "message": f"Replacement requested. Will generate the next inactive slot (currently playing {music_state['current_slot']})."
    }

@app.post("/stop")
async def stop_music():
    """
    Stops the music loop and background thread.
    """
    global thread
    stop_flag["value"] = True
    music_state["replace_requested"] = False

    if thread and thread.is_alive():
        thread.join()

    return {"status": "stopped", "message": "Music generation loop has been stopped."}
