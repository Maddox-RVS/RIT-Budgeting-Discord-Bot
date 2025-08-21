from discord.app_commands import CommandTree
from discord import Intents, Client, Message
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional
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

        if parsedDate.date() <= datetime.now().date():
            await interaction.response.send_message("The budget end date must be in the future!", ephemeral=True)
            return

        backend.setupBudget(userID, starting_dining_dollars, starting_tiger_bucks, starting_us_dollars, parsedDate)
        await interaction.response.send_message(f'Setup complete! Your budget will end on {parsedDate.strftime('%A, %B %d, %Y')}.\n\nYour current balance: {backend.getUserBalance(userID)}', ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Invalid date format! Use YYYY-MM-DD.", ephemeral=True)
        return
    
@tree.command(name='report', description='Reports your current balance and daily budget.')
async def reportCmd(interaction: discord.Interaction) -> None:
    userID: str = str(interaction.user.id)

    if not backend.isBudgetSetup(userID):
        await interaction.response.send_message("You need to set up your budget first using /setup.", ephemeral=True)
        return

    report: str = backend.getUserBudgetReport(userID)

    await interaction.response.send_message(report, ephemeral=True)   

@tree.command(name='transactions', description='Shows the user\'s transactions.')
async def transactionsCmd(interaction: discord.Interaction, date_start_range: Optional[str] = None, date_end_range: Optional[str] = None) -> None:
    userID: str = str(interaction.user.id)

    if not backend.isBudgetSetup(userID):
        await interaction.response.send_message("You need to set up your budget first using /setup.", ephemeral=True)
        return
    
    if (date_start_range is None) != (date_end_range is None):
        await interaction.response.send_message("Please provide both date ranges (start and end).", ephemeral=True)
        return

    try:
        parsedStartDate: Optional[datetime] = datetime.strptime(date_start_range, "%Y-%m-%d") if date_start_range else None
        parsedEndDate: Optional[datetime] = datetime.strptime(date_end_range, "%Y-%m-%d") if date_end_range else None

        transactions: str = backend.getUserTransactionHistory(userID, parsedStartDate, parsedEndDate)
        await interaction.response.send_message(transactions, ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Invalid date format! Use YYYY-MM-DD.", ephemeral=True)
        return

@tree.command(name='spent', description='Records an expense for the user.')
async def spentCmd(interaction: discord.Interaction, amount: float, description: str) -> None:
    userID: str = str(interaction.user.id)

    if not backend.isBudgetSetup(userID):
        await interaction.response.send_message("You need to set up your budget first using /setup.", ephemeral=True)
        return
    
    await interaction.response.send_message(
        f'Choose which money type to apply the transaction to:',
        view=backend.BudgetTypeSelectorView(userID, amount, description, spending=True),
        ephemeral=True)
    
@tree.command(name='add', description='Adds money to the user\'s budget.')
async def addCmd(interaction: discord.Interaction, amount: float, description: str) -> None:
    userID: str = str(interaction.user.id)

    if not backend.isBudgetSetup(userID):
        await interaction.response.send_message("You need to set up your budget first using /setup.", ephemeral=True)
        return
    
    await interaction.response.send_message(
        f'Choose which money type to apply the transaction to:',
        view=backend.BudgetTypeSelectorView(userID, amount, description, spending=False),
        ephemeral=True)
    
@tree.command(name='respread', description='Respreads the user\'s remaining budget over the remaining days.')
async def respreadCmd(interaction: discord.Interaction) -> None:
    userID: str = str(interaction.user.id)

    if not backend.isBudgetSetup(userID):
        await interaction.response.send_message("You need to set up your budget first using /setup.", ephemeral=True)
        return

    backend.respreadUserBudget(userID)
    dailyBudget = backend.getUserDailyBudget(userID)
    await interaction.response.send_message(
        f"Your remaining budget has been respread over the remaining days.\nYour daily budget is now ${dailyBudget:.2f}.",
        ephemeral=True)
    
@tree.command(name='set-budget-end-date', description='Sets the end date for the user\'s budget.')
async def setBudgetEndDateCmd(interaction: discord.Interaction, budget_end_date: str) -> None:
    userID: str = str(interaction.user.id)

    if not backend.isBudgetSetup(userID):
        await interaction.response.send_message("You need to set up your budget first using /setup.", ephemeral=True)
        return

    try:
        parsedDate: datetime = datetime.strptime(budget_end_date, "%Y-%m-%d")

        if parsedDate.date() <= datetime.now().date():
            await interaction.response.send_message("The budget end date must be in the future!", ephemeral=True)
            return

        backend.setUserBudgetEndDate(userID, parsedDate)
        await interaction.response.send_message(f'Your budget end date has been set to {parsedDate.strftime("%A, %B %d, %Y")}.', ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Invalid date format! Use YYYY-MM-DD.", ephemeral=True)
        return

@client.event
async def on_ready() -> None:
    await tree.sync()
    print(f'{client.user} is now running!')

def main() -> None:
    client.run(DISCORD_TOKEN)

if __name__ == '__main__':
    main()