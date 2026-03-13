import discord
from discord import app_commands
import random
import json
import os
import time

# --- 설정 및 환경변수 ---
TOKEN = os.environ.get("TOKEN")
ALLOWED_CHANNEL_IDS = [1481967169746112553, 1482035295338627072]
ADMIN_ROLE_IDS = [1467919008610259198, 1468252935119962152]
DATA_FILE = "data.json"
COOLDOWN_SECONDS = 0  # 필요 시 초 단위로 설정

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# --- 1. 아이템 구성 (v4.1 최종본) ---
TAJJA_ITEMS = [
    # S급 완제품
    {"name": "고니", "emoji": "🧒🏻", "weight": 0.5},
    {"name": "평경장", "emoji": "👴🏼", "weight": 0.875},
    {"name": "아귀", "emoji": "👹", "weight": 0.875},
    {"name": "짝귀", "emoji": "👂", "weight": 0.875},
    {"name": "예림이", "emoji": "💃", "weight": 0.875},
    # 2번 고니재료
    {"name": "홍단", "emoji": "📜", "weight": 1.5},
    {"name": "매화", "emoji": "🌸", "weight": 1.5},
    {"name": "벚꽃", "emoji": "🌸", "weight": 1.5},
    {"name": "만막", "emoji": "🎑", "weight": 1.5},
    {"name": "붓꽃", "emoji": "🌿", "weight": 1.5},
    # 3번 평경장재료
    {"name": "모란꽃", "emoji": "🌺", "weight": 1.7},
    {"name": "청단", "emoji": "📘", "weight": 1.7},
    {"name": "나비", "emoji": "🦋", "weight": 1.7},
    {"name": "난초", "emoji": "🌱", "weight": 1.7},
    {"name": "국화", "emoji": "🌼", "weight": 1.7},
    # 4번 아귀재료
    {"name": "벚나무", "emoji": "🌳", "weight": 1.7},
    {"name": "송학", "emoji": "🦅", "weight": 1.7},
    {"name": "국준", "emoji": "🍷", "weight": 1.7},
    {"name": "단풍", "emoji": "🍁", "weight": 1.7},
    {"name": "홍싸리", "emoji": "🌿", "weight": 1.7},
    # 5번 짝귀재료
    {"name": "개구리", "emoji": "🐸", "weight": 1.7},
    {"name": "멧돼지", "emoji": "🐗", "weight": 1.7},
    {"name": "기러기", "emoji": "🦆", "weight": 1.7},
    {"name": "사슴", "emoji": "🦌", "weight": 1.7},
    {"name": "봉황", "emoji": "🔥", "weight": 1.7},
    # 6번 예림이재료
    {"name": "휘파람새", "emoji": "🐦", "weight": 1.7},
    {"name": "두견새", "emoji": "🐤", "weight": 1.7},
    {"name": "매조", "emoji": "🦜", "weight": 1.7},
    {"name": "학", "emoji": "🦢", "weight": 1.7},
    {"name": "공산", "emoji": "⛰️", "weight": 1.7},
    # 기타 및 재화
    {"name": "방뚫권(1일)", "emoji": "🔓", "weight": 4.0},
    {"name": "방뚫권(3일)", "emoji": "🔐", "weight": 1.0},
    {"name": "500EXP", "emoji": "💰", "weight": 20.0},
    {"name": "1000EXP", "emoji": "💵", "weight": 18.5},
    {"name": "5000EXP", "emoji": "💳", "weight": 9.0},
    {"name": "한번더", "emoji": "🔄", "weight": 2.0},
]

# --- 2. 카테고리 및 조합 레시피 설정 ---
CATEGORIES = {
    "✨ 완제품": ["고니", "평경장", "아귀", "짝귀", "예림이"],
    "🎴 고니 재료 (2번)": ["홍단", "매화", "벚꽃", "만막", "붓꽃"],
    "👴🏼 평경장 재료 (3번)": ["모란꽃", "청단", "나비", "난초", "국화"],
    "👹 아귀 재료 (4번)": ["벚나무", "송학", "국준", "단풍", "홍싸리"],
    "👂 짝귀 재료 (5번)": ["개구리", "멧돼지", "기러기", "사슴", "봉황"],
    "💃 예림이 재료 (6번)": ["휘파람새", "두견새", "매조", "학", "공산"],
    "📦 소모품 및 기타": ["방뚫권(1일)", "방뚫권(3일)", "한번더"]
}

CRAFT_MAP = {
    "🎴 고니 재료 (2번)": "고니",
    "👴🏼 평경장 재료 (3번)": "평경장",
    "👹 아귀 재료 (4번)": "아귀",
    "👂 짝귀 재료 (5번)": "짝귀",
    "💃 예림이 재료 (6번)": "예림이"
}

BOX_LIST = {
    "타짜상자": {"items": TAJJA_ITEMS, "emoji": "🎴", "color": 0xE74C3C},
}

