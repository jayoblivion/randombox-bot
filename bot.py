import discord
from discord import app_commands
import random
import json
import os
import time

TOKEN = os.environ.get("TOKEN")
ALLOWED_CHANNEL_IDS = [1481967169746112553, 1482035295338627072]
ADMIN_ROLE_IDS = [1467919008610259198, 1468252935119962152]

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# --- 아이템 구성 ---
TAJJA_ITEMS = [
    {"name": "고니", "emoji": "🧒🏻", "weight": 0.5},
    {"name": "평경장", "emoji": "👴🏼", "weight": 0.875},
    {"name": "아귀", "emoji": "👹", "weight": 0.875},
    {"name": "짝귀", "emoji": "👂", "weight": 0.875},
    {"name": "예림이", "emoji": "💃", "weight": 0.875},
    {"name": "홍단", "emoji": "📜", "weight": 1.5},
    {"name": "매화", "emoji": "🌸", "weight": 1.5},
    {"name": "벚꽃", "emoji": "🌸", "weight": 1.5},
    {"name": "만막", "emoji": "🎑", "weight": 1.5},
    {"name": "붓꽃", "emoji": "🌿", "weight": 1.5},
    {"name": "모란꽃", "emoji": "🌺", "weight": 1.7},
    {"name": "청단", "emoji": "📘", "weight": 1.7},
    {"name": "나비", "emoji": "🦋", "weight": 1.7},
    {"name": "난초", "emoji": "🌱", "weight": 1.7},
    {"name": "국화", "emoji": "🌼", "weight": 1.7},
    {"name": "벚나무", "emoji": "🌳", "weight": 1.7},
    {"name": "송학", "emoji": "🦅", "weight": 1.7},
    {"name": "국준", "emoji": "🍷", "weight": 1.7},
    {"name": "단풍", "emoji": "🍁", "weight": 1.7},
    {"name": "홍싸리", "emoji": "🌿", "weight": 1.7},
    {"name": "개구리", "emoji": "🐸", "weight": 1.7},
    {"name": "멧돼지", "emoji": "🐗", "weight": 1.7},
    {"name": "기러기", "emoji": "🦆", "weight": 1.7},
    {"name": "사슴", "emoji": "🦌", "weight": 1.7},
    {"name": "봉황", "emoji": "🔥", "weight": 1.7},
    {"name": "휘파람새", "emoji": "🐦", "weight": 1.7},
    {"name": "두견새", "emoji": "🐤", "weight": 1.7},
    {"name": "매조", "emoji": "🦜", "weight": 1.7},
    {"name": "학", "emoji": "🦢", "weight": 1.7},
    {"name": "공산", "emoji": "⛰️", "weight": 1.7},
    {"name": "방뚫권(1일)", "emoji": "🔓", "weight": 4.0},
    {"name": "방뚫권(3일)", "emoji": "🔐", "weight": 1.0},
    {"name": "500EXP", "emoji": "💰", "weight": 20.0},
    {"name": "1000EXP", "emoji": "💵", "weight": 18.5},
    {"name": "5000EXP", "emoji": "💳", "weight": 9.0},
    {"name": "한번더", "emoji": "🔄", "weight": 2.0},
]

# --- 조합 레시피 정의 ---
CRAFT_RECIPES = {
    "고니 조합": {
        "ingredients": ["홍단", "매화", "벚꽃", "만막", "붓꽃"],
        "results": ["고니"],
        "emoji": "🎴"
    },
    "상급 조합": {
        "ingredients": [
            ["모란꽃", "청단", "나비", "난초", "국화"],
            ["벚나무", "송학", "국준", "단풍", "홍싸리"],
            ["개구리", "멧돼지", "기러기", "사슴", "봉황"],
            ["휘파람새", "두견새", "매조", "학", "공산"]
        ],
        "results": ["평경장", "아귀", "짝귀", "예림이"],
        "emoji": "💎"
    }
}

BOX_LIST = {
    "타짜상자": {"items": TAJJA_ITEMS, "emoji": "🎴", "color": 0xE74C3C},
}

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def draw_item(items):
    weights = [item["weight"] for item in items]
    return random.choices(items, weights=weights, k=1)[0]

def is_admin(interaction: discord.Interaction) -> bool:
    user_roles = [role.id for role in interaction.user.roles]
    return interaction.user.guild_permissions.administrator or any(r in user_roles for r in ADMIN_ROLE_IDS)

async def check_channel(interaction: discord.Interaction) -> bool:
    if interaction.channel_id not in ALLOWED_CHANNEL_IDS:
        await interaction.response.send_message("❌ 해당 채널에서는 사용할 수 없어요!", ephemeral=True)
        return False
    return True

