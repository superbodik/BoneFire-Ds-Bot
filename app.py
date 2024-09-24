import disnake
from disnake.ext import commands
import logging
import config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

intents = disnake.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    for guild in bot.guilds:
        print(f'Connected to server: {guild.name} (ID: {guild.id})')

@bot.event
async def on_command_error(ctx, error):
    logger.error(f"An error occurred: {error}")

@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"An error occurred in event {event}: {args} {kwargs}", exc_info=True)

# Загрузка Cogs
cogs = ["cogs.user_interactions"]

for cog in cogs:
    try:
        bot.load_extension(cog)
        logger.info(f"Cog {cog} loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load cog {cog}: {e}")

bot.sent_messages = {}
bot.sent_confirmations = {}
bot.sent_reviews = {}

bot.run(config.BOT_TOKEN)
