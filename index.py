import os
import re
from flask import Flask, jsonify, request, abort, Response
from flask_pymongo import PyMongo
from pymongo import ReturnDocument
import telebot
from dotenv import load_dotenv
from bson.json_util import dumps
from json import loads

load_dotenv()

app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_CONNECT_STRING")
mongo = PyMongo(app)

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"), threaded=False)

@bot.message_handler(commands=['hi'])
def send_welcome(message):
	bot.reply_to(message, "Howdy, how are you doing?")

@bot.message_handler(commands=["sir"])
def set_up_venv(message):
  body = """
when creating a new workspace
```
python -m venv venv
```

activate the venv
```
# windows
. venv/Scripts/activate 

# macOS/linux
. venv/bin/activate 
```

installing fastAPI and motor
```
pip install fastapi uvicorn motor python-dotenv
```

create a requirements.txt
```
pip freeze > requiremtnts.txt
```

start your server application
```
uvicorn app:app --reload
```

stop the server application
```
ctrl+c
```
  """
  bot.reply_to(message, body, parse_mode='Markdown')
def getNextSequence(name):
  ret = mongo.db.counters.find_one_and_update(
    {'_id': name},
    {'$inc': {'seq': 1}},
    return_document=ReturnDocument.AFTER
  )
  return ret["seq"]

ADD_REGEX=r"^\/(led)\s(add)\s(\w+)"
@bot.message_handler(regexp=ADD_REGEX)
def add_led(message):
  m = re.search(ADD_REGEX, message.text)
  led_name = m.group(3)
  user_name = message.from_user.first_name if message.from_user.first_name else message.from_user.first_name
  user_id = message.from_user.id

  led = mongo.db.leds.find_one({"creator.tele_id": user_id})
  if not led == None:
    bot.reply_to(message, f"you've already adopted an LED")
    return

  mongo.db.leds.insert_one(
    {
      "name": led_name,
      "colour": [255,255,255],
      "position": getNextSequence("position"),
      "state": 1,
      "creator": {
        "tele_id": user_id,
        "tele_name": user_name
      }
    }
  )
  bot.reply_to(message, f"{user_name} adopted an LED. Its name is \"{led_name}\"")
 
#! STATE
TOGGLE_REGEX=r"^\/(led)\s(state)\s(\w+)"
@bot.message_handler(regexp=TOGGLE_REGEX)
def toggle_led(message):
  m = re.search(TOGGLE_REGEX, message.text)
  desired_state = m.group(3)
  state_options = {
    "on": 1,
    "off": 2,
    "blink": 3
  }
  if not desired_state in state_options:
    bot.reply_to(message, f"try \"on\", \"off\" or \"blink\"")
    return

  user_id = message.from_user.id
  led = mongo.db.leds.find_one_and_update({"creator.tele_id": user_id}, {"$set": {"state": state_options[desired_state]}}, return_document=ReturnDocument.AFTER)

  if led == None:
    bot.reply_to(message, f"you sure you have an LED?")
    return
  
  bot.reply_to(message, f"your LED, {led['name']}, should be {desired_state} now")


NAME_REGEX=r"^\/(led)\s(name)\s(\w+)"
@bot.message_handler(regexp=NAME_REGEX)
def name_led(message):
  m = re.search(NAME_REGEX, message.text)
  desired_name = m.group(3)

  user_id = message.from_user.id
  led = mongo.db.leds.find_one_and_update({"creator.tele_id": user_id}, {"$set": {"name": desired_name}}, return_document=ReturnDocument.AFTER)

  if led == None:
    bot.reply_to(message, f"you sure you have an LED?")
    return
  
  bot.reply_to(message, f"your LED's name is now \"{led['name']}\"")

#! COLOUR
COLOUR_REGEX=r"^\/(led)\s(colour)\s(#(?:[0-9a-fA-F]{3}){1,2}$)"
@bot.message_handler(regexp=COLOUR_REGEX)
def colour_led(message):
  m = re.search(COLOUR_REGEX, message.text)
  desired_colour = m.group(3)

  desired_colour_hex = desired_colour.lstrip('#')
  hex_len = len(desired_colour_hex)
  step = int(hex_len/3)
  rgb = [int(desired_colour_hex[i:i+step], 16) for i in range(0, hex_len, step)]

  user_id = message.from_user.id
  led = mongo.db.leds.find_one_and_update({"creator.tele_id": user_id}, {"$set": {"colour": rgb}}, return_document=ReturnDocument.AFTER)

  if led == None:
    bot.reply_to(message, f"you sure you have an LED?")
    return
  
  bot.reply_to(message, f"your LED, {led['name']}, should be coloured {desired_colour} now")

ALL_REGEX = r"^\/(led)\s(all)"
@bot.message_handler(regexp=ALL_REGEX)
def led_toggle(message): 
  all_leds = mongo.db.leds.find({}).sort("position")
  all_led_names = "\n".join([str(l["position"]) +". "+ l["name"] for l in all_leds])
  bot.reply_to(message, f"here's a list of all the LEDs\n\n{all_led_names}")


@app.route('/api', methods=['POST'])
def api():
  if request.headers.get('content-type') == 'application/json':
      json_string = request.get_data().decode('utf-8')
      print(json_string)
      update = telebot.types.Update.de_json(json_string)
      bot.process_new_updates([update])
      return ''
  else:
      abort(403)

@app.route('/embed/leds', methods=['GET'])
def embed_get_leds():
  leds = mongo.db.leds.find({},{"position": 1, "colour": 1, "state": 1, "_id": 0}).sort("position")
  leds_list = loads(dumps(leds))
  return jsonify(leds_list)

@app.route("/deep", methods=["GET"])
def deep():
  return Response({"a": "b"}, status=204)

if (__name__ == "__main__") and (os.getenv("ENVIRONMENT") == "dev"):
  # app.run(debug=True, port=4010, host="0.0.0.0")
  bot.infinity_polling()
