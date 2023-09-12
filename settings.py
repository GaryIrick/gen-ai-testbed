import os


class AppSettings:
    chat_api_endpoint: str
    chat_api_type: str
    chat_api_key: str
    chat_model: str
    embedding_api_endpoint: str
    embedding_api_type: str
    embedding_api_key: str
    embedding_model: str

    def __init__(self):
        self.chat_api_endpoint = os.environ["CHAT_API_ENDPOINT"]
        self.chat_api_type = os.environ["CHAT_API_TYPE"]
        self.chat_api_key = os.environ["CHAT_API_KEY"]
        self.chat_model = os.environ["CHAT_MODEL"]
        self.embedding_api_endpoint = os.environ["EMBEDDING_API_ENDPOINT"]
        self.embedding_api_type = os.environ["EMBEDDING_API_TYPE"]
        self.embedding_api_key = os.environ["EMBEDDING_API_KEY"]
        self.embedding_model = os.environ["EMBEDDING_MODEL"]
