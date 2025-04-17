import httpx
from logger import Logger

CLOUDFLARE_API_TOKEN = "your-cloudflare-api-token"
ZONE_ID = "your-zone-id"

log = Logger(__name__).get_logger()

async def http_post(url, headers=None, payload=None):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, headers=headers, json=payload)

        log.info(f"Request to {url} returned status {response.status_code}")

        if response.status_code >= 400:
            log.warning(f"Error response: {response.text}")
            return {
                "success": False,
                "status": response.status_code,
                "error": response.json().get("errors", "Unknown error"),
            }

        return {
            "success": True,
            "status": response.status_code,
            "data": response.json(),
        }

    except httpx.RequestError as exc:
        log.error(f"Request to {url} failed: {str(exc)}")
        return {
            "success": False,
            "status": None,
            "error": str(exc),
        }


async def purge_cache(hosts: list):
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/purge_cache"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"hosts": hosts}
    return await http_post(url, headers=headers, payload=payload)
