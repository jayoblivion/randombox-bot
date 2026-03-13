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

BOX_LIST = {
    "타짜상자": {
        "items": TAJJA_ITEMS,
        "emoji": "🎴",
        "color": 0xE74C3C,
    },
}

COOLDOWN_SECONDS = 0
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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

class EditItemModal(discord.ui.Modal):
    def __init__(self, target_id, target_name, item_name, current_count):
        super().__init__(title=f"{item_name} 수량 수정")
        self.target_id = target_id
        self.target_name = target_name
        self.item_name = item_name
        self.amount = discord.ui.TextInput(
            label=f"수량 입력 (현재: {current_count}개)",
            placeholder="0 입력 시 아이템 제거",
            required=True
        )
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            count = int(self.amount.value)
        except ValueError:
            await interaction.response.send_message("❌ 숫자만 입력해주세요!", ephemeral=True)
            return

        if count < 0:
            await interaction.response.send_message("❌ 0 이상의 숫자를 입력해주세요!", ephemeral=True)
            return

        data = load_data()
        if count == 0:
            data[self.target_id]["inventory"].pop(self.item_name, None)
            save_data(data)
            await interaction.response.send_message(f"🗑️ **{self.target_name}**의 **{self.item_name}** 을 제거했어요!", ephemeral=True)
        else:
            data[self.target_id]["inventory"][self.item_name] = count
            save_data(data)
            await interaction.response.send_message(f"✅ **{self.target_name}**의 **{self.item_name}** 을 **{count}개** 로 설정했어요!", ephemeral=True)

class ItemSelectView(discord.ui.View):
    def __init__(self, target_id, target_name, inventory):
        super().__init__(timeout=60)
        self.target_id = target_id
        self.target_name = target_name

        options = [
            discord.SelectOption(label=f"{name} (현재 {count}개)", value=name)
            for name, count in inventory.items()
        ]

        select = discord.ui.Select(placeholder="수정할 아이템을 선택하세요", options=options)
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        item_name = interaction.data["values"][0]
        data = load_data()
        current_count = data[self.target_id]["inventory"].get(item_name, 0)
        modal = EditItemModal(self.target_id, self.target_name, item_name, current_count)
        await interaction.response.send_modal(modal)

