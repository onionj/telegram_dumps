import os, csv
from pyrogram import Client, filters
from pyrogram.errors import PeerIdInvalid

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_ID: str
    API_HASH: str
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


setting = Settings()


app = Client("my_account", api_id=setting.API_ID, api_hash=setting.API_HASH)


def calculate_percentage(part, whole):
    try:
        percentage = (part / whole) * 100
        return percentage
    except ZeroDivisionError:
        return None


def is_english(text: str, eng_percentage: int):
    if eng_percentage == 0:
        return True

    text_len = len(text)
    eng_count = 0

    for char in text:
        if char.isascii():
            eng_count += 1

        current_percent = calculate_percentage(eng_count, text_len)
        if current_percent and current_percent >= eng_percentage:
            return True

    return False


async def read_chat_history(
    client, chat_id: str, limit: int = 100, eng_percentage: int = 50
):
    texts: list[tuple] = []
    async for message in client.get_chat_history(chat_id, limit=limit):
        if message.text and is_english(message.text, eng_percentage):
            username = ""
            id = ""

            sender = (
                message.forward_from_chat or message.sender_chat or message.from_user
            )

            if sender:
                username = sender.username
                id = sender.id
            else:
                print("sender not found", message)

            texts.append(
                (
                    message.date,
                    username,
                    id,
                    message.text,
                )
            )
    return texts


@app.on_message(filters.command(["getgroups"]) & filters.me)
async def get_groups_handler(client, message):
    """
    Group chat ids:
    `/getgroups`
    """
    print(message.text)
    temp_message = await message.reply("⌛️Processing...", quote=True)

    try:
        dialogs = []
        async for dialog in client.get_dialogs():
            if dialog.chat.type.value in {"group", "supergroup"}:
                dialogs.append(
                    f"{dialog.chat.title or dialog.chat.first_name}\n{dialog.chat.id}\n"
                )

        await message.reply("```Group Ids\n" + "\n".join(dialogs) + "```", quote=True)

    except:
        await message.reply("Error", quote=True)
        raise
    finally:
        await temp_message.delete()


@app.on_message(filters.command(["getprivates"]) & filters.me)
async def get_private_handler(client, message):
    """
    Privates chat ids:
    `/getprivates`
    """
    print(message.text)
    temp_message = await message.reply("⌛️Processing...")

    try:
        dialogs = []
        async for dialog in client.get_dialogs():
            if dialog.chat.type.value in {"private"}:
                dialogs.append(
                    f"{dialog.chat.title or dialog.chat.first_name}\n{dialog.chat.id}\n"
                )
        await message.reply(
            "```Privates chat ids\n" + "\n".join(dialogs) + "```", quote=True
        )

    except:
        await message.reply("⚠️ Error", quote=True)
        raise
    finally:
        await temp_message.delete()


@app.on_message(filters.command(["getchannels"]) & filters.me)
async def get_chanel_handler(client, message):
    """
    Channel chat ids:
    `/getchannels`
    """
    print(message.text)
    temp_message = await message.reply("⌛️Processing...", quote=True)

    try:
        dialogs = []
        async for dialog in client.get_dialogs():
            if dialog.chat.type.value in {"channel"}:
                dialogs.append(
                    f"{dialog.chat.title or dialog.chat.first_name}\n{dialog.chat.id}\n"
                )
        await message.reply("```Channel Ids\n" + "\n".join(dialogs) + "```", quote=True)

    except:
        await message.reply("⚠️ Error", quote=True)
        raise
    finally:
        await temp_message.delete()


@app.on_message(filters.command(["chat_dump"]) & filters.me)
async def chat_dump(client, message):
    """
    📝 Dump Groups, channels, and Private chats
    ```Format:\n/chat_dump CHAT_ID LIMIT ENG_PERCENTAGE\n```
    ```Example:\n/chat_dump -12345678 1000 60\n```
    ```Get Chat Ids:\n/getgroups\n/getchannels\n/getprivates```
    """
    print(message.text)

    if message.text == "help":
        await message.reply(chat_dump.__doc__, quote=True)

    temp_message = await message.reply("⌛️Processing...", quote=True)

    try:
        chat_id, limit, eng_percentage = message.text.strip("/chat_dump ").split(" ")
        messages = await read_chat_history(
            client=client,
            chat_id=chat_id,
            limit=int(limit),
            eng_percentage=int(eng_percentage),
        )
        file_name = f"chat_dump_{chat_id}_{limit}_{eng_percentage}.csv"
        caption = f"""
        chat_id: {chat_id}
        limit: {limit}
        eng_percentage: {eng_percentage}
        csv rows: {len(messages)}
        """

        with open(file_name, "w", newline="", encoding="utf-8") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["datetime", "username", "id", "message"])
            csv_writer.writerows(messages)

        await message.reply_document(file_name, quote=True, caption=caption)
        os.remove(file_name)

    except PeerIdInvalid:
        await message.reply("⚠️ Invalid ChatID\n", quote=True)
    except ValueError:
        await message.reply("⚠️ Value Error, Help:\n" + chat_dump.__doc__, quote=True)
    except:
        await message.reply("⚠️ Error", quote=True)
        raise
    finally:
        await temp_message.delete()


@app.on_message(filters.command(["help"]) & filters.me)
async def help(client, message):
    print(message.text)
    await message.reply(chat_dump.__doc__, quote=True)


app.run()
