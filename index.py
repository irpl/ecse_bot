import os
import re
from flask import Flask, jsonify, request, abort
import telebot
# from dotenv import load_dotenv

# load_dotenv()
app = Flask(__name__)

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"), threaded=False)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Howdy, how are you doing?")

@bot.message_handler(regexp=r"^\/(led)\s?(\d+)+")
def led_toggle(message):
  m = re.search(r"^\/(led)\s?(\d+)+", message.text)
  led = m.group(2)
  bot.reply_to(message, f"Attempting to toggle LED #{led}")

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
