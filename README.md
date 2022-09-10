# Sending ODS Slack dump to a Telegram channel

OpenDataScience [ods.ai](https://ods.ai/) is an international Data Science community, mostly Russian-speaking. As a result of Feb 2022 disaster ODS Slack got under sanctions and can no longer register new users. Also, messages and files in [ODS Slack](https://opendatascience.slack.com/) older than 90 days are hidden (there's ongoing activity with migrating the community to [Matrix](https://chat.ods.ai/#/)). Luckily, we have some dumps. This repo helps to send messages from ODS Slack dump to a Telegram channel.

This code is used to populate the [ODS jobs dump](https://t.me/ods_jobs_dump_bot) Telegram bot, and it can be used for any other dumped Slack channel (**#theory\_and\_practice, #article_essence**, etc.)

## Setting up the environment

- Install Poetry with Python >= 3.9;
- Run `poetry install` to set up a virtual environment for the project and install all dependencies.

## Specifying the Telegram channel data

- Specify your channel ID in `config.yml` under  `telegram` -> `telegram_chat_id`. You can get your ID via [@username_to_id_bot](https://t.me/username_to_id_bot).

## Downloading the dump

The ODS Slack dump that I got spans 2015-04-14 to 2022-01-17. [Download link](https://disk.yandex.ru/d/Iz6qREJTrYItqw) (~500 Mb zipped, 3.3 Gb unzipped)

- Downlod a Slack dump, unpack it and specify the path in `config.yml` under `data` -> `path_to_ods_slack_dump`;
- Put the channel name of interest (e.g. "_jobs") in `config.yml` under `data` -> `ods_channel_name`.

## Sending messages from the dump to the bot

- Customize the code of the `ods_dump_telegram_channel.dump_to_telegram_bot.get_posts` function, e.g. you might want to add replies to messages, not only original posts. You might also show the number of reactions, etc;
- Run `poetry run python -m ods_dump_telegram_channel.dump_to_telegram_bot`.

## Caveates

Some of the caveates are mentiones in the source code of `ods_dump_telegram_channel.dump_to_telegram_bot.py` as TODOs. Current drawbacks:

- formatting to HTML is not complete, there are some issues, and I only formatted bolded text, user mentions, and hyperlinks, the rest is shown as plain text;
- the `bot.send_message` is still hitting timeout errors (e.g. telegram.error.RetryAfter: Flood control exceeded) so you'd better process posts in chuncks;
- Messages are limited to 4096 chars (that's not enough for e.g. posts in **#article_essence** where valuable content goes into a thread as well as the main post). It'd be nice to implement sending replies from a Slack thread as replies to a Telegram message.
