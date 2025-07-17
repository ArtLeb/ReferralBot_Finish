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
        self.DB_HOST = os.getenv('DB_HOST')
        self.DB_PORT = os.getenv('DB_PORT', '3306')
        self.DB_USERNAME = os.getenv('DB_USERNAME')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD')
        self.DB_NAME = os.getenv('DB_NAME')
        self.OWNER_ID = int(os.getenv('OWNER_ID', 0))
        #self.QR_GENERATION_URL = os.getenv('QR_GENERATION_URL')

config = Config()