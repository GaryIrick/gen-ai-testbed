import os


class AppSettings:
    chat_api_endpoint: str
    chat_api_type: str
    chat_api_key: str
    chat_model: str

    search_api_endpoint: str
    search_index: str
    search_api_key: str

    heroes_api_endpoint: str

    def __init__(self):
        self.chat_api_endpoint = os.environ["CHAT_API_ENDPOINT"]
        self.chat_api_type = os.environ["CHAT_API_TYPE"]
        self.chat_api_key = os.environ["CHAT_API_KEY"]
        self.chat_model = os.environ["CHAT_MODEL"]
        self.search_api_endpoint = os.environ["SEARCH_API_ENDPOINT"]
        self.search_api_key = os.environ["SEARCH_API_KEY"]
        self.search_index = os.environ["SEARCH_INDEX"]
        self.heroes_api_endpoint = os.environ["HEROES_API_ENDPOINT"]
