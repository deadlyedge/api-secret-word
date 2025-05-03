import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def test_maker_api(client):
    # Test case 1: pass_code already exists
    data1 = {
        "wordsArea": "test words 1",
        "passArea": "existing_pass_code",
        "phrase_code": "testphrase1",
        "picture": None
    }
    response1 = await client.post(f"{BASE_URL}/maker", json=data1)
    print("Maker Test 1 status:", response1.status_code)
    print("Maker Test 1 response:", response1.json())

    # Test case 2: new pass_code with phrase_code, no picture
    data2 = {
        "wordsArea": "test words 2",
        "passArea": "new_pass_code_2",
        "phrase_code": "testphrase2",
        "picture": None
    }
    response2 = await client.post(f"{BASE_URL}/maker", json=data2)
    print("Maker Test 2 status:", response2.status_code)
    print("Maker Test 2 response:", response2.json())

    # Test case 3: new pass_code with words only, no phrase_code, no picture (should error)
    data3 = {
        "wordsArea": "test words 3",
        "passArea": "new_pass_code_3",
        "phrase_code": None,
        "picture": None
    }
    response3 = await client.post(f"{BASE_URL}/maker", json=data3)
    print("Maker Test 3 status:", response3.status_code)
    print("Maker Test 3 response:", response3.json())

async def test_tTag_api(client):
    # Test case 1: valid pass_code and phrase_code
    data1 = {
        "passArea": "new_pass_code_2",
        "phrase_code": "testphrase2"
    }
    response1 = await client.post(f"{BASE_URL}/tTag", json=data1)
    print("tTag Test 1 status:", response1.status_code)
    try:
        print("tTag Test 1 response:", response1.json())
    except Exception as e:
        print("tTag Test 1 response JSON decode error:", e)

    # Test case 2: missing pass_code
    data2 = {
        "phrase_code": "testphrase2"
    }
    response2 = await client.post(f"{BASE_URL}/tTag", json=data2)
    print("tTag Test 2 status:", response2.status_code)
    try:
        print("tTag Test 2 response:", response2.json())
    except Exception as e:
        print("tTag Test 2 response JSON decode error:", e)

    # Test case 3: no matching record
    data3 = {
        "passArea": "nonexistent_pass",
        "phrase_code": "nonexistent_phrase"
    }
    response3 = await client.post(f"{BASE_URL}/tTag", json=data3)
    print("tTag Test 3 status:", response3.status_code)
    try:
        print("tTag Test 3 response:", response3.json())
    except Exception as e:
        print("tTag Test 3 response JSON decode error:", e)

async def main():
    async with httpx.AsyncClient() as client:
        await test_maker_api(client)
        await test_tTag_api(client)

if __name__ == "__main__":
    asyncio.run(main())
