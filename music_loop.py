from music_gen import generate_music
from firebase import upload_to_firebase
import time
import os
from json_gen import main

def generate_and_upload_loop(music_state, stop_flag):
    print("🔁 Music generation/upload loop started...")

    try:
        current_mode = music_state.get("mode", "focus")
        current_user = music_state.get("user_id")
        current_slot = "M1"
        next_slot = "M2"

        # ✅ Initial generation and upload of M1
        initial_file = generate_music(current_mode)
        if not initial_file or not os.path.exists(initial_file):
            print("❌ Failed to generate initial music.")
            return

        upload_to_firebase(initial_file, f"users/{current_user}/{current_slot}.mp3")
        print(f"☁️ Uploaded {current_slot}.mp3")
        main()
        

        # ✅ Generate next file immediately
        next_file = generate_music(current_mode)
        upload_to_firebase(next_file, f"users/{current_user}/{next_slot}.mp3")
        print(f"☁️ Uploaded {next_slot}.mp3")

        # 🔁 Replace loop continues until stopped
        while not stop_flag["value"]:
            main()
            # Wait for frontend to call /replace before replacing the next slot
            print(f"⏳ Waiting for /replace to be triggered (Next: {current_slot})...")
            while not music_state.get("replace_requested"):
                if stop_flag["value"]:
                    return
                time.sleep(0.5)

            # Reset flag
            music_state["replace_requested"] = False

            # ✅ Regenerate the currently inactive slot
            print(f"🔁 Regenerating and replacing: {current_slot}")
            new_file = generate_music(current_mode)
            if new_file and os.path.exists(new_file):
                upload_to_firebase(new_file, f"users/{current_user}/{current_slot}.mp3")
                print(f"☁️ Replaced: {current_slot}.mp3")
            else:
                print(f"⚠️ Generation failed for slot: {current_slot}")

            # 🔄 Switch slots
            current_slot, next_slot = next_slot, current_slot

    finally:
        print("🛑 Music loop stopped.")
