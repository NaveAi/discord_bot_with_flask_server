import os
import logging
import discord
import cohere
from threading import Thread
import asyncio

# הגדרת הלוגר
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# הגדרת ה-DiscordBot
class DiscordBot:
    def __init__(self):
        self.DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
        self.COHERE_API = os.environ.get("COHERE_API")
        self.PREAMBLE = os.environ.get("PREAMBLE", " ")
        self.TEMPERATURE = float(os.environ.get("TEMPERATURE", 0.7))

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        self.client = discord.Client(intents=intents)
        self.co = cohere.Client(self.COHERE_API)
        self.setup_bot()

    def setup_bot(self):
        @self.client.event
        async def on_ready():
            logger.info(f'הבוט {self.client.user} מחובר בהצלחה!')
            logger.info(f'מחובר ל-{len(self.client.guilds)} שרתים')
            for guild in self.client.guilds:
                logger.info(f'מחובר לשרת: {guild.name} (id: {guild.id})')
            global bot_is_ready
            bot_is_ready = True

        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return
            await self.handle_message(message)

    async def handle_message(self, message):
        if self.client.user in message.mentions or message.reference and message.reference.resolved.author == self.client.user:
            await self.respond_to_mention(message)
        elif message.content.startswith('!hello'):
            await message.channel.send('שלום!')

    async def respond_to_mention(self, message):
        content = message.content
        try:
            chat_history = []
            async for msg in message.channel.history(limit=10):
                role = "USER" if msg.author != self.client.user else "CHATBOT"
                chat_history.append({"role": role, "text": msg.content})
            
            chat_history.reverse()
            
            response = self.co.chat(
                model="command-r-plus",
                message=content,
                chat_history=chat_history,
                preamble=self.PREAMBLE,
                temperature=self.TEMPERATURE
            )
            await message.channel.send(response.text)
        except Exception as e:
            logger.error(f'שגיאה: {e}')
            await message.channel.send("אירעה שגיאה. נסה שוב מאוחר יותר.")

    def run(self):
        logger.info('מתחיל להריץ את הבוט...')
        try:
            self.client.run(self.DISCORD_TOKEN)
        except Exception as e:
            logger.error(f'שגיאה בהרצת הבוט: {e}')

# משתנים גלובליים לסימון מצב הבוט
bot_is_ready = False
bot_thread = None

# פונקציה להרצת הבוט ב-Thread
def run_bot():
    global bot_is_ready, bot_thread
    logger.info('מתחיל את פונקציית run_bot...')
    bot = DiscordBot()
    bot.run()

# הגדרת WSGI application
def application(environ, start_response):
    global bot_is_ready, bot_thread
    status = '200 OK'
    
    if bot_thread is None:
        logger.info('מתחיל את ה-Thread של הבוט...')
        bot_thread = Thread(target=run_bot)
        bot_thread.start()
        output = 'הבוט מתחיל...'.encode('utf-8')
    elif bot_is_ready:
        output = 'הבוט פועל ומחובר!'.encode('utf-8')
    else:
        output = 'הבוט עדיין מתחבר...'.encode('utf-8')
    
    response_headers = [('Content-type', 'text/plain; charset=utf-8'), ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]

if __name__ == "__main__":
    logger.info('הרצת הסקריפט באופן ישיר.')
    run_bot()