# --- 데이터 관리 함수 ---
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

# --- 3. View 클래스들 ---

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
            
            drawn_log = []
            while True:
                item = draw_item(box["items"])
                if item["name"] == "한번더":
                    drawn_log.append(f"{item['emoji']} **한번더**")
                    continue
                else:
                    final_item = item
                    break
            
            if user_id not in data: data[user_id] = {"inventory": {}}
            inv = data[user_id]["inventory"]
            inv[final_item["name"]] = inv.get(final_item["name"], 0) + 1
            save_data(data)

            desc = ""
            if drawn_log:
                desc = " > ".join(drawn_log) + " > \n\n"
            desc += f"{final_item['emoji']} **{final_item['name']}** 획득!"

            embed = discord.Embed(title=f"{box['emoji']} {box_name} 결과", description=desc, color=box["color"])
            await interaction.response.edit_message(content="✅ 결과가 나왔습니다!", view=None)
            await interaction.followup.send(embed=embed)
        return callback

# --- 4. 봇 명령어 ---

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ {bot.user} 로그인 완료")

@tree.command(name="뽑기", description="상자를 오픈합니다.")
async def gacha(interaction: discord.Interaction):
    if not await check_channel(interaction): return
    await interaction.response.send_message("🎁 상자를 선택하세요!", view=BoxSelectView(str(interaction.user.id)), ephemeral=True)

@tree.command(name="인벤토리", description="항목별 보유 아이템 확인")
async def inventory(interaction: discord.Interaction):
    if not await check_channel(interaction): return
    data = load_data()
    user_id = str(interaction.user.id)
    inv = data.get(user_id, {}).get("inventory", {})
    if not inv:
        await interaction.response.send_message("비어있습니다.", ephemeral=True)
        return

    embed = discord.Embed(title=f"🎒 {interaction.user.display_name}의 가방", color=0x3498DB)
    
    # 카테고리별 출력 로직
    all_listed = []
    for cat_name, items in CATEGORIES.items():
        found = []
        for name in items:
            if inv.get(name, 0) > 0:
                emoji = next((i["emoji"] for i in TAJJA_ITEMS if i["name"] == name), "🔹")
                found.append(f"{emoji} {name} x{inv[name]}")
                all_listed.append(name)
        if found:
            embed.add_field(name=cat_name, value="\n".join(found), inline=False)

    # 나머지 재화
    others = [f"{next((i['emoji'] for i in TAJJA_ITEMS if i['name'] == k), '💰')} {k} x{v}" 
              for k, v in inv.items() if k not in all_listed and v > 0]
    if others:
        embed.add_field(name="💰 재화 및 기타", value="\n".join(others), inline=False)

    await interaction.response.send_message(embed=embed)

@tree.command(name="조합", description="보유한 재료 세트로 상급 아이템을 제작합니다.")
async def craft(interaction: discord.Interaction):
    if not await check_channel(interaction): return
    user_id = str(interaction.user.id)
    data = load_data()
    inv = data.get(user_id, {}).get("inventory", {})

    success_log = []
    for cat_name, result_name in CRAFT_MAP.items():
        ingredients = CATEGORIES[cat_name]
        # 해당 세트의 모든 재료를 최소 1개 이상 가지고 있는지 체크
        while all(inv.get(ing, 0) >= 1 for ing in ingredients):
            for ing in ingredients:
                inv[ing] -= 1
            inv[result_name] = inv.get(result_name, 0) + 1
            res_emoji = next((i["emoji"] for i in TAJJA_ITEMS if i["name"] == result_name))
            success_log.append(f"✨ **{cat_name}** 조합 성공! ⮕ {res_emoji} **{result_name}** 획득")

    if not success_log:
        await interaction.response.send_message("❌ 조합 가능한 세트가 없습니다.", ephemeral=True)
    else:
        # 0개인 템 정리 후 저장
        data[user_id]["inventory"] = {k: v for k, v in inv.items() if v > 0}
        save_data(data)
        await interaction.response.send_message("\n".join(success_log))

@tree.command(name="확률", description="모든 아이템 확률 정보")
async def rates(interaction: discord.Interaction):
    if not await check_channel(interaction): return
    box = BOX_LIST["타짜상자"]
    total = sum(i["weight"] for i in box["items"])
    
    embed = discord.Embed(title="📊 타짜상자 상세 확률표", color=0x2ECC71)
    # 가독성을 위해 확률 순으로 정렬
    sorted_items = sorted(box["items"], key=lambda x: x['weight'])
    
    # 필드가 너무 길어질 수 있으므로 나눠서 저장
    chunks = [sorted_items[i:i + 12] for i in range(0, len(sorted_items), 12)]
    for idx, chunk in enumerate(chunks):
        lines = [f"{i['emoji']} {i['name']}: **{i['weight']/total*100:.3f}%**" for i in chunk]
        embed.add_field(name=f"목록 #{idx+1}", value="\n".join(lines), inline=True)
        
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)