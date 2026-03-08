import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_USERNAME = "Download12erBot"
DOWNLOAD_PATH = 'downloads'
MAX_FILE_SIZE = 500 * 1024 * 1024

SUPPORTED_SITES = {
    'youtube.com': 'YouTube', 'youtu.be': 'YouTube',
    'tiktok.com': 'TikTok', 'vt.tiktok.com': 'TikTok'
}