# --- 박스 선택 뷰 (한번더 로직 포함) ---
class BoxSelectView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=30)
        self.user_id = user_id
        for box_name, box_data in BOX_LIST.items():
            btn = discord.ui.Button(label=f"{box_data['emoji']} {box_name}", style=discord.ButtonStyle.primary)
            btn.callback = self.make_callback(box_name)
            self.add_item(btn)

    def make_callback(self, box_name):
        async def callback(interaction: discord.Interaction):
            if str(interaction.user.id) != self.user_id: return
            
            data = load_data()
            user_id = self.user_id
            box = BOX_LIST[box_name]
            
            # 재추첨 로직 (한번더 당첨 시 반복)
            drawn_items = []
            while True:
                item = draw_item(box["items"])
                drawn_items.append(item)
                if item["name"] != "한번더":
                    break
            
            final_item = drawn_items[-1]
            
            if user_id not in data: data[user_id] = {}
            if "inventory" not in data[user_id]: data[user_id]["inventory"] = {}
            
            inv = data[user_id]["inventory"]
            inv[final_item["name"]] = inv.get(final_item["name"], 0) + 1
            save_data(data)

            desc = ""
            if len(drawn_items) > 1:
                desc = "🔄 **한번더!** 가 당첨되어 다시 뽑았습니다!\n\n"
            desc += f"{final_item['emoji']} **{final_item['name']}** 획득!"

            embed = discord.Embed(title=f"{box['emoji']} {box_name} 결과", description=desc, color=box["color"])
            await interaction.response.edit_message(content="✅ 상자를 오픈했습니다!", view=None)
            await interaction.followup.send(embed=embed)
        return callback

# --- 명령어 구현 ---

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ 봇 온라인: {bot.user}")

@tree.command(name="뽑기", description="타짜 상자를 오픈합니다!")
async def gacha(interaction: discord.Interaction):
    if not await check_channel(interaction): return
    await interaction.response.send_message("🎁 오픈할 상자를 선택하세요!", view=BoxSelectView(str(interaction.user.id)), ephemeral=True)

@tree.command(name="인벤토리", description="내 소지품을 확인합니다.")
async def inventory(interaction: discord.Interaction):
    if not await check_channel(interaction): return
    data = load_data()
    user_id = str(interaction.user.id)
    inv = data.get(user_id, {}).get("inventory", {})
    
    if not inv:
        await interaction.response.send_message("텅 빈 지갑입니다... `/뽑기`를 이용하세요.", ephemeral=True)
        return

    lines = [f"• {name} x{count}" for name, count in inv.items()]
    embed = discord.Embed(title=f"🎒 {interaction.user.display_name}의 가방", description="\n".join(lines), color=0x3498DB)
    await interaction.response.send_message(embed=embed)

@tree.command(name="조합", description="재료를 모아 상위 등급 아이템으로 조합합니다.")
async def craft(interaction: discord.Interaction):
    if not await check_channel(interaction): return
    user_id = str(interaction.user.id)
    data = load_data()
    inv = data.get(user_id, {}).get("inventory", {})

    crafted_something = False
    log = []

    # 1. 고니 조합 체크
    recipe = CRAFT_RECIPES["고니 조합"]
    while all(inv.get(ing, 0) >= 1 for ing in recipe["ingredients"]):
        for ing in recipe["ingredients"]: inv[ing] -= 1
        result = random.choice(recipe["results"])
        inv[result] = inv.get(result, 0) + 1
        log.append(f"✨ **고니** 조합 성공!")
        crafted_something = True

    # 2. 상급 조합 체크
    recipe_upper = CRAFT_RECIPES["상급 조합"]
    for group in recipe_upper["ingredients"]:
        while all(inv.get(ing, 0) >= 1 for ing in group):
            for ing in group: inv[ing] -= 1
            result = random.choice(recipe_upper["results"])
            inv[result] = inv.get(result, 0) + 1
            log.append(f"💎 **{result}** 조합 성공!")
            crafted_something = True

    if crafted_something:
        # 수량이 0이 된 아이템 정리
        data[user_id]["inventory"] = {k: v for k, v in inv.items() if v > 0}
        save_data(data)
        await interaction.response.send_message("\n".join(log))
    else:
        await interaction.response.send_message("❌ 조합 가능한 재료 세트가 부족합니다.", ephemeral=True)

@tree.command(name="확률", description="아이템 당첨 확률을 확인합니다.")
async def show_rates(interaction: discord.Interaction):
    if not await check_channel(interaction): return
    embed = discord.Embed(title="📊 타짜 상자 확률표", color=0x2ECC71)
    for box_name, box_data in BOX_LIST.items():
        total = sum(i["weight"] for i in box_data["items"])
        # 가독성을 위해 상위 아이템 위주로 먼저 표시
        sorted_items = sorted(box_data["items"], key=lambda x: x['weight'])
        lines = [f"{i['emoji']} {i['name']}: **{i['weight']/total*100:.2f}%**" for i in sorted_items]
        embed.description = "\n".join(lines)
    await interaction.response.send_message(embed=embed)

# (관리자 기능은 기존 코드와 동일하므로 생략 가능하나 필요시 유지)
# ... [admin_edit_inventory, admin_clear_inventory 코드] ...

bot.run(TOKEN)