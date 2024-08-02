import json
from typing import Dict, List, Optional

import aiohttp
import requests
from langchain_core.pydantic_v1 import BaseModel, Extra, SecretStr, root_validator
from langchain_core.utils import get_from_dict_or_env

DABOM_API_URL = "https://api.dabomai.com"


class DabomSearchAPIWrapper(BaseModel):
    """Wrapper for Tavily Search API."""

    dabom_api_key: SecretStr

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    @root_validator(pre=True)
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and endpoint exists in environment."""
        dabom_api_key = get_from_dict_or_env(
            values, "dabom_api_key", "DABOM_API_KEY"
        )
        values["dabom_api_key"] = dabom_api_key
        return values

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.dabom_api_key.get_secret_value()}",
            "Content-Type": "application/json"
        }

    def raw_results(
        self,
        query: str,
        max_results: Optional[int] = 5,

    ) -> Dict:
        params = {
            "query": query,
            "max_results": max_results,

        }
        response = requests.post(
            # type: ignore
            f"{DABOM_API_URL}/search",
            json=params,
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    def results(
        self,
        query: str,
        max_results: Optional[int] = 5,
 
    ) -> List[Dict]:
        """Run query through Dabom Search and return metadata.

        Args:
            query: The query to search for.
            max_results: The maximum number of results to return.

        Returns:
            query: The query that was searched for.
            response_time: The response time of the query.
            results: A list of dictionaries containing the results:
                title: The title of the result.
                url: The url of the result.
                content: The content of the result.
                score: The score of the result.
        """
        raw_search_results = self.raw_results(
            query,
            max_results=max_results,

        )
        return self.clean_results(raw_search_results["results"])

    async def raw_results_async(
        self,
        query: str,
        max_results: Optional[int] = 5,

    ) -> Dict:
        """Get results from the Dabom Search API asynchronously."""

        # Function to perform the API call
        async def fetch() -> str:
            params = {
                "api_key": self.dabom_api_key.get_secret_value(),
                "query": query,
                "max_results": max_results,
            }
            async with aiohttp.ClientSession(headers=self._get_headers()) as session:
                async with session.post(f"{DABOM_API_URL}/search", json=params) as res:
                    if res.status == 200:
                        data = await res.text()
                        return data
                    else:
                        raise Exception(f"Error {res.status}: {res.reason}")

        results_json_str = await fetch()
        return json.loads(results_json_str)

    async def results_async(
        self,
        query: str,
        max_results: Optional[int] = 5,

    ) -> List[Dict]:
        results_json = await self.raw_results_async(
            query=query,
            max_results=max_results,
        )
        return self.clean_results(results_json["results"])

    def clean_results(self, results: List[Dict]) -> List[Dict]:
        """Clean results from Tavily Search API."""
        clean_results = []
        for result in results:
            clean_results.append(
                {
                    "url": result["url"],
                    "content": result["content"],
                }
            )
        return clean_results
