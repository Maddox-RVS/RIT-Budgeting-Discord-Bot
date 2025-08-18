from discord.app_commands import CommandTree
from discord import Intents, Client, Message
from responses import getResponse
from dotenv import load_dotenv
from datetime import datetime
from typing import Final
import discord
import backend
import os

load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

intents: Intents = Intents.default()
intents.message_content = True
client: Client = Client(intents=intents)
tree: CommandTree = CommandTree(client)

# async def sendMessage(message: Message, userMessage: str) -> None:
#     if not userMessage: 
#         print('Message was empty because intents were not enabled properly.')
#         return

#     if isPrivate := userMessage[0] == '?':
#         userMessage = userMessage[1:]
    
#     try:
#         response: str = getResponse(userInput=userMessage)
#         await message.author.send(response) if isPrivate else await message.channel.send(response)
#     except Exception as e:
#         print(f'An error occured: {e}')

@tree.command(name='setup', description='Sets up the bot for the user.')
async def setupCmd(interaction: discord.Interaction, 
                   starting_dining_dollars: float, 
                   starting_tiger_bucks: float, 
                   starting_us_dollars: float, 
                   budget_end_date: str) -> None:
    
    userID: str = str(interaction.user.id)
    if backend.isBudgetSetup(userID):
        await interaction.response.send_message("You have already set up your budget!", ephemeral=True)
        return
    
    try: 
        parsedDate: datetime = datetime.strptime(budget_end_date, "%Y-%m-%d")
        backend.setupBudget(userID, starting_dining_dollars, starting_tiger_bucks, starting_us_dollars, parsedDate)
        await interaction.response.send_message(f'Setup complete! Your budget will end on {parsedDate.strftime("%Y-%m-%d")}.\n\nYour current balance: {backend.getUserBalance(userID)}', ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Invalid date format! Use YYYY-MM-DD.", ephemeral=True)
        return

@client.event
async def on_ready() -> None:
    await tree.sync()
    print(f'{client.user} is now running!')

@client.event
async def on_message(message: Message) -> None:
    # if message.author == client.user: return

    # username: str = str(message.author)
    # userMessage: str = message.content
    # channel: str = str(message.channel)

    # print(f'[{channel}] {username}: {userMessage}')
    # await sendMessage(message=message, userMessage=userMessage)
    pass

def main() -> None:
    client.run(DISCORD_TOKEN)

if __name__ == '__main__':
    main()