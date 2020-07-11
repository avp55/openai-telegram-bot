import logging
import openai
import requests
import telegram as tg
from flask import Flask, request

from config import run_local

# Need to supply a credentials file with strings for Telegram Bot Key, OpenAI API Key, ngrok endpoint (localhost)
from .. import creds

# ---- Setup ----

# OpenAI API Token
openai.api_key = creds.openAI_token

# Initialize Telegram Bot
bot = tg.Bot(token=creds.bot_token)

# App Config
app = Flask(__name__)


@app.route('/', methods=['POST'])
def telegram_resp():
    content = request.get_json(silent=True)
    try:
        message = content['message']
        chat_id = message['chat']['id']
        msg_id = message['message_id']
        if is_valid_command(message):
            parsed_cmd, parsed_txt = return_recovered(message)
            if parsed_txt != "":
                if parsed_cmd == '/qa':
                    ai_qa_resp = open_ai_qa(parsed_txt)
                    bot.send_message(chat_id=chat_id, text=ai_qa_resp, reply_to_message_id=msg_id)
                elif parsed_cmd == '/ac':
                    ai_qa_resp = auto_comp(parsed_txt)
                    bot.send_message(chat_id=chat_id, text=ai_qa_resp, reply_to_message_id=msg_id)
    except KeyError:
        pass
    return ""


def is_valid_command(message):
    try:
        return message['entities'][0]['type'] == 'bot_command'
    except (KeyError, IndexError):
        return False


def return_recovered(message):
    text = message.get("text", "")
    split_text = text.split(" ")
    if len(split_text) > 0 and (split_text[0] == '/qa' or split_text[0] == '/ac'):
        recover_message = ' '.join(split_text[1:])
        return split_text[0], recover_message
    return "", ""


def auto_comp(text):
    res = openai.Completion.create(
        engine="davinci",
        prompt=text,
        max_tokens=50,
        temperature=0.9,
        stop="Q:"
    )
    opt = res['choices']
    if len(opt) > 0:
        opt = opt[0].get("text", "")
        return opt
    return ""


def open_ai_qa(text):

    prompt = """
    
    Q: What is human life expectancy in the United States?
    A: Human life expectancy in the United States is 78 years.

    Q: Who was president of the United States in 1955?
    A: Dwight D. Eisenhower was president of the United States in 1955.

    Q: What party did he belong to?
    A: He belonged to the Republican Party.

    Q: Who was president of the United States before George W. Bush?
    A: Bill Clinton was president of the United States before George W. Bush.

    Q: Who won the World Series in 1995?
    A: The Atlanta Braves won the World Series in 1995.
    
    """
    prompt += 'Q: ' + text.rstrip()+"\n"
    res = openai.Completion.create(
        engine="davinci",
        prompt=prompt,
        max_tokens=100,
        temperature=0,
        top_p=1,
        stop="Q:"
    )
    opt = res.get("choices", "")
    if len(opt) > 0:
        opt = opt[0]['text']
        return opt
    return ""


def local_host_run():
    api = "https://api.telegram.org/bot" + creds.bot_token + "/setWebHook?url=" + creds.ngrok
    r = requests.post(api)
    return r.ok


if __name__ == '__main__':
    success = True
    if run_local:
        success = local_host_run()
    if success:
        app.run(debug=False)
    else:
        logging.error("Could not post web-hook for localhost")
