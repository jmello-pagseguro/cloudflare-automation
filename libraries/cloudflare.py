import httpx, os, re
from core.logger import Logger
from typing import List, Dict, Optional, Union, Any

class Cloudflare:
    def __init__(
        self,
        logger: Optional[Logger] = None
    ):
        """
        Initialize the Cloudflare cache purger.
        
        :param api_token: Cloudflare API token
        :param zone_id: Cloudflare zone ID
        :param timeout: HTTP request timeout in seconds (default: 10)
        :param logger: Optional custom logger instance
        """
        self.api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        self.zone_id = '123'
        self.apps = []
        self.timeout = 30
        self.log = logger if logger else Logger(__name__).get_logger()
    
    async def _http_get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Union[bool, int, str, Dict]]:
        """
        Internal method to make HTTP GET requests.
        
        :param url: Target URL
        :param headers: Request headers
        :param params: Query parameters
        :return: Dictionary with response details
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, params=params)

            self.log.info(f"Request to {url} returned status {response.status_code}")

            if response.status_code >= 400:
                self.log.warning(f"Error response: {response.text}")
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
            self.log.error(f"Request to {url} failed: {str(exc)}")
            return {
                "success": False,
                "status": None,
                "error": str(exc),
            }
    
    async def _http_post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict] = None
    ) -> Dict[str, Union[bool, int, str, Dict]]:
        """
        Internal method to make HTTP POST requests.
        
        :param url: Target URL
        :param headers: Request headers
        :param payload: Request payload
        :return: Dictionary with response details
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)

            self.log.info(f"Request to {url} returned status {response.status_code}")

            if response.status_code >= 400:
                self.log.warning(f"Error response: {response.text}")
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
            self.log.error(f"Request to {url} failed: {str(exc)}")
            return {
                "success": False,
                "status": None,
                "error": str(exc),
            }
        

    async def get_zone_id(self, zone_name: str) -> Dict[str, Union[bool, int, str, Dict]]:
        """
        Get the Cloudflare zone ID for a given zone name.
        
        :param zone_name: Name of the zone
        :return: Dictionary with zone ID or error
        """
        url = f"https://api.cloudflare.com/client/v4/zones"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        params = {
            "name": f"{zone_name}",
            "status": "active",
            "account": {
                "id": os.getenv("CLOUDFLARE_ACCOUNT_ID")
            }
        }
        
        self.log.info(f"Fetching zone ID for {zone_name}")
        result = await self._http_get(url, headers=headers, params=params)
        if result["success"]:
            print(result['data'])
            if result["data"]["result_info"]["total_count"] > 0:
                if result["data"]["result_info"]["total_count"] > 1:
                    self.log.warning(f"Multiple zones found for {zone_name}.")
                    max_length = 0
                    longest_zone_name_check = []
                    longest_zone_id = None  # Variable to store the zone_id of the longest zone_name_check
                    for zone in result["data"]["result"]:
                        zone_name = zone["name"]
                        zone_id = zone["id"]
                        zone_name_check = zone_name.split('.')
                        length_zone_name = len(zone_name_check)
                        self.log.info(f"Zone name: {zone_name}, Split length: {length_zone_name}")
                        if length_zone_name > max_length:
                            max_length = length_zone_name
                            longest_zone_name_check = zone_name_check
                            longest_zone_id = zone_id  # Update the zone_id for the longest zone_name_check
                    self.log.info(f"Longest split list: {longest_zone_name_check} with length {max_length}")
                    self.log.info(f"Zone ID for the longest zone: {longest_zone_id}")
                    zone_name = longest_zone_name_check
                    self.zone_id = longest_zone_id
                else:
                    zone_name = result["data"]["result"][0]["name"]
                    self.zone_id = result["data"]["result"][0]["id"]
                    longest_zone_id = self.zone_id
                self.log.info(f"Zone ID for {zone_name} is {self.zone_id}")
                return {
                    "success": True,
                    "status": result["status"],
                    "zone_id": self.zone_id,
                    "longest_zone_id": longest_zone_id,  # Include the longest zone_id in the response
                }
            self.log.warning(f"No zones found for {zone_name}")
        return {
            "success": False,
            "status": result["status"],
            "error": f"No zones found for {zone_name}",
        }

    async def purge_cache(self, hosts: List[str]) -> Dict[str, Union[bool, int, str, Dict]]:
        """
        Purge Cloudflare cache for specified hosts.
        
        :param hosts: List of hosts to purge
        :return: Dictionary with purge operation results
        """

        if hosts[0] == '':
            self.log.warning("Empty hosts list provided for cache purge")
            return {
                "success": False,
                "error": "No hosts provided for cache purge",
            }
        
        for host in hosts:
            zone_filter = host.split('.')
            if len(zone_filter) > 3:
                zone_filter = zone_filter[1:]
            else:
                zone_filter = zone_filter
            zone_filter = '.'.join(zone_filter)    
            result = await self.get_zone_id(zone_filter)
            print(result)
            if result["success"]:
                self.log.info(f"Zone ID for {zone_filter} is {result['zone_id']}")
                self.apps.append(
                    {
                        "zone_id": result["zone_id"],
                        "host": host
                    }
                )
            else:
                self.log.error(f"Failed to get zone ID for {zone_filter}: {result['error']}")
                return {
                    "success": False,
                    "error": f"Failed to get zone ID for {zone_filter}: {result['error']}",
                }
        self.log.info(f"Purging cache for hosts: {', '.join(hosts)}")

        if len(self.apps) == 0:
            self.log.warning("No valid zone IDs found for cache purge")
            return {
                "success": False,
                "error": "No valid zone IDs found for cache purge",
            }
        if len(self.apps) > 0:
            return {
                "success": True,
                "message": f"Multiple zone IDs found for the provided hosts: {', '.join(hosts)}. Please specify a single host."
            }
            for app in self.apps:
                self.log.info(f"Zone ID: {app['zone_id']}, Host: {app['host']}")
                url = f"https://api.cloudflare.com/client/v4/zones/{app['zone_id']}/purge_cache"
                headers = {
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                }
                payload = {"hosts": [app["host"]]}
                result = await self._http_post(url, headers=headers, payload=payload)
                if result["success"]:
                    self.log.info(f"Cache purged successfully for {app['host']}")
                    return {
                        "success": True,
                        "message": f"Cache purged successfully for {app['host']}",
                    }
                else:
                    self.log.error(f"Failed to purge cache for {app['host']}: {result['error']}")
                    return {
                        "success": False,
                        "error": f"Failed to purge cache for {app['host']}: {result['error']}",
                    }