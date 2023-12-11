import string,random

def generateRandomString(length=10):
    """生成随机10字节长度的字符串，为什么主键不用自增？？？？？？？？？？？？？？？？？？ 脱裤子放屁 脑残"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))


print(generateRandomString())