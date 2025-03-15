import socket
import os
import discord
import mcstatus
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import traceback

load_dotenv()


def tcp_ping(host: str, port: int, timeout: float = 1.0) -> bool:
    """
    指定したホストとポートにTCP接続を試み、接続可能かを確認する。

    :param host: 接続先のホスト名またはIPアドレス
    :param port: 接続するポート番号
    :param timeout: タイムアウト時間（秒）
    :return: 接続成功なら True、失敗なら False
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
            return True
        except (socket.timeout, socket.error):
            return False


def getmcstatus(host: str, port: int, timeout: float = 1.0):
    server = mcstatus.JavaServer.lookup(f"{host}:{port}", timeout)
    return server


def create_embed(title, description, servName, color=discord.Color.green()):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="マイクラサーバー起動確認BOT ("+servName+")")
    return embed


servHost = "192.168.11.70"  # 変更してください
servPort = 25565
servName = "〇〇鯖"
TOKEN = os.getenv("PING_BOT_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


@tasks.loop(seconds=30)
async def playersCount():
    global servHost, servPort, servName
    status = getmcstatus(servHost, servPort, 5).status()
    status = discord.Game(
        f"参加人数: {status.players.online}人")
    await bot.change_presence(activity=status)


@bot.tree.command(name="ping", description=servName+"に接続できるか確認します")
async def ping(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    try:
        global servName
        if tcp_ping(servHost, servPort, 1):
            await interaction.followup.send(embed=create_embed(
                "確認結果", "サーバーは稼働しています", servName))
        else:
            await interaction.followup.send(embed=create_embed(
                "確認結果", "サーバーは停止しています", servName, discord.Color.red()))
    except Exception as e:
        user_dir = os.path.expanduser("~")
        stack_trace = traceback.format_exc()
        stack_trace = stack_trace.replace(user_dir, "C:\\Users\\*******")
        await interaction.followup.send(
            embed=create_embed("エラー", f"# {type(e).__name__}\nエラー内容: ```\n{stack_trace}\n```\n管理者にお問い合わせください", discord.Color.dark_red()))
        raise


@bot.tree.command(name="getserver", description=servName+"の情報を取得します")
async def getserver(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    try:
        query = getmcstatus(servHost, servPort, 5).query()
        players = query.players.names
        playersStr = ""
        for player in players:
            playersStr = playersStr + player+"\n"
        await interaction.followup.send(
            embed=create_embed("参加者", playersStr, servName))
    except Exception as e:
        user_dir = os.path.expanduser("~")
        stack_trace = traceback.format_exc()
        stack_trace = stack_trace.replace(user_dir, "C:\\Users\\*******")
        await interaction.followup.send(
            embed=create_embed("エラー", f"# {type(e).__name__}\nエラー内容: ```\n{stack_trace}\n```\n管理者にお問い合わせください", discord.Color.dark_red()))
        raise


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")
    playersCount.start()

bot.run(TOKEN)
