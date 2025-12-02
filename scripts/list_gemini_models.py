import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


async def list_models():
    if not API_KEY:
        print("GEMINI_API_KEY not found in environment variables.")
        return

    print(f"Fetching available Gemini models using key: {API_KEY[:5]}...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}?key={API_KEY}", timeout=10.0)
            response.raise_for_status()
            data = response.json()

            print("\nAvailable Models:")
            for model in data.get("models", []):
                name = model.get("name")
                display_name = model.get("displayName")
                methods = model.get("supportedGenerationMethods", [])

                if "generateContent" in methods:
                    print(f" - {name} ({display_name})")

        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(list_models())
