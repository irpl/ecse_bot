import os
import re
from flask import Flask, jsonify, request, abort
from flask_pymongo import PyMongo
import telebot
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_CONNECT_STRING")
mongo = PyMongo(app)

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"), threaded=False)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Howdy, how are you doing?")

@bot.message_handler(regexp=r"^\/(led)\s?(\w+)")
def led_toggle(message):
  m = re.search(r"^\/(led)\s?(\w+)", message.text)
  led_name = m.group(2)
  if led_name == "all":
    all_leds = mongo.db.leds.find({}).sort("position")
    all_led_names = "\n".join([str(l["position"]) +". "+ l["name"] for l in all_leds])
    bot.reply_to(message, f"here's a list of all the LEDs\n\n{all_led_names}")
    return
  bot.reply_to(message, f"attempting to toggle LED {led_name}")
  led = mongo.db.leds.find_one({"name": led_name})
  if led == None:
    bot.reply_to(message, f"there's no led called {led_name}. ask phillip to add it.")
    return
  current_state = led["state"]
  mongo.db.leds.update_one({"name": led_name}, {"$set": { "state": not current_state}})
  updated_led = mongo.db.leds.find_one({"name": led_name})
  if (not current_state) == updated_led["state"]:
    bot.reply_to(message, f"led {led_name} should toggle now.")
  else:
    bot.reply_to(message, "something might have gone wrong. tell phillip")


@app.route('/api', methods=['POST'])
def api():
  print("test")
  if request.headers.get('content-type') == 'application/json':
      json_string = request.get_data().decode('utf-8')
      print(json_string)
      update = telebot.types.Update.de_json(json_string)
      bot.process_new_updates([update])
      return ''
  else:
      abort(403)


if (__name__ == "__main__") and (os.getenv("ENVIRONMENT") == "dev"):
  # app.run(debug=True, port=4010, host="0.0.0.0")
  bot.infinity_polling()
