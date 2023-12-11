import string,random

def generateRandomString(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))


print(generateRandomString())
