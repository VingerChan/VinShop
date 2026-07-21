import base64
from PIL import Image,ImageDraw,ImageFont
import random
from io import BytesIO
# 字符集：排除掉 O I 0 1
CHAR_SET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
# 系统可用字体路径
FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def random_color(min_v:int=0, max_v:int=255) -> tuple:
    """
    生成随机RGB颜色
    :param min_v: 通道最小值
    :param max_v: 通道最大值
    :return: (R,G,B)元组
    """
    return (random.randint(min_v, max_v), random.randint(min_v, max_v), random.randint(min_v, max_v))

def generate_captcha() -> tuple[str,bytes]:
    """
    生成图形验证码
    :return: (验证码文本，PNG图片二进制数据)
    """
    # 1.随机选取4个字符组成验证码文本
    code = ''.join(random.choices(CHAR_SET, k=4))
    # 2.创建浅色背景画布(宽120px，高40px)
    img = Image.new('RGB',(120,40),random_color(160,255))
    # 3.创建绘图对象
    draw = ImageDraw.Draw(img)
    # 4.加载字体(字号36,比画布高度略小，可以留出上下边距)
    font = ImageFont.truetype(FONT_PATH, size=36)
    # ── 逐个绘制字符，每个字符带随机偏移 ──
    for i, ch in enumerate(code):
        # 每个字符横向间隔约 28px，再加上 ±3px 随机偏移
        x = 5 + i * 28 + random.randint(-3, 3)
        # 纵向随机偏移 -2 ~ 5px
        y = random.randint(-2, 5)
        # 用深色（0~80）绘制字符，与浅色背景形成对比
        draw.text((x, y), ch, font=font, fill=random_color(0, 80))

    # ── 添加 2~3 条随机干扰线 ──
    for _ in range(random.randint(2, 3)):
        x1 = random.randint(0, 120)
        y1 = random.randint(0, 40)
        x2 = random.randint(0, 120)
        y2 = random.randint(0, 40)
        draw.line((x1, y1, x2, y2), fill=random_color(100, 200), width=2)

    # ── 添加 60~100 个随机噪点 ──
    for _ in range(random.randint(60, 100)):
        draw.point(
            (random.randint(0, 120), random.randint(0, 40)),
            fill=random_color(0, 255)
        )

    # ── 将图片写入内存字节流 ──
    buf = BytesIO()
    img.save(buf, 'PNG')
    # 取回字节数据
    image_bytes = buf.getvalue()

    return code, image_bytes

def generate_captcha_base64() -> tuple[str, str]:
    """
    生成带 base64 编码的图形验证码（给 CaptchaView 直接用）
    :return: (验证码文本, base64 图片字符串)
    """
    code, image_bytes = generate_captcha()
    b64_str = base64.b64encode(image_bytes).decode()
    return code, b64_str