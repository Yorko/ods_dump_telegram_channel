import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List

import telegram
from async_timeout import timeout

from ods_dump_telegram_channel.utils import load_config_params, process_to_html

# loading project-wide configuration params
params: Dict[str, Any] = load_config_params()
PATH_TO_DUMP = Path(params["data"]["path_to_ods_slack_dump"])
with open(params["telegram"]["path_to_telegram_bot_secret_file"]) as f:
    TELEGRAM_TOKEN = f.read().strip()
TELEGRAM_USER_ID = params["telegram"]["telegram_user_id"]


def get_user_dict(path_to_dump: Path, filename: str = "users.json"):
    """

    :param path_to_dump: path to local Slack dump
    :param filename: filename with users info
    :return: a dictionary mapping Slack User IDs to their nicknames
    """
    with open(path_to_dump / filename) as f:
        full_user_dict_list = json.load(f)

    user_dict = {user_dict["id"]: user_dict["name"] for user_dict in full_user_dict_list}

    return user_dict


def get_posts(
    path_to_dump: Path,
    user_dict: Dict[str, str],
    channel: str,
    add_replies: bool = False,
    max_length: int = 3800,
) -> List[str]:
    posts = []

    for filename in sorted((path_to_dump / channel).glob("*.json")):
        with open(str(filename)) as f:

            post_date = filename.stem
            content = json.load(f)

            content_dict = {
                f"{entry['user']}_{entry['ts']}": {
                    "real_name": entry["user_profile"]["real_name"],
                    "text": entry["text"],
                }
                for entry in content
                if entry.get("user") and entry.get("user_profile")
            }

            for entry in content:

                # obligatory fields
                if not (entry.get("reply_count") and entry.get("reactions") and entry.get("user_profile")):
                    continue

                author, text = entry["user_profile"]["real_name"], entry["text"]

                post = f"POSTED BY *{author}* on {post_date}:\n{text}"

                # Nice try but posts get too long with replies, while Telegram can
                # send messages up to 4096 tokens.
                # TODO: figure out how to send messages as replies
                if add_replies:
                    # Adding only today's replies
                    today_reply_ids = [f"{reply['user']}_{reply['ts']}" for reply in entry["replies"]]
                    if set(content_dict.keys()).intersection(today_reply_ids):
                        post += "\n\nTHREAD:\n"

                        for reply in entry["replies"]:
                            reply_id = f"{reply['user']}_{reply['ts']}"
                            if not content_dict.get(reply_id):
                                continue
                            post += "-" * 16 + "\n" + content_dict[reply_id]["real_name"] + "\n"
                            post += (
                                process_to_html(content_dict[reply_id]["text"], user_dict=user_dict) + "\n" + "-" * 16
                            )

                posts.append(post[:max_length])

    return posts


async def send(
    message_body: str,
    telegram_token: str = TELEGRAM_TOKEN,
    telegram_user_id: str = TELEGRAM_USER_ID,
    timeout_sec: int = 30,
):
    bot = telegram.Bot(telegram_token)
    async with bot:
        # TODO: I'm still catching Telegram timeout errors (e.g. telegram.error.RetryAfter: Flood control exceeded)
        #  and have to process posts in chunks
        async with timeout(timeout_sec):
            try:
                await bot.send_message(
                    text=process_to_html(message_body, user_dict=user_dict),
                    chat_id=telegram_user_id,
                    parse_mode="HTML",
                )
            except telegram.error.BadRequest:
                await bot.send_message(
                    text=message_body,
                    chat_id=telegram_user_id,
                )


async def main():
    sent_messages = [send(post) for post in posts]
    await asyncio.gather(*sent_messages)


if __name__ == "__main__":

    # get a dictionary with user nicknames
    user_dict = get_user_dict(path_to_dump=PATH_TO_DUMP)

    # get all posts from the channel
    posts = get_posts(
        path_to_dump=PATH_TO_DUMP,
        user_dict=user_dict,
        channel=params["data"]["ods_channel_name"],
    )

    # send posts to a Telegram bot
    asyncio.run(main())
