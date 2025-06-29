import os
import dotenv

dotenv.load_dotenv()


class Config:
    def __init__(self):
        self.BOT_TG_TOKEN = os.getenv('BOT_TG_TOKEN')
        self.REDIS_HOST = os.getenv('REDIS_HOST')
        self.REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
        self.REDIS_USERNAME = os.getenv('REDIS_USERNAME')
        self.REDIS_PREFIX = os.getenv('REDIS_PREFIX')


config = Config()
