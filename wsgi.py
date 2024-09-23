import os
import logging
import discord
import cohere
from threading import Thread

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
        intents.presences = True
        
        self.client = discord.Client(intents=intents)
        self.co = cohere.Client(self.COHERE_API)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.setup_bot()

    def setup_bot(self):
        @self.client.event
        async def on_ready():
            logging.info(f'הבוט {self.client.user} מחובר בהצלחה!')

        @self.client.event
        async def on_message(message):
            await self.handle_message(message)

    async def handle_message(self, message):
        logging.info(f'קיבלתי הודעה מ-{message.author}: {message.content}')
        if message.author == self.client.user:
            return
        if message.reference or self.client.user in message.mentions:
            await self.respond_to_mention(message)
        else:
            await self.handle_command(message)

    async def respond_to_mention(self, message):
        content = message.content
        try:
            logging.info('מתקשר עם Cohere לשליחת הודעה...')
            
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
            logging.info('קיבלתי תגובה מ-Cohere בהצלחה.')
            await message.channel.send(response.text)
        except cohere.CohereAPIError as e:
            logging.error(f'שגיאה ב-API של Cohere: {e}')
            await message.channel.send("שגיאה בתקשורת עם Cohere, נסה שוב מאוחר יותר.")
        except Exception as e:
            logging.error(f'שגיאה כללית: {e}')
            await message.channel.send("אירעה שגיאה פנימית. נסה שוב מאוחר יותר.")

    async def handle_command(self, message):
        if message.content.startswith('!hello'):
            await message.channel.send('שלום!')

    def run(self):
        self.client.run(self.DISCORD_TOKEN)

# פונקציה להרצת הבוט ב-Thread
def run_bot():
    bot = DiscordBot()
    bot.run()

# הגדרת WSGI application
def application(environ, start_response):
    status = '200 OK'
    output = 'הבוט פועל!'.encode('utf-8')  # קידוד ל-UTF-8
    response_headers = [('Content-type', 'text/plain; charset=utf-8'), ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]

# הרצת הבוט ב-Thread
if __name__ == "__main__":
    Thread(target=run_bot).start()
    logging.info('הרצת הבוט ב-Thread התחילה.')