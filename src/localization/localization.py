from InquirerPy import inquirer
from InquirerPy.utils import color_print
import valclient

from .locales import Locales
from ..utilities.logging import Logger

class Localizer:

    locale = "en-US"
    config = None

    @staticmethod
    def get_localized_text(*keys):

        def get_default(*keys):
            localized = Locales["en-US"]
            for key in keys:
                localized = localized.get(key)
            return localized

        try:
            localized = Locales[Localizer.locale]
            for key in keys:
                if localized is None:
                    get_default(*keys)
                localized = localized.get(key)
            if localized is not None:
                return localized
        except:
            return get_default(*keys)


    @staticmethod
    def get_config_key(key):
        try:
            for k,value in Locales[Localizer.locale]["config"].items():
                if k == key:
                    return value
            return key
        except:
            return key

    @staticmethod
    def unlocalize_key(key):
        for k,value in Locales[Localizer.locale]["config"].items():
            if value == key:
                return k
        return key

    @staticmethod
    def get_config_value(*keys):
        localized_keys = [Localizer.get_config_key(key) for key in keys]
        result = Localizer.config
        for key in localized_keys:
            result = result[key]
        return result

    @staticmethod
    def set_locale(config):
        for _, data in Locales.items():
            if data != {}:
                for key,value in data["config"].items():
                    if key == "locale" and value in config.keys():
                        Localizer.locale = config[value][0]

    @staticmethod
    def prompt_locale(config):
        if config["locale"][0] == "":
            locale = config["locale"]
            current = locale[0]
            options = locale[1]
            choice = inquirer.select(
                message="Select your locale (language):",
                default=current,
                choices={option:option for option in options},
                pointer=">"
            )
            choice = choice.execute()
            locale[0] = choice

            print() # So the console output looks pretty

    @staticmethod
    def autodetect_region(config):
        # If the region is not specified in the config, try to autodetect it (this happens on first launch)
        if Localizer.get_config_value("region", 0) == "":
            color_print([("Yellow", Localizer.get_localized_text("prints", "startup", "autodetect_region"))])

            Logger.debug("About to initialize NA valclient for autodetecting region...")

            # Default to NA for now
            client = valclient.Client()
            client.activate()

            Logger.debug("Client initialized. Now searching active game sessions for VALORANT...")

            # Find the valorant game session and fetch its region
            sessions = client.riotclient_session_fetch_sessions()
            val_session = next(session for _, session in sessions.items() if session["productId"] == "valorant")
            region = next(arg.split("=", 2)[1] for arg in val_session["launchConfiguration"]["arguments"] if "-ares-deployment" in arg) # The value of the ares-deployment arg is the region

            Logger.debug(f"Found region '{region}' from session {val_session}")

            # Update the passed config to specify the detected region
            config[Localizer.get_config_key("region")][0] = region
            color_print([("LimeGreen", f"{Localizer.get_localized_text('prints', 'startup', 'autodetected_region')} {Localizer.get_config_value('region', 0)}\n")])

            return True
        return False