import aiohttp
import asyncio

async def get_user_birthdate(api_key: str, user_id: int):
    url = f"https://api.telegram.org/bot{api_key}/getChat"
    data = {
        "chat_id": user_id,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            if response.status == 200:
                response_json = await response.json()
                birthdate = response_json.get("result", {}).get('birthdate', None)
                if birthdate:
                    day = birthdate.get('day')
                    month = birthdate.get('month')
                    if day and month:
                        return f"{day:02d}.{month:02d}"
                return None
            else:
                print(f"Error: {response.status}")
                return None