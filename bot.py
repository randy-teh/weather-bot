import os
import telebot
import requests
import logging
from dotenv import load_dotenv
from geopy.geocoders import Nominatim

load_dotenv()

BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEATHER_TOKEN = os.environ.get('WEATHER_TOKEN')
POLLING_TIMEOUT = None
bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    '''
    returns a welcome message when the '/start' command is sent by the user
    '''
    bot.send_message(message.chat.id, f'Hello {message.from_user.first_name}, where are you interested in today?')


@bot.message_handler(commands=['weather'])
def send_weather(message):
    '''
    returns a prompt asking the user to enter a location when the '/weather' command is sent.
    registers the next step handler to wait for the user's input and calls the 'fetch_weather' function
    '''
    location = 'Where would you like to know about today?'
    sent_message = bot.send_message(message.chat.id, location, parse_mode='Markdown')
    bot.register_next_step_handler(sent_message, fetch_weather)
    return location


def location_handler(message):
    '''
    returns the latitude and longitude coordinated from user's message (location) using the Nominatim geocoder.
    if location is found - returns the rounded latitude and longitude
    else - returns Location not found
    '''
    location = message.text
    # Create a geocoder instance
    geolocator = Nominatim(user_agent="weather_app")

    try:
        # Get the latitude and longitude
        location_data = geolocator.geocode(location)
        latitude = round(location_data.latitude,2)
        longitude = round(location_data.longitude,2)
        # print(latitude, longitude)
        return latitude, longitude
    except AttributeError:
        print("Location not found.")


def get_weather(latitude,longitude):
    '''
    arguments - latitude, longitude
    takes in arguments as inputs and constructs URL to make API call to OpenWeatherMap API
    returns a response JSON after fetching weather data for the specified latitude and longitude
    '''
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={WEATHER_TOKEN}&units=metric"
    response = requests.get(url)
    #print(response.json())
    return response.json()

def change_humidity(humidity):
    if (humidity >= 70):
        return 'as bad as Singapore'
    elif (40 <= humidity < 70):
        return 'not bad'
    elif (humidity > 40):
        return 'low'

def fetch_weather(message): 
    '''
    called when the user provides location in response to the '/weather' command.
    uses the 'location_handler' function to get latitude & longitude of the provided location and 'get_weather' function to fetch the weather data
    extracts weather description from API response and sends to user as message.
    '''
    latitude, longitude = location_handler(message)
    response = get_weather(latitude,longitude)
    description = response['weather'][0]['description']
    temperatures = response['main']
    wind = response['wind']
    humidity = change_humidity(temperatures['humidity'])
    
    weather_message = f'''*{message.text.title()} weather*:
    Generally, {description}
    Current temperature, {temperatures['temp']} degrees but it feels like {temperatures['feels_like']} degrees
    Today is a minimum of {temperatures['temp_min']} degrees and a maximum of {temperatures['temp_max']} degrees
    Humidity is {humidity} today at {temperatures['humidity']}%
    '''
    # weather_message = f'*{message.text} weather*: \n {description}\n Current temperature: {temperatures['temp']} degrees \n'
    bot.send_message(message.chat.id, 'Here\'s the weather!')
    bot.send_message(message.chat.id, weather_message, parse_mode='Markdown')

@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    '''
    echoes back any other messages bot receives from user
    '''
    default_message = f'''
    Hi! This is a bot that returns the weather of a given location.
To start, type in /weather and reply the bot with any location!
Any other message will echo this message back over and over again, {message.from_user.first_name}, so don't be silly.
    '''
    bot.reply_to(message, default_message)

bot.infinity_polling()