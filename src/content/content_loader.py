import requests
from requests.adapters import HTTPAdapter, Retry

from ..localization.localization import Localizer
from ..utilities.logging import Logger

class Loader:

    CONTENT_LOAD_TIMEOUT = 5 # Seconds
    RETRY_STRATEGY = Retry(total=5, backoff_factor=1) # 5 max retries

    @staticmethod
    def fetch(session, endpoint="/"):
        data = session.get(f"https://valorant-api.com/v1{endpoint}?language=all", timeout=Loader.CONTENT_LOAD_TIMEOUT)
        return data.json()

    @staticmethod
    def load_all_content(client):
        Logger.debug("Calling VALORANT API to load game content in memory...")

        session = requests.Session()
        session.mount("https://", HTTPAdapter(max_retries=Loader.RETRY_STRATEGY))

        content_data = {
            "agents": [],
            "maps": [],
            "modes": [],
            "comp_tiers": [],
            "season": {},
            "queue_aliases": { #i'm so sad these have to be hardcoded but oh well :(
                "newmap": "New Map",
                "competitive": "Competitive",
                "unrated": "Unrated",
                "spikerush": "Spike Rush",
                "deathmatch": "Deathmatch",
                "ggteam": "Escalation",
                "onefa": "Replication",
                "custom": "Custom",
                "snowball": "Snowball Fight",
                "": "Custom",
            },
            "team_aliases": {
                "TeamOne": "Defender",
                "TeamTwo": "Attacker",
                "TeamSpectate": "Observer",
                "TeamOneCoaches": "Defender Coach",
                "TeamTwoCoaches": "Attacker Coach",
            },
            "team_image_aliases": {
                "TeamOne": "team_defender",
                "TeamTwo": "team_attacker",
                "Red": "team_defender",
                "Blue": "team_attacker",
            },
            "modes_with_icons": ["ggteam","onefa","snowball","spikerush","unrated","deathmatch"]
        }
        all_content = client.fetch_content()
        agents = Loader.fetch(session, "/agents")["data"]
        maps = Loader.fetch(session, "/maps")["data"]
        modes = Loader.fetch(session, "/gamemodes")["data"]
        comp_tiers = Loader.fetch(session, "/competitivetiers")["data"][-1]["tiers"]

        for season in all_content["Seasons"]:
            if season["IsActive"] and season["Type"] == "act":
                content_data["season"] = {
                    "competitive_uuid": season["ID"],
                    "season_uuid": season["ID"],
                    "display_name": season["Name"]
                }

        for agent in agents:
            content_data["agents"].append({
                "uuid": agent["uuid"],
                "display_name": agent["displayName"]["en-US"],
                "display_name_localized": agent["displayName"][Localizer.locale],
                "internal_name": agent["developerName"]
            })

        for game_map in maps:
            content_data["maps"].append({
                "uuid": game_map["uuid"],
                "display_name": game_map["displayName"]["en-US"],
                "display_name_localized": game_map["displayName"][Localizer.locale],
                "path": game_map["mapUrl"],
                "internal_name": game_map["mapUrl"].split("/")[-1]
            })

        for mode in modes:
            content_data["modes"].append({
                "uuid": mode["uuid"],
                "display_name": mode["displayName"]["en-US"],
                "display_name_localized": mode["displayName"][Localizer.locale],
            })

        for tier in comp_tiers:
            content_data["comp_tiers"].append({
                "display_name": tier["tierName"]["en-US"],
                "display_name_localized": tier["tierName"][Localizer.locale],
                "id": tier["tier"],
            })

        Logger.debug("Done loading game content.")

        return content_data