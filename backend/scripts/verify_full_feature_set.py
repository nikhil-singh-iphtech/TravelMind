import asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app

async def test_full_features():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        print("\n=== 1. Testing Auth Signup & Login ===")
        email = f"user_test_{asyncio.get_event_loop().time()}@example.com"
        signup_res = await client.post("/auth/signup", json={
            "full_name": "Nikhil Singh",
            "email": email,
            "password": "SecretPassword123"
        })
        assert signup_res.status_code == 200, f"Signup failed: {signup_res.text}"
        token = signup_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Signup successful. Token received.")

        me_res = await client.get("/auth/me", headers=headers)
        assert me_res.status_code == 200
        print(f"Auth /me verified for: {me_res.json()['full_name']}")

        print("\n=== 2. Streaming Plan & Saving Run ===")
        payload = {
            "trip": {
                "origin": "DEL",
                "destination": "TYO",
                "start_date": "2026-11-01",
                "duration_days": 7,
                "budget": 300000,
                "currency": "INR",
                "travellers": 2,
                "interests": ["culture", "outdoor"]
            },
            "engine": "custom"
        }
        res = await client.post("/travel-plans/stream", json=payload, headers=headers)
        assert res.status_code == 200
        print("Stream completed.")

        print("\n=== 3. Listing Saved Travel Plans ===")
        list_res = await client.get("/travel-plans", headers=headers)
        assert list_res.status_code == 200
        plans = list_res.json()
        print(f"Found {len(plans)} saved travel plan(s).")
        assert len(plans) > 0, "No plans saved!"
        first_run_id = plans[0]["run_id"]

        print(f"\n=== 4. Fetching Single Plan Details (run_id={first_run_id}) ===")
        get_res = await client.get(f"/travel-plans/{first_run_id}", headers=headers)
        assert get_res.status_code == 200
        print("Plan fetched successfully.")

        print(f"\n=== 5. Public Shareable Link (run_id={first_run_id}) ===")
        public_res = await client.get(f"/travel-plans/public/{first_run_id}")
        assert public_res.status_code == 200
        print("Public share endpoint verified.")

        print(f"\n=== 6. Interactive Plan Refinement ===")
        refine_payload = {
            "custom_budget": 350000
        }
        refine_res = await client.post(f"/travel-plans/{first_run_id}/refine", json=refine_payload, headers=headers)
        assert refine_res.status_code == 200
        refined_data = refine_res.json()
        print("Plan refined successfully!")
        print(f"Refined status: {refined_data['status']}")

if __name__ == "__main__":
    asyncio.run(test_full_features())