class AdminConfirmClearView(discord.ui.View):
    def __init__(self, admin_id, target_id, target_name):
        super().__init__(timeout=15)
        self.admin_id = admin_id
        self.target_id = target_id
        self.target_name = target_name

    @discord.ui.button(label="✅ 확인", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.admin_id:
            await interaction.response.send_message("본인만 사용할 수 있어요!", ephemeral=True)
            return
        data = load_data()
        if self.target_id in data:
            data[self.target_id]["inventory"] = {}
            save_data(data)
        await interaction.response.edit_message(content=f"🗑️ **{self.target_name}**의 인벤토리가 초기화됐어요!", view=None)

    @discord.ui.button(label="❌ 취소", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.admin_id:
            await interaction.response.send_message("본인만 사용할 수 있어요!", ephemeral=True)
            return
        await interaction.response.edit_message(content="❌ 취소됐어요!", view=None)

class BoxSelectView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=30)
        self.user_id = user_id

        for box_name, box_data in BOX_LIST.items():
            button = discord.ui.Button(
                label=f"{box_data['emoji']} {box_name}",
                custom_id=box_name,
                style=discord.ButtonStyle.primary
            )
            button.callback = self.make_callback(box_name)
            self.add_item(button)

    def make_callback(self, box_name):
        async def callback(interaction: discord.Interaction):
            if str(interaction.user.id) != self.user_id:
                await interaction.response.send_message("본인만 선택할 수 있어요!", ephemeral=True)
                return

            now = time.time()
            data = load_data()
            user_id = self.user_id
            cooldown_key = f"last_draw_{box_name}"

            if user_id in data:
                elapsed = now - data[user_id].get(cooldown_key, 0)
                if elapsed < COOLDOWN_SECONDS:
                    remaining = int(COOLDOWN_SECONDS - elapsed)
                    await interaction.response.edit_message(
                        content=f"⏳ 쿨타임 중! **{remaining}초** 후에 다시 뽑을 수 있어요.",
                        view=None
                    )
                    return

            box = BOX_LIST[box_name]
            item = draw_item(box["items"])

            if user_id not in data:
                data[user_id] = {}
            data[user_id][cooldown_key] = now
            if "inventory" not in data[user_id]:
                data[user_id]["inventory"] = {}
            inv = data[user_id]["inventory"]
            inv[item["name"]] = inv.get(item["name"], 0) + 1
            save_data(data)

            embed = discord.Embed(
                title=f"{box['emoji']} {box_name} 오픈!",
                description=f"{item['emoji']} **{item['name']}** 획득!",
                color=box["color"]
            )
            embed.set_footer(text=f"{interaction.user.display_name} | 쿨타임: {COOLDOWN_SECONDS}초")
            await interaction.response.edit_message(content="✅ 상자를 선택했어요!", view=None)
            await interaction.followup.send(embed=embed)

        return callback

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ 봇 로그인 완료: {bot.user}")

@tree.command(name="뽑기", description="랜덤박스를 열어 아이템을 획득합니다!")
async def gacha(interaction: discord.Interaction):
    if not await check_channel(interaction):
        return
    user_id = str(interaction.user.id)
    view = BoxSelectView(user_id)
    await interaction.response.send_message("🎁 오픈할 상자를 선택해주세요!", view=view, ephemeral=True)

@tree.command(name="인벤토리", description="내 보유 아이템을 확인합니다.")
async def inventory(interaction: discord.Interaction):
    if not await check_channel(interaction):
        return
    user_id = str(interaction.user.id)
    data = load_data()

    if user_id not in data or not data[user_id].get("inventory"):
        await interaction.response.send_message("인벤토리가 비어있어요! `/뽑기`로 아이템을 획득하세요.", ephemeral=True)
        return

    inv = data[user_id]["inventory"]
    lines = [f"🎴 {name} x{count}" for name, count in inv.items()]
    embed = discord.Embed(
        title=f"🎒 {interaction.user.display_name}의 인벤토리",
        description="\n".join(lines),
        color=0x3498DB
    )
    await interaction.response.send_message(embed=embed)

@tree.command(name="관리자_인벤토리수정", description="특정 유저의 인벤토리를 수정합니다.")
async def admin_edit_inventory(interaction: discord.Interaction, 유저: discord.Member):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ 권한이 없어요!", ephemeral=True)
        return

    target_id = str(유저.id)
    data = load_data()

    if target_id not in data or not data[target_id].get("inventory"):
        await interaction.response.send_message(f"❌ **{유저.display_name}**의 인벤토리가 비어있어요!", ephemeral=True)
        return

    inv = data[target_id]["inventory"]
    lines = [f"🎴 {name} x{count}" for name, count in inv.items()]
    embed = discord.Embed(
        title=f"🎒 {유저.display_name}의 인벤토리",
        description="\n".join(lines),
        color=0x3498DB
    )
    view = ItemSelectView(target_id, 유저.display_name, inv)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@tree.command(name="관리자_인벤토리초기화", description="특정 유저의 인벤토리를 초기화합니다.")
async def admin_clear_inventory(interaction: discord.Interaction, 유저: discord.Member):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ 권한이 없어요!", ephemeral=True)
        return
    view = AdminConfirmClearView(str(interaction.user.id), str(유저.id), 유저.display_name)
    await interaction.response.send_message(f"⚠️ 정말 **{유저.display_name}**의 인벤토리를 초기화할까요?", view=view, ephemeral=True)

@tree.command(name="확률", description="상자별 아이템 확률을 확인합니다.")
async def show_rates(interaction: discord.Interaction):
    if not await check_channel(interaction):
        return
    embed = discord.Embed(title="📊 상자별 확률표", color=0x2ECC71)
    for box_name, box_data in BOX_LIST.items():
        total = sum(i["weight"] for i in box_data["items"])
        lines = [f"{i['emoji']} {i['name']}: {i['weight']/total*100:.1f}%" for i in box_data["items"]]
        embed.add_field(name=f"{box_data['emoji']} {box_name}", value="\n".join(lines), inline=False)
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)