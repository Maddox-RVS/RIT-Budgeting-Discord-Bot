from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from typing import Final
from enum import Enum
import discord
import pickle
import atexit
import os

USER_DATA_SAVE_FILE: Final[str] = 'user_data.pkl'

class BudgetType(Enum):
    DINING_DOLLARS = 'diningDollars'
    TIGER_BUCKS = 'tigerBucks'
    USD = 'USD'

    def getPrettyString(self) -> str:
        if self == BudgetType.DINING_DOLLARS: return 'Dining Dollars'
        elif self == BudgetType.TIGER_BUCKS: return 'Tiger Bucks'
        elif self == BudgetType.USD: return 'USD'
        else: return 'Unknown Budget Type'

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value

@dataclass
class UserData:
    startingDiningDollars: float = 0.0
    startingTigerBucks: float = 0.0
    startingUSD: float = 0.0

    diningDollars: float = 0.0
    tigerBucks: float = 0.0
    USD: float = 0.0

    budgetDate: Optional[datetime] = None
    dailyBudget: float = 0.0

    ledger: list[tuple[float, str, datetime]] = field(default_factory=list)
    breaks: list[tuple[datetime, datetime]] = field(default_factory=list)

userData: Optional[dict[str, UserData]] = None

def loadUserData() -> dict[str, UserData]:
    if not os.path.exists(USER_DATA_SAVE_FILE): return {}
    
    with open(USER_DATA_SAVE_FILE, 'rb') as file:
        userData = pickle.load(file)
        return userData
    
def intialize() -> None:
    global userData
    userData = loadUserData()
    
def saveUserData() -> None:
    with open(USER_DATA_SAVE_FILE, 'wb') as file:
        pickle.dump(userData, file)

def isBudgetSetup(userID: str) -> bool:
    return userID in userData and userData[userID].budgetDate is not None

def getDaysInUserBudget(userID: str) -> int:
    if userID not in userData or userData[userID].budgetDate is None:
        return 0
    
    data: UserData = userData[userID]
    
    today: datetime = datetime.now()
    daysInBudget: int = (data.budgetDate - today).days

    for brk in data.breaks:
        breakStart, breakEnd = brk
        if breakStart.date() < today.date() and breakEnd.date() < today.date(): continue
        elif breakStart.date() < today.date(): breakStart = today
        
        breakLength: int = (breakEnd - breakStart).days + 1
        daysInBudget -= breakLength

def getBreaksReport(userID: str) -> str:
    data: UserData = userData[userID]
    
    report: str = (
        f'### Budget Report\n'
        '────────────────────────────────────\n')
    
    for brk in data.breaks:
        breakStart, breakEnd = brk
        report += f'- **Break from `{breakStart.strftime('%A, %B %d, %Y')}` to `{breakEnd.strftime('%A, %B %d, %Y')}`**\n'

    report += '────────────────────────────────────\n'
    return report

def addBreak(userID: str, breakStartTime: datetime, breakEndTime: datetime) -> None:
    data: UserData = userData[userID]

    data.breaks.append((breakStartTime, breakEndTime))

    # TODO: Remove this code below, replace with code that iterates all breaks and resolves any overlap conflicts by merging the breaks
    # for i, brk in enumerate(data.breaks):
    #     exisitingBreakStart, existingEndBreak = brk
    #     if exisitingBreakStart <= breakStartTime <= existingEndBreak or exisitingBreakStart <= breakEndTime <= existingEndBreak:
    #         newBreakStart: datetime = min(exisitingBreakStart, breakStartTime)
    #         newBreakEnd: datetime = max(existingEndBreak, breakEndTime)
    #         data.breaks[i] = (newBreakStart, newBreakEnd)
    #         userData[userID] = data
    #         return

def removeBreak(userID: str, index: int) -> list[tuple[datetime, datetime]]:
    data: UserData = userData[userID]
    
    brks: list[tuple[datetime, datetime]] = data.breaks
    return brks.pop(index)

def getUserNumBreaks(userID: str) -> int:
    data: UserData = userData[userID]
    return len(data.breaks)

def getUserBalance(userID: str) -> float:
    data: UserData = userData[userID]
    return data.diningDollars + data.tigerBucks + data.USD

def addUserBalance(userID: str, amount: float, budgetType: BudgetType) -> None:
    data: UserData = userData[userID]
    
    if budgetType == BudgetType.DINING_DOLLARS: data.diningDollars += amount
    elif budgetType == BudgetType.TIGER_BUCKS: data.tigerBucks += amount
    elif budgetType == BudgetType.USD: data.USD += amount

    userData[userID] = data

