import random
import json
from twitchio.ext import commands
from supabase_client import get_balance, add_points, deduct_points

# Load config
with open("config.json", "r") as f:
    CONFIG = json.load(f)

CHANNEL = CONFIG["channel"].lower()
BOT_NICK = CONFIG["bot_nick"]
TOKEN = CONFIG["token"]
POINT_NAME = CONFIG["stream_points_name"]
BET_MULTIPLIER = CONFIG["bet_multiplier"]

class BingoBot(commands.Bot):
    def __init__(self):
        super().__init__(token=TOKEN, prefix='!', initial_channels=[CHANNEL])
        self.boards = {}  # {username: {"board": [...], "bet": X}}

    def generate_board(self):
        tiles = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        random.shuffle(tiles)
        return tiles[:25]

    def check_bingo(self, board):
        for row in range(5):
            if all(board[row * 5 + col] == "#" for col in range(5)):
                return True
        for col in range(5):
            if all(board[row * 5 + col] == "#" for row in range(5)):
                return True
        if all(board[i * 5 + i] == "#" for i in range(5)):
            return True
        if all(board[i * 5 + (4 - i)] == "#" for i in range(5)):
            return True
        return False

    def mark_tile(self, board, tile):
        tile = tile.upper()
        if tile in board:
            idx = board.index(tile)
            board[idx] = "#"
            return True
        return False

    def print_board(self, board):
        return "\n".join([" ".join(board[i*5:(i+1)*5]) for i in range(5)])

    async def event_ready(self):
        print(f"{BOT_NICK} is live and connected to chat.")

    @commands.command(name="joinbingo")
    async def join_bingo(self, ctx):
        user = ctx.author.name.lower()
        parts = ctx.message.content.strip().split()

        if len(parts) != 2:
            await ctx.send(f"{user}, usage: !joinbingo <amount>")
            return

        try:
            bet_amount = int(parts[1])
            if bet_amount <= 0:
                raise ValueError()
        except ValueError:
            await ctx.send(f"{user}, please enter a valid bet amount (e.g. !joinbingo 10).")
            return

        if user in self.boards:
            await ctx.send(f"{user}, you're already in!")
            return

        if not deduct_points(user, bet_amount):
            await ctx.send(f"{user}, you don’t have enough {POINT_NAME} to bet {bet_amount}.")
            return

        self.boards[user] = {
            "board": self.generate_board(),
            "bet": bet_amount
        }

        await ctx.send(f"{user} joined bingo with a {bet_amount} {POINT_NAME} bet!")

    @commands.command(name="myboard")
    async def show_board(self, ctx):
        user = ctx.author.name.lower()
        if user not in self.boards:
            await ctx.send(f"{user}, you haven't joined yet! Type !joinbingo <amount>")
            return
        board = self.boards[user]["board"]
        board_str = self.print_board(board)
        await ctx.send(f"{user}'s board:\n{board_str}")

    @commands.command(name="mark")
    async def mark_tile_cmd(self, ctx):
        if ctx.author.name.lower() != CHANNEL and not ctx.author.is_mod:
            return

        parts = ctx.message.content.strip().split()
        if len(parts) != 2:
            await ctx.send("Usage: !mark <letter>")
            return

        tile = parts[1].upper()
        marked = 0
        winners = []

        for user, entry in self.boards.items():
            board = entry["board"]
            if self.mark_tile(board, tile):
                marked += 1
                if self.check_bingo(board):
                    winners.append(user)

        await ctx.send(f"{marked} boards updated with {tile}.")

        for user in winners:
            bet = self.boards[user]["bet"]
            reward = bet * BET_MULTIPLIER
            add_points(user, reward)
            await ctx.send(f"🎉 {user} got a BINGO! (+{reward} {POINT_NAME})")

bot = BingoBot()
bot.run()