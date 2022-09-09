import re
from pathlib import Path
from typing import Any, Dict

import yaml


def get_project_root() -> Path:
    """
    Return a Path object pointing to the project root directory.
    :return: Path
    """
    return Path(__file__).parent.parent


def load_config_params() -> Dict[str, Any]:
    """
    Loads global project configuration params defined in the `config.yaml` file.
    :return: a nested dictionary corresponding to the `config.yaml` file.
    """
    project_root: Path = get_project_root()
    with open(project_root / "config.yml") as f:
        params: Dict[str, Any] = yaml.load(f, Loader=yaml.FullLoader)
    return params


def process_to_html(message: str, user_dict: Dict[str, str]):
    """

    :param message: message text
    :param user_dict: a dictionary mapping Slack User IDs to their nicknames
    :return: HTML-formatted message
    """

    # replace user mentions
    message = re.sub(
        r"\<@.+\>",
        lambda x: user_dict.get(x.group(0).strip("<>@"), "USER") if x.group(0) else x.group(),
        message,
    )

    # format URLs: <url> -> <a href="url">url</a>
    message_with_links = re.sub(
        r"^[^\S\n]*\< |\<([^*\r\n]*)\>",
        lambda x: f'<a href="{x.group(1)}">{x.group(1)}</a>' if x.group(1) else x.group(),
        message,
        flags=re.M,
    )

    # format bolded text to HTML: *blabla* -> <blabla></b>
    bolded_message_with_links = re.sub(
        r"^[^\S\n]*\* |\*([^*\r\n]*)\*",
        lambda x: f"<b>{x.group(1)}</b>" if x.group(1) else x.group(),
        message_with_links,
        flags=re.M,
    )

    return bolded_message_with_links