def subtractUserBalance(userID: str, amount: float, budgetType: BudgetType) -> None:
    data: UserData = userData[userID]
    
    if budgetType == BudgetType.DINING_DOLLARS: data.diningDollars -= amount
    elif budgetType == BudgetType.TIGER_BUCKS: data.tigerBucks -= amount
    elif budgetType == BudgetType.USD: data.USD -= amount

    userData[userID] = data

def spend(userID: str, amount: float, transactionDescription: str, budgetType: BudgetType) -> None:
    data: UserData = userData[userID]

    data.ledger.append((-amount, transactionDescription, datetime.now()))
    userData[userID] = data

    subtractUserBalance(userID, amount, budgetType)

def add(userID: str, amount: float, transactionDescription: str, budgetType: BudgetType) -> None:
    data: UserData = userData[userID]

    data.ledger.append((amount, transactionDescription, datetime.now()))
    userData[userID] = data

    addUserBalance(userID, amount, budgetType)

def setUserBalance(userID: str, amount: float, budgetType: BudgetType) -> None:
    data: UserData = userData[userID]

    if budgetType == BudgetType.DINING_DOLLARS: data.diningDollars = amount
    elif budgetType == BudgetType.TIGER_BUCKS: data.tigerBucks = amount
    elif budgetType == BudgetType.USD: data.USD = amount

    userData[userID] = data

def getUserBudgetSpread(userID: str) -> float:
    data: UserData = userData[userID]
    daysInBudget: int = getDaysInUserBudget(userID)
    return (getUserBalance(userID) / daysInBudget) if daysInBudget > 0 else 0.0

def setupBudget(userID: str, 
                startingDiningDollars: float, 
                startingTigerBucks: float, 
                startingUSD: float, 
                budgetDate: datetime) -> None:
    
    daysInBudget: int = getDaysInUserBudget(userID)
    userBudgetSpread: float = (startingDiningDollars + startingTigerBucks + startingUSD) / daysInBudget if daysInBudget > 0 else 0.0

    userData[userID] = UserData(startingDiningDollars=startingDiningDollars,
                                startingTigerBucks=startingTigerBucks,
                                startingUSD=startingUSD,
                                diningDollars=startingDiningDollars,
                                tigerBucks=startingTigerBucks,
                                USD=startingUSD, 
                                budgetDate=budgetDate,
                                dailyBudget=userBudgetSpread)

def getUserDailyBudget(userID: str) -> float:
    data: UserData = userData[userID]
    return data.dailyBudget

def respreadUserBudget(userID: str) -> None:
    userBudgetSpread: float = getUserBudgetSpread(userID)
    data: UserData = userData[userID]

    data.dailyBudget = userBudgetSpread
    

def setUserBudgetEndDate(userID: str, budgetEndDate: datetime) -> None:
    data: UserData = userData[userID]
    data.budgetDate = budgetEndDate

    daysInBudget: int = getDaysInUserBudget(userID)
    userBudgetSpread: float = (data.startingDiningDollars + data.startingTigerBucks + data.startingUSD) / daysInBudget if daysInBudget > 0 else 0.0

    data.dailyBudget = userBudgetSpread
    userData[userID] = data

def getUserBudgetReport(userID: str) -> str:
    data: UserData = userData[userID]

    ledger: list[tuple[float, str, datetime]] = data.ledger

    transactions: list[tuple[float, str, datetime]] = []
    for transaction in ledger:
        amount, description, date = transaction
        if date.date() == datetime.now().date():
            transactions.append(transaction)

    moneySpentToday: float = sum([transaction[0] for transaction in transactions if transaction[0] < 0])

    report: str = (
        f'### Budget Report\n'
        '────────────────────────────────────\n'
        f'- **Dining Dollars →** ${data.diningDollars:.2f}\n'
        f'- **Tiger Bucks →** ${data.tigerBucks:.2f}\n'
        f'- **USD →** ${data.USD:.2f}\n'
        '────────────────────────────────────\n'
        f'- **Total Balance →** ${getUserBalance(userID):.2f}\n'
        '────────────────────────────────────\n'
        f'**Transactions Today:** {'None' if not transactions else ''}\n')
    
    for transaction in transactions:
        amount, description, date = transaction
        sign: str = '-' if amount < 0 else '+'
        report += f'- **[{sign}] ${abs(amount):.2f}** on "*{description}*" at `{date.strftime('%I:%M %p')}`\n'

    def format_money(value: float) -> str:
        sign = '-' if value < 0 else ''
        return f'{sign}${abs(value):.2f}'

    report += (
        '────────────────────────────────────\n'
        f'- **Money Spent Today →** {format_money(moneySpentToday)}\n'
        f'- **Money Left Available Today →** {format_money(data.dailyBudget - abs(moneySpentToday))}\n'
        f'- **Daily Budget →** {format_money(data.dailyBudget)}\n'
        f'- **Budget End Date →** {data.budgetDate.strftime('%A, %B %d, %Y')}\n'
        '────────────────────────────────────\n'
    )

    return report

def getUserTransactionHistory(userID: str, searchDateStart: datetime = None, searchDateEnd: datetime = None) -> str:
    data: UserData = userData[userID]
    ledger: list[tuple[float, str, datetime]] = data.ledger

    if not ledger:
        return "No transactions found."

    history: str = "### Transaction History\n────────────────────────────────────\n"
    
    transactionFound: bool = False

    for transaction in ledger:
        if searchDateStart and searchDateEnd and not (transaction[2].date() >= searchDateStart.date() and transaction[2].date() <= searchDateEnd.date()):
            continue

        transactionFound = True

        amount, description, searchDate = transaction
        sign: str = '-' if amount < 0 else '+'
        history += f'- **[{sign}] ${abs(amount):.2f}** on "*{description}*" on `{searchDate.strftime('%A, %B %d, %Y at %I:%M %p')}`\n'

    if not transactionFound:
        history += "No transactions found for the specified date range.\n"

    history += '────────────────────────────────────\n'
    
    return history

class BudgetTypeSelector(discord.ui.Select):
    def __init__(self, userID: str, amount: float, description: str, spending: bool = True) -> None:
        options: list = [
            discord.SelectOption(label='Dining Dollars', value=str(BudgetType.DINING_DOLLARS)),
            discord.SelectOption(label='Tiger Bucks', value=str(BudgetType.TIGER_BUCKS)),
            discord.SelectOption(label='USD', value=str(BudgetType.USD))]
        
        super().__init__(placeholder='Select which type of money you spent...', options=options, min_values=1, max_values=1)

        self.userID: str = userID
        self.amount: float = amount
        self.description: str = description
        self.spending: bool = spending

    async def callback(self, interaction: discord.Interaction) -> None:
        budgetType: BudgetType = BudgetType(self.values[0])

        if self.spending:
            spend(self.userID, self.amount, self.description, budgetType)
            await interaction.response.send_message(f'Spent **${self.amount:.2f}** on "*{self.description}*" using `{budgetType.getPrettyString()}`.', ephemeral=True)
        else:
            add(self.userID, self.amount, self.description, budgetType)
            await interaction.response.send_message(f'Added **${self.amount:.2f}** to your `{budgetType.getPrettyString()}` budget for "*{self.description}*".', ephemeral=True)

class BudgetTypeSelectorView(discord.ui.View):
    def __init__(self, userID: str, amount: float, description: str, spending: bool = True) -> None:
        super().__init__(timeout=60.0)
        self.add_item(BudgetTypeSelector(userID, amount, description, spending))

class BreakRemovalSelector(discord.ui.Select):
    def __init__(self, userID: str) -> None:
        options: list[tuple[datetime, datetime]] = []
        for i, brk in enumerate(userData[userID].breaks):
            breakStart, breakEnd = brk
            options.append(discord.SelectOption(label=f'{breakStart.strftime('%B %d, %Y')} to {breakEnd.strftime('%B %d, %Y')}', value=i))
        
        super().__init__(placeholder='Select a break to remove...', options=options, min_values=1, max_values=1) # dont set max_value to more than 1, the backend's remove break uses .pop(index), popping one index shifts the rest

        self.userID: str = userID

    async def callback(self, interaction: discord.Interaction) -> None:
        index: int = int(self.values[0])
        removedBreak: tuple[datetime, datetime] = removeBreak(self.userID, index)
        await interaction.response.send_message(f'Removed break from `{removedBreak[0].strftime('%A, %B %d, %Y')}` to `{removedBreak[1].strftime('%A, %B %d, %Y')}`.', ephemeral=True)

class BreakRemovalSelectorView(discord.ui.View):
    def __init__(self, userID: str) -> None:
        super().__init__(timeout=60.0)
        self.add_item(BreakRemovalSelector(userID))

intialize()
atexit.register(saveUserData)