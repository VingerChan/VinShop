import string
import random
def generate_default_nickname():
    # random.choices从给定序列中随机取k个字符，例如vin_847362qaz
    digits = ''.join(random.choices(string.digits, k=6))
    letters = ''.join(random.choices(string.ascii_lowercase, k=3))
    return f"vin_{digits}{letters}"