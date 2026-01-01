import os
import firebase_admin
from firebase_admin import credentials, storage
import json
firebase_initialized = False
firebase_key_path = "firebase_key.json"

def write_service_account_file():
    # key_content = os.getenv("FIREBASE_CRED_PATH", "assets/serviceAccountKey.json")
    key_content = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if not key_content:
        raise RuntimeError("Firebase key not found in environment variables.")

    # Save the JSON content to a file
    with open(firebase_key_path, "w") as f:
        json.dump(json.loads(key_content), f)

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = firebase_key_path

def init_firebase():
    global firebase_initialized
    if firebase_initialized:
        return

    write_service_account_file()

    if not os.path.exists(firebase_key_path):
        raise FileNotFoundError(f"Firebase credential file not found at: {firebase_key_path}")

    cred = credentials.Certificate(firebase_key_path)
      
    firebase_admin.initialize_app(cred, {
        'storageBucket': os.getenv('FIREBASE_BUCKET', 'xenotune-fromx.appspot.com')  # ✅ corrected bucket name
    })

    firebase_initialized = True

# def init_firebase():
#     """Initialize the Firebase Admin SDK once."""
#     global firebase_initialized
#     if firebase_initialized:
#         return

#     cred_path = os.getenv("FIREBASE_CRED_PATH", "assets\serviceAccountKey.json")
#     if not os.path.exists(cred_path):
#         raise FileNotFoundError(f"❌ Firebase credential file not found at: {cred_path}")

#     firebase_bucket = os.getenv("FIREBASE_BUCKET", "xenotune-fromx.firebasestorage.app")
#     cred = credentials.Certificate(cred_path)
#     firebase_admin.initialize_app(cred, {
#         'storageBucket': firebase_bucket
#     })

#     firebase_initialized = True
#     print(f"✅ Firebase initialized with bucket: {firebase_bucket}")


def upload_to_firebase(local_file_path: str, firebase_path: str) -> str:
    """Uploads a file to Firebase Storage and returns the public URL."""
    init_firebase()

    if not os.path.isfile(local_file_path):
        raise FileNotFoundError(f"❌ Local file not found: {local_file_path}")

    try:
        bucket = storage.bucket()
        blob = bucket.blob(firebase_path)

        blob.upload_from_filename(local_file_path)
        blob.make_public()

        print(f"✅ Uploaded to Firebase: {firebase_path}")
        return blob.public_url

    except Exception as e:
        print(f"❌ Firebase upload failed: {e}")
        raise


if __name__ == "__main__":
    try:
        url = upload_to_firebase("output/music.mp3", "generated_music/music.mp3")
        print(f"Public URL: {url}")
    except Exception as err:
        print(f"Error: {err}")
