import asyncio
import httpx
import sys

API_URL = "http://localhost:8000/api"


async def main():
    print("Starting Sample Run...")

    # 1. Create a Run
    payload = {
        "brands": ["AWS", "Digital Ocean", "Azure"],
        "prompts": [
            "What is the best cloud provider for enterprise?",
            "Cheapest cloud services for startups?",
        ],
        "models": ["gemini-2.0-flash"],
        "notes": "Sample CLI Run",
    }

    async with httpx.AsyncClient() as client:
        try:
            print(f"Sending request to {API_URL}/runs...")
            response = await client.post(f"{API_URL}/runs", json=payload)
            response.raise_for_status()
            run_data = response.json()
            run_id = run_data["id"]
            print(f"Run created! ID: {run_id}")

            # 2. Poll for completion
            print("Waiting for completion...")
            while True:
                status_res = await client.get(f"{API_URL}/runs/{run_id}")
                status_data = status_res.json()
                status = status_data["status"]

                if status in ["completed", "failed"]:
                    print(f"Run finished with status: {status}")
                    break

                print(f"   Status: {status}...")
                await asyncio.sleep(1)

            # 3. Get Summary
            print("Fetching Summary...")
            summary_res = await client.get(f"{API_URL}/runs/{run_id}/summary")
            summary_res.raise_for_status()
            summary = summary_res.json()

            print("\n--- Run Summary ---")
            print(f"Total Prompts: {summary['total_prompts']}")
            print(f"Total Responses: {summary['total_responses']}")
            print("\nBrand Visibility:")
            for metric in summary["metrics"]:
                print(
                    f" - {metric['brand_name']}: {metric['mentions']} mentions "
                    f"({metric['visibility_score']:.1f}%)"
                )

        except httpx.RequestError as e:
            print(f"Connection error: {e}")
            print("Make sure the server is running: uvicorn app.main:app --reload")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
