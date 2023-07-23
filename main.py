import os
import discord
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv
import json
from datetime import datetime
import openai
from openai.error import ServiceUnavailableError

# Load environment variables
load_dotenv(find_dotenv())

# Read the log file path from the environment variables
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH")
openai.api_key = os.getenv("OPENAI_API_KEY")
INSTRUCTION = os.getenv("INSTRUCTION")

# Create a bot instance with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@bot.event
async def on_message(message):
    if not message.author.bot:  # Ignore messages sent by bots
        if 'bob' in message.content.lower() and not message.content.startswith('!bob'):
            # await message.add_reaction('🤖')
            await message.channel.send("sup")  # Send "sup" as a reply to the 'bob' keyword

    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    
    emoji = "🤖"
    if reaction.emoji == emoji:
        try:
            # Delete the reacted message sent by the bot
            await reaction.message.delete()
        except discord.NotFound:
            pass  # Message already deleted or not found


@bot.command()
async def bob(ctx, *, question):
    print(f"Received command: !bob {question}")
    system_message = f'{ctx.author.name} asks "{question}"'

    # Include username, instruction, and question in the user message
    messages = [
        {
            "role": "system",
            "content": INSTRUCTION,
        },
        {
            "role": "user",
            "content": f"{system_message}\n{question}",
        },
    ]

    try:
        async with ctx.typing():
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=150,
            )
    except ServiceUnavailableError:
        await ctx.send("I apologize, but I'm currently experiencing high traffic and cannot respond at the moment. Please try again later.")
        return
    except Exception as e:
        await ctx.send(f"An error occurred while processing your request: {e}")
        return

    if response and "choices" in response and len(response["choices"]) > 0:
        response_content = response["choices"][0]["message"]["content"]
        if response_content:
            command_message = await ctx.send(response_content)
            await command_message.add_reaction("🤖")  # Add the 🤖 reaction to the response message
            await ctx.message.add_reaction("🤖")  # Add the 🤖 reaction to the !bob command message

            log_conversation(ctx.author.name, question, response_content)
        else:
            await ctx.send("I'm sorry, I couldn't generate a response at the moment.")
    else:
        print(f"Empty or invalid response from GPT-3.5-turbo model: {response}")
        await ctx.send("I'm sorry, I couldn't generate a response at the moment.")


def log_conversation(author, question, response_content):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_data = {
        "author": author,
        "question": question,
        "response_content": response_content,
        "timestamp": timestamp,
    }
    with open(LOG_FILE_PATH, "a") as log_file:
        log_file.write(json.dumps(log_data) + "\n")


def run_bot():
    bot.run(os.getenv("DISCORD_TOKEN"))


# Run the bot and start the chat session with GPT-3.5-turbo in the same event loop
run_bot()
