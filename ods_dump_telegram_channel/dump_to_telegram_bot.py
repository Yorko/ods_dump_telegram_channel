import json
import time
from pathlib import Path
from typing import Any, Dict, List

import requests
from tqdm import tqdm

from ods_dump_telegram_channel.utils import load_config_params, process_to_html


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
    min_length: int = 300,
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

                if len(post) < min_length:
                    continue

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


def send_with_sleep(
    messages: List[str],
    user_dict,
    token: str,
    chat_id: str,
    short_pause_sec: int = 1,
    long_pause_sec: int = 120,
    send_as_html: bool = True,
):

    for message in tqdm(messages, total=len(messages)):

        html_message = process_to_html(message, user_dict=user_dict)
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={html_message}"
        if send_as_html:
            html_url = url + "&parse_mode=html"
            resp = requests.get(html_url).json()

            # TODO: implement nice retries
            if resp.get("error_code") == 400:
                print("sending as raw text")
                url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
                resp = requests.get(url).json()
            elif resp.get("error_code") == 429:
                print(f"Sleeping {long_pause_sec} sec.")
                time.sleep(long_pause_sec)
                # TODO: here we can still hit an error, retries needed
                resp = requests.get(html_url).json()
            print(resp)

        time.sleep(short_pause_sec)


def main():
    # loading project-wide configuration params
    params: Dict[str, Any] = load_config_params()
    path_to_dump = Path(params["data"]["path_to_ods_slack_dump"])
    with open(params["telegram"]["path_to_telegram_bot_secret_file"]) as f:
        telegram_token = f.read().strip()
    telegram_chat_id = params["telegram"]["telegram_chat_id"]

    # get a dictionary with user nicknames
    user_dict = get_user_dict(path_to_dump=path_to_dump)

    # get all posts from the channel
    posts = get_posts(
        path_to_dump=path_to_dump,
        user_dict=user_dict,
        channel=params["data"]["ods_channel_name"],
    )

    # send posts to a Telegram bot
    send_with_sleep(messages=posts, token=telegram_token, chat_id=telegram_chat_id, user_dict=user_dict)


if __name__ == "__main__":
    main()
