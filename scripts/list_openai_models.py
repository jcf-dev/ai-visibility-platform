import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = "https://api.openai.com/v1/models"


async def list_models():
    if not API_KEY:
        print("OPENAI_API_KEY not found in environment variables.")
        return

    print(f"Fetching available OpenAI models using key: {API_KEY[:5]}...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                BASE_URL, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            print("\nAvailable Models:")
            # Sort models by id for easier reading
            models = sorted(data.get("data", []), key=lambda x: x["id"])

            for model in models:
                print(f" - {model['id']}")

        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(list_models())
