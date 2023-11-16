import os
import discord
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv
import json
from datetime import datetime
from openai import OpenAI

load_dotenv(find_dotenv())

LOG_FILE_PATH = os.getenv("LOG_FILE_PATH")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Initializing OpenAI client
INSTRUCTION = os.getenv("INSTRUCTION")

CONVERSATION_HISTORY_FILE = os.getenv("CONVERSATION_HISTORY_FILE", "conversation_history.json")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

try:
    with open(CONVERSATION_HISTORY_FILE, "r") as file:
        conversation_history = json.load(file)
except FileNotFoundError:
    conversation_history = []

previous_question = ""

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    
    emoji = "🤖"
    if reaction.emoji == emoji:
        try:
            await reaction.message.delete()
        except discord.NotFound:
            pass

@bot.command()
async def bob(ctx, *, question):
    global conversation_history
    global previous_question

    print(f"Received command: !bob {question}")
    system_message = f'{ctx.author.name} asks "{question}"'

    last_two_messages = conversation_history[-2:]
    user_messages = [{"role": "user", "content": msg.get("question", "")} for msg in last_two_messages]

    user_messages.append({"role": "user", "content": f"{system_message}\n{question}"})

    messages = [
        {"role": "system", "content": INSTRUCTION},
        {"role": "user", "content": f"{system_message}\n{question}"}
    ]

    for msg in last_two_messages:
        messages.append({
            "role": "user",
            "content": msg.get("content", "")
        })

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=1.0,
            max_tokens=250,
        )

        print("API Response Content:", response.choices[0].message.content)  # Add this line to print only the content

        response_content = response.choices[0].message.content
        if response_content:
            command_message = await ctx.send(response_content)
            await command_message.add_reaction("🤖")
            await ctx.message.add_reaction("🤖")

            conversation_history.append({
                "author": ctx.author.name,
                "question": f"{system_message}\n{question}",
                "response_content": response_content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

            previous_question = question

            with open(CONVERSATION_HISTORY_FILE, "w") as file:
                json.dump(conversation_history[-2:], file)

            log_conversation(ctx.author.name, question, response_content)
        else:
            await ctx.send("I'm sorry, I couldn't generate a response at the moment.")
    except Exception as e:
        await ctx.send(f"An error occurred while processing your request: {e}")



@bot.command()
async def last_question(ctx):
    global previous_question

    if previous_question:
        await ctx.send(f"The last question you asked me was: {previous_question}")
    else:
        await ctx.send("I don't recall any previous questions.")

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

run_bot()