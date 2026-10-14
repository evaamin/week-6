import os

import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


# small client for the Genius API
class Genius:

    BASE_URL = "https://api.genius.com"

    # use the given token, or fall back to ACCESS_TOKEN from .env
    def __init__(self, access_token=None):
        self.access_token = access_token or os.environ.get("ACCESS_TOKEN")

    # send a GET request to an API path and return the JSON response
    def _get(self, path, params=None):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(self.BASE_URL + path,
                                params=params,
                                headers=headers,
                                timeout=10)
        response.raise_for_status()
        return response.json()

    # return the list of search hits for a term
    def search(self, search_term, per_page=15):
        json_data = self._get("/search",
                              params={"q": search_term, "per_page": per_page})
        return json_data["response"]["hits"]

    # primary artist ID from the first hit, or None if no hits
    def get_artist_id(self, search_term):
        hits = self.search(search_term, per_page=1)
        if not hits:
            return None
        return hits[0]["result"]["primary_artist"]["id"]

    # artist JSON for a Genius artist ID
    def get_artist_by_id(self, artist_id):
        return self._get(f"/artists/{artist_id}")

    # artist JSON for the most likely artist of a search term ({} if none)
    def get_artist(self, search_term):
        artist_id = self.get_artist_id(search_term)
        if artist_id is None:
            return {}
        return self.get_artist_by_id(artist_id)

    # build one df row from an artist JSON object
    @staticmethod
    def _artist_row(search_term, artist_json):
        artist = artist_json.get("response", {}).get("artist", {})
        return {
            "search_term": search_term,
            "artist_name": artist.get("name"),
            "artist_id": artist.get("id"),
            "followers_count": artist.get("followers_count"),
        }

    # df with one row of artist info per search term
    def get_artists(self, search_terms):
        rows = [self._artist_row(term, self.get_artist(term))
                for term in search_terms]
        return pd.DataFrame(rows,
                            columns=["search_term", "artist_name",
                                     "artist_id", "followers_count"])
