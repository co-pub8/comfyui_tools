import discord
import random

intents = discord.Intents.all()
client = discord.Client(intents=intents)


# Bot起動時に呼び出される関数
@client.event
async def on_ready():
    print("Ready!")


# メッセージの検知
@client.event
async def on_message(message):
    # 自身が送信したメッセージには反応しない
    if message.author == client.user:
        return

    # ユーザーからのメンションを受け取った場合、あらかじめ用意された配列からランダムに返信を返す
    if client.user in message.mentions:

        ansewr_list = [
            "さすがですね！",
            "知らなかったです！",
            "すごいですね！",
            "センスが違いますね！",
            "そうなんですか？",
        ]
        answer = random.choice(ansewr_list)
        print(answer)
        await message.channel.send(answer)


# Bot起動
client.run("APIキーを入力してください")
