import discord
from discord import app_commands
import random
import json
import os
import time

# --- 설정 및 환경변수 ---
TOKEN = os.environ.get("TOKEN")
ALLOWED_CHANNEL_IDS = [1481967169746112553, 1482035295338627072, 1482063138495926396]
ADMIN_ROLE_IDS = [1467919008610259198, 1468252935119962152]
DATA_FILE = "data.json"

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# --- 1. 아이템 구성 ---
TAJJA_ITEMS = [
    {"name": "고니", "emoji": "🧒🏻", "weight": 0.25},
    {"name": "평경장", "emoji": "👴🏼", "weight": 0.4375},
    {"name": "아귀", "emoji": "👹", "weight": 0.4375},
    {"name": "짝귀", "emoji": "👂", "weight": 0.4375},
    {"name": "예림이", "emoji": "💃", "weight": 0.4375},
    {"name": "홍단", "emoji": "📜", "weight": 1.5725},
    {"name": "매화", "emoji": "🌸", "weight": 1.5725},
    {"name": "벚꽃", "emoji": "🌸", "weight": 1.5725},
    {"name": "만막", "emoji": "🎑", "weight": 1.5725},
    {"name": "붓꽃", "emoji": "🌿", "weight": 1.5725},
    {"name": "모란꽃", "emoji": "🌺", "weight": 1.7725},
    {"name": "청단", "emoji": "📘", "weight": 1.7725},
    {"name": "나비", "emoji": "🦋", "weight": 1.7725},
    {"name": "난초", "emoji": "🌱", "weight": 1.7725},
    {"name": "국화", "emoji": "🌼", "weight": 1.7725},
    {"name": "벚나무", "emoji": "🌳", "weight": 1.7725},
    {"name": "송학", "emoji": "🦅", "weight": 1.7725},
    {"name": "국준", "emoji": "🍷", "weight": 1.7725},
    {"name": "단풍", "emoji": "🍁", "weight": 1.7725},
    {"name": "홍싸리", "emoji": "🌿", "weight": 1.7725},
    {"name": "개구리", "emoji": "🐸", "weight": 1.7725},
    {"name": "멧돼지", "emoji": "🐗", "weight": 1.7725},
    {"name": "기러기", "emoji": "🦆", "weight": 1.7725},
    {"name": "사슴", "emoji": "🦌", "weight": 1.7725},
    {"name": "봉황", "emoji": "🔥", "weight": 1.7725},
    {"name": "휘파람새", "emoji": "🐦", "weight": 1.7725},
    {"name": "두견새", "emoji": "🐤", "weight": 1.7725},
    {"name": "매조", "emoji": "🦜", "weight": 1.7725},
    {"name": "학", "emoji": "🦢", "weight": 1.7725},
    {"name": "공산", "emoji": "⛰️", "weight": 1.7725},
    {"name": "방뚫권(1일)", "emoji": "🔓", "weight": 4.0},
    {"name": "방뚫권(3일)", "emoji": "🔐", "weight": 1.0},
    {"name": "500EXP", "emoji": "💰", "weight": 20.0},
    {"name": "1000EXP", "emoji": "💵", "weight": 18.5},
    {"name": "5000EXP", "emoji": "💳", "weight": 9.0},
    {"name": "한번더", "emoji": "🔄", "weight": 2.0},
]

CATEGORIES = {
    "✨ 역할": ["고니", "평경장", "아귀", "짝귀", "예림이"],
    "🎴 고니 재료": ["홍단", "매화", "벚꽃", "만막", "붓꽃"],
    "👴🏼 평경장 재료": ["모란꽃", "청단", "나비", "난초", "국화"],
    "👹 아귀 재료": ["벚나무", "송학", "국준", "단풍", "홍싸리"],
    "👂 짝귀 재료": ["개구리", "멧돼지", "기러기", "사슴", "봉황"],
    "💃 예림이 재료": ["휘파람새", "두견새", "매조", "학", "공산"],
    "💰 EXP": ["500EXP", "1000EXP", "5000EXP"],
    "📦 기타": ["방뚫권(1일)", "방뚫권(3일)", "한번더"]
}

CRAFT_MAP = {
    "🎴 고니 재료": "고니", "👴🏼 평경장 재료": "평경장",
    "👹 아귀 재료": "아귀", "👂 짝귀 재료": "짝귀", "💃 예림이 재료": "예림이"
}

BOX_LIST = {"타짜상자": {"items": TAJJA_ITEMS, "emoji": "🎴", "color": 0xE74C3C}}

# --- 데이터 유틸리티 ---
def load_data():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(interaction: discord.Interaction) -> bool:
    user_roles = [role.id for role in interaction.user.roles]
    return interaction.user.guild_permissions.administrator or any(r in user_roles for r in ADMIN_ROLE_IDS)

async def check_channel(interaction: discord.Interaction) -> bool:
    if interaction.channel_id not in ALLOWED_CHANNEL_IDS:
        await interaction.response.send_message("❌ 이 명령어는 지정된 뽑기 채널에서만 사용할 수 있어요!", ephemeral=True)
        return False
    return True

# --- 2. 관리자 전용 클래스 ---
class EditItemModal(discord.ui.Modal):
    def __init__(self, target_id, target_name, item_name, current_count):
        super().__init__(title=f"{item_name} 수량 수정")
        self.target_id, self.target_name, self.item_name = target_id, target_name, item_name
        self.amount = discord.ui.TextInput(label=f"수량 (현재: {current_count}개)", placeholder="0 입력 시 제거", required=True)
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        try: count = int(self.amount.value)
        except: return await interaction.response.send_message("❌ 숫자만 입력!", ephemeral=True)
        data = load_data()
        user_data = data.setdefault(self.target_id, {"inventory": {}})
        if count <= 0: user_data["inventory"].pop(self.item_name, None)
        else: user_data["inventory"][self.item_name] = count
        save_data(data)
        await interaction.response.send_message(f"✅ **{self.target_name}**의 **{self.item_name}**: {count}개 설정 완료", ephemeral=True)

class ItemSelectView(discord.ui.View):
    def __init__(self, target_id, target_name, inventory):
        super().__init__(timeout=60)
        self.target_id, self.target_name = target_id, target_name
        options = []
        for k, v in list(inventory.items())[:15]:
            options.append(discord.SelectOption(label=f"{k} ({v}개)", value=k))
        essentials = ["500EXP", "1000EXP", "5000EXP", "고니", "평경장", "아귀", "짝귀", "예림이"]
        for item in essentials:
            if item not in inventory and len(options) < 25:
                options.append(discord.SelectOption(label=f"{item} (추가하기)", value=item))
        select = discord.ui.Select(placeholder="수정/추가할 아이템 선택", options=options)
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        item_name = interaction.data["values"][0]
        data = load_data()
        curr = data.get(self.target_id, {}).get("inventory", {}).get(item_name, 0)
        await interaction.response.send_modal(EditItemModal(self.target_id, self.target_name, item_name, curr))

class AdminConfirmClearView(discord.ui.View):
    def __init__(self, admin_id, target_id, target_name):
        super().__init__(timeout=15)
        self.admin_id, self.target_id, self.target_name = admin_id, target_id, target_name

    @discord.ui.button(label="✅ 확인", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.admin_id: return
        data = load_data()
        if self.target_id in data: data[self.target_id]["inventory"] = {}
        save_data(data)
        await interaction.response.edit_message(content=f"🗑️ **{self.target_name}** 초기화 완료", view=None)

# --- 3. 일반 사용자 View ---
class BoxSelectView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=30)
        self.user_id = user_id

    def make_callback(self, box_name):
        async def callback(interaction: discord.Interaction):
            if str(interaction.user.id) != self.user_id: return
            data, box = load_data(), BOX_LIST[box_name]
            log = []
            while True:
                item = random.choices(box["items"], weights=[i["weight"] for i in box["items"]], k=1)[0]
                if item["name"] == "한번더": log.append(f"{item['emoji']} **한번더**"); continue
                final_item = item; break
            
            user_id = self.user_id
            if user_id not in data: data[user_id] = {"inventory": {}}
            inv = data[user_id].setdefault("inventory", {})
            inv[final_item["name"]] = inv.get(final_item["name"], 0) + 1
            save_data(data)

            desc = (" > ".join(log) + " > \n\n" if log else "") + f"{final_item['emoji']} **{final_item['name']}** 획득!"
            embed = discord.Embed(title=f"{box['emoji']} 결과", description=desc, color=box["color"])
            embed.set_author(name=f"{interaction.user.display_name}님의 결과", icon_url=interaction.user.display_avatar.url)
            
            await interaction.response.edit_message(content="✅ 결과 확인", view=None)
            await interaction.followup.send(embed=embed)
        return callback

    @classmethod
    def create(cls, user_id):
        view = cls(user_id)
        for box_name, box_data in BOX_LIST.items():
            btn = discord.ui.Button(label=f"{box_data['emoji']} {box_name}", style=discord.ButtonStyle.primary)
            btn.callback = view.make_callback(box_name)
            view.add_item(btn)
        return view

# --- 4. 명령어 ---
@bot.event
async def on_ready(): await tree.sync(); print(f"✅ {bot.user} 로그인")

# [채널 제한 적용] 뽑기
@tree.command(name="뽑기")
async def gacha(interaction: discord.Interaction):
    if await check_channel(interaction): # 지정 채널에서만 작동
        await interaction.response.send_message("🎁 상자 선택", view=BoxSelectView.create(str(interaction.user.id)), ephemeral=True)

# [채널 제한 해제] 인벤토리는 어디서나 확인 가능
@tree.command(name="인벤토리")
async def inventory(interaction: discord.Interaction):
    inv = load_data().get(str(interaction.user.id), {}).get("inventory", {})
    if not inv: return await interaction.response.send_message("비어있음", ephemeral=True)
    embed = discord.Embed(title=f"🎒 {interaction.user.display_name}의 가방", color=0x3498DB)
    all_listed = []
    total_exp = 0
    exp_values = {"500EXP": 500, "1000EXP": 1000, "5000EXP": 5000}
    for e_name, e_val in exp_values.items(): total_exp += inv.get(e_name, 0) * e_val
    embed.description = f"💵 **보유 재화 합계: {total_exp:,} EXP**"
    for cat, items in CATEGORIES.items():
        found = [f"{next(i['emoji'] for i in TAJJA_ITEMS if i['name']==n)} {n} x{inv[n]}" for n in items if inv.get(n,0)>0]
        if found: embed.add_field(name=cat, value="\n".join(found), inline=False); all_listed.extend(items)
    others = [f"{next((i['emoji'] for i in TAJJA_ITEMS if i['name']==k), '💰')} {k} x{v}" for k, v in inv.items() if k not in all_listed and v>0]
    if others: embed.add_field(name="💰 기타", value="\n".join(others), inline=False)
    await interaction.response.send_message(embed=embed)

# [채널 제한 적용] 조합
@tree.command(name="조합")
async def craft(interaction: discord.Interaction):
    if await check_channel(interaction): # 지정 채널에서만 작동
        user_id, data = str(interaction.user.id), load_data()
        inv, logs = data.get(user_id, {}).get("inventory", {}), []
        for cat, res in CRAFT_MAP.items():
            while all(inv.get(ing, 0) >= 1 for ing in CATEGORIES[cat]):
                for ing in CATEGORIES[cat]: inv[ing] -= 1
                inv[res] = inv.get(res, 0) + 1
                logs.append(f"✨ **{cat}** 성공 ⮕ **{res}**")
        if not logs: await interaction.response.send_message("❌ 재료 부족", ephemeral=True)
        else: data[user_id]["inventory"] = {k:v for k,v in inv.items() if v>0}; save_data(data); await interaction.response.send_message("\n".join(logs))

# [채널 제한 해제] 확률은 어디서나 확인 가능 (관리자 전용은 유지)
@tree.command(name="확률")
async def rates(interaction: discord.Interaction):
    if not is_admin(interaction):
        return await interaction.response.send_message("❌ 이 명령어는 관리자만 사용할 수 있습니다.", ephemeral=True)
    box = BOX_LIST["타짜상자"]
    total = sum(i["weight"] for i in box["items"])
    items = sorted(box["items"], key=lambda x: x['weight'], reverse=True)
    rate_text = ""
    for x in items:
        rate_text += f"{x['emoji']} **{x['name']}**: {x['weight']/total*100:.3f}%\n"
    embed = discord.Embed(title="📊 타짜상자 상세 확률표", description=rate_text, color=0x2ECC71)
    embed.set_footer(text="관리자 전용 데이터입니다.")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# [채널 제한 해제] 관리자 명령어
@tree.command(name="관리자_인벤토리수정")
async def admin_edit(interaction: discord.Interaction, 유저: discord.Member):
    if not is_admin(interaction): return await interaction.response.send_message("❌ 권한없음", ephemeral=True)
    data = load_data()
    inv = data.get(str(유저.id), {}).get("inventory", {})
    await interaction.response.send_message(f"🎒 {유저.display_name} 수정", view=ItemSelectView(str(유저.id), 유저.display_name, inv), ephemeral=True)

@tree.command(name="관리자_인벤토리초기화")
async def admin_clear(interaction: discord.Interaction, 유저: discord.Member):
    if not is_admin(interaction): return await interaction.response.send_message("❌ 권한없음", ephemeral=True)
    await interaction.response.send_message(f"⚠️ {유저.display_name} 초기화?", view=AdminConfirmClearView(str(interaction.user.id), str(유저.id), 유저.display_name), ephemeral=True)

bot.run(TOKEN)