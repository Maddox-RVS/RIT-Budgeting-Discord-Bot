from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from typing import Final
from enum import Enum
import pickle
import atexit
import os

USER_DATA_SAVE_FILE: Final[str] = 'user_data.pkl'

class BudgetType(Enum):
    DINING_DOLLARS = 'diningDollars'
    TIGER_BUCKS = 'tigerBucks'
    USD = 'USD'

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
    budgetFloor: float = 0.0

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

def getUserBalance(userID: str) -> float:
    data: UserData = userData[userID]
    return data.diningDollars + data.tigerBucks + data.USD

def addUserBalance(userID: str, amount: float, budgetType: BudgetType) -> None:
    data: UserData = userData[userID]
    
    if budgetType == BudgetType.DINING_DOLLARS: data.diningDollars += amount
    elif budgetType == BudgetType.TIGER_BUCKS: data.tigerBucks += amount
    elif budgetType == BudgetType.USD: data.USD += amount

    userData[userID] = data

def subtractUserDiningDollars(userID: str, amount: float, budgetType: BudgetType) -> None:
    data: UserData = userData[userID]
    
    if budgetType == BudgetType.DINING_DOLLARS: data.diningDollars -= amount
    elif budgetType == BudgetType.TIGER_BUCKS: data.tigerBucks -= amount
    elif budgetType == BudgetType.USD: data.USD -= amount

    userData[userID] = data

def setUserBalance(userID: str, amount: float, budgetType: BudgetType) -> None:
    data: UserData = userData[userID]

    if budgetType == BudgetType.DINING_DOLLARS: data.diningDollars = amount
    elif budgetType == BudgetType.TIGER_BUCKS: data.tigerBucks = amount
    elif budgetType == BudgetType.USD: data.USD = amount

    userData[userID] = data

def getUserBudgetSpread(userID: str) -> float:
    data: UserData = userData[userID]
    budgetingDate: datetime = data.budgetDate
    today: datetime = datetime.now()
    daysInBudget: int = (today - budgetingDate).days

    return getUserBalance(userID) / daysInBudget if daysInBudget > 0 else 0.0

def setupBudget(userID: str, 
                startingDiningDollars: float, 
                startingTigerBucks: float, 
                startingUSD: float, 
                budgetDate: datetime) -> None:

    today: datetime = datetime.now()
    daysInBudget: int = (today - budgetDate).days
    userBudgetSpread: float = (startingDiningDollars + startingTigerBucks + startingUSD) / daysInBudget if daysInBudget > 0 else 0.0

    userData[userID] = UserData(startingDiningDollars=startingDiningDollars,
                                startingTigerBucks=startingTigerBucks,
                                startingUSD=startingUSD,
                                diningDollars=startingDiningDollars,
                                tigerBucks=startingTigerBucks,
                                USD=startingUSD, 
                                budgetDate=budgetDate,
                                dailyBudget=userBudgetSpread,
                                budgetFloor=userBudgetSpread)
    
def setUserDailyBudgetFloor(userID: str, floor: float) -> bool:
    if floor < 0: return False

    data: UserData = userData[userID]
    data.budgetFloor = floor
    userData[userID] = data

    return True

def getUserDailyBudget(userID: str) -> float:
    data: UserData = userData[userID]
    return data.dailyBudget

def respreadUserBudget(userID: str) -> None:
    userBudgetSpread: float = getUserBudgetSpread(userID)
    data: UserData = userData[userID]

    if userBudgetSpread >= data.budgetFloor:
        data.dailyBudget = userBudgetSpread

intialize()
atexit.register(saveUserData)