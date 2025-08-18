from random import choice, randint

def getResponse(userInput: str) -> str:
    loweredInput: str = userInput.lower()

    if 'hello' in loweredInput:
        return 'Hello, User!'