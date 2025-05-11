# File: debugiq_voice_ws_client.py

import asyncio
import websockets
import base64
import json
import sys
import os

WS_URL = "ws://localhost:8000/voice/ws"  # Adjust to Render if testing remotely

def encode_audio(file_path: str) -> str:
    """Base64 encode a .wav file."""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

async def send_voice_command(file_path: str):
    print(f"🎙️ Connecting to {WS_URL} ...")
    async with websockets.connect(WS_URL) as ws:
        print("✅ Connected.")
        audio_b64 = encode_audio(file_path)

        # Send audio payload
        await ws.send(json.dumps({
            "type": "voice_input",
            "format": "wav",
            "audio_base64": audio_b64
        }))

        # Receive and print all responses
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            print("⬇️  Response:", json.dumps(data, indent=2))

            # Exit if final result received
            if data.get("type") == "final_result":
                print("🏁 Workflow completed.")
                break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debugiq_voice_ws_client.py <audio.wav>")
        sys.exit(1)

    audio_file = sys.argv[1]
    if not os.path.exists(audio_file):
        print(f"File not found: {audio_file}")
        sys.exit(1)

    asyncio.run(send_voice_command(audio_file))
