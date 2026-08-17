import os
from dotenv import load_dotenv

load_dotenv()

# ==== Telegram Bot Settings ====
BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")

# Comma separated list of admin Telegram user IDs, e.g. "123456789,987654321"
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

# ==== Mandatory Join Gate ====
# Users must join this channel before they can use the bot at all.
# Must be the @username of a channel where the bot is an admin. Leave empty to disable.
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "@officialZORVAKChannel")
REQUIRED_CHANNEL_DISPLAY = os.getenv(
    "REQUIRED_CHANNEL_DISPLAY",
    "https://t.me/officialZORVAKChannel"
)

# ==== Economy Settings ====
# How many points = 1 USDT
POINTS_PER_USDT = int(os.getenv("POINTS_PER_USDT", "1000"))

# Minimum withdrawal amount in USDT
MIN_WITHDRAW_USDT = float(os.getenv("MIN_WITHDRAW_USDT", "5"))

# Points awarded per task type (you can change these anytime)
POINTS_DAILY_BONUS = int(os.getenv("POINTS_DAILY_BONUS", "20"))
POINTS_JOIN_CHANNEL = int(os.getenv("POINTS_JOIN_CHANNEL", "50"))
POINTS_REFERRAL = int(os.getenv("POINTS_REFERRAL", "100"))
POINTS_AD_VIEW = int(os.getenv("POINTS_AD_VIEW", "200"))

# Seconds between ad views (anti-spam)
AD_VIEW_COOLDOWN_SECONDS = 60

# ==== AdsGram Integration ====
ADSGRAM_TOKEN = os.getenv(
    "ADSGRAM_TOKEN",
    "f5e051b500fc4e82a0d62dcb1ce56ebb"
)
ADSGRAM_BLOCK_ID = os.getenv("ADSGRAM_BLOCK_ID", "43200")

# ==== Support Contact ====
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@OfficialZORVAK")

# Database file
DB_PATH = os.getenv("DB_PATH", "earnbot.db")
