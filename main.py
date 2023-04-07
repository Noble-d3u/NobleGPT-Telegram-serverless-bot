import logging
import os

import boto3
import openai

from utils import Standard_messages as STD_MSG

# TOKEN = os.environ["TELEGRAM_TOKEN"]
REGION_NAME = os.environ["REGION_NAME"]
TABLE_NAME = os.environ["TABLE_NAME"]
log = logging.getLogger("main-log")
log.setLevel(logging.DEBUG)


class Database:
    def __init__(self, keys=None) -> None:
        if keys:
            pass
        else:
            db = boto3.resource(
                "dynamodb",
                region_name=REGION_NAME,
            )
        self._db = db
        self.table = db.Table(TABLE_NAME)

    def get_key(self, id):
        response = self.table.get_item(Key={"Chat_ID": str(id)})
        key = response["Item"].get("Key", None)
        return key

    def set_key(self, id, key):
        self.table.put_item(
            Item={
                "Chat_ID": str(id),
                "Key": str(key),
            }
        )


class Message:
    message_id: str
    date: str
    text: str
    chat_id: str
    first_name: str
    last_name: str
    username: str
    chat_type: str
    has_reply: bool = False

    def __init__(self, message: dict[dict, dict]) -> None:
        if not isinstance(message, dict):
            raise Exception("message is not a dict")
        self.message_id = message.get("message_id", None)
        self.date = message.get("date", None)
        self.text = message.get("text", None)
        __chat__ = message.get("chat", None)
        if not __chat__:
            raise Exception("no chat in message")
        self.chat_id = __chat__.get("id", None)
        self.first_name = __chat__.get("first_name", None)
        self.last_name = __chat__.get("last_name", None)
        self.username = __chat__.get("username", None)
        self.chat_type = __chat__.get("type", None)
        self.__from__ = message.get("from", None)
        self.__chat__ = __chat__
        self.__reply__ = __reply__ = message.get("reply_to_message", None)
        if __reply__:
            self.has_reply = True
            self.reply = Message(__reply__)


def main(event, context):
    log.info("Event:" + str(event))
    payload = {"statusCode": 500}
    if not isinstance(event, dict):
        return payload  # Internal Server Error
    event_message = event.get("message", None)
    event_update_id = event.get("update_id", None)
    if not event_message or not event_update_id:
        log.info("No message or update id found")
        return payload  # Internal Server Error
    msg = Message(event_message)
    msg_text = msg.text
    if msg_text == "/start":
        payload = {
            "statusCode": 200,
            "method": "sendMessage",
            "chat_id": msg.chat_id,
            "text": STD_MSG["welcome"],
        }
    elif msg_text == "/set_key":
        payload = {
            "statusCode": 200,
            "method": "sendMessage",
            "chat_id": msg.chat_id,
            "text": STD_MSG["set_key"],
            "reply_markup": {
                "method": "ForceReply",
                "force_reply": True,
            },
        }
    elif msg.has_reply == True:
        if msg.reply.text == STD_MSG["set_key"]:
            try:
                Database().set_key(msg.chat_id, msg_text)
                openai.api_key = msg_text
                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Hello world!"}]
                )
                reply = completion["choices"][0]["message"]["content"].strip()
            except Exception as e:
                payload = {
                    "statusCode": 200,
                    "method": "sendMessage",
                    "chat_id": msg.chat_id,
                    "text": str(e),
                }
            else:
                payload = {
                    "statusCode": 200,
                    "method": "sendMessage",
                    "chat_id": msg.chat_id,
                    "text": str(reply),
                }
    else:
        key = Database().get_key(msg.chat_id)
        if not key:
            payload = {
                "statusCode": 200,
                "method": "sendMessage",
                "chat_id": msg.chat_id,
                "text": STD_MSG["not_config"],
            }
            return payload
        try:
            openai.api_key = key
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=[{"role": "user", "content": msg_text}]
            )
            reply = completion["choices"][0]["message"]["content"].strip()
        except Exception as e:
            payload = {
                "statusCode": 200,
                "method": "sendMessage",
                "chat_id": msg.chat_id,
                "text": str(e),
            }
        else:
            payload = {
                "statusCode": 200,
                "method": "sendMessage",
                "chat_id": msg.chat_id,
                "text": str(reply),
            }
    return payload


if __name__ == "__main__":
    main(None, None)
