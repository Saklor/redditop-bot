"""
Redditop Bot v1.0
This bot's purpose is to give an inline method of seeing and
sharing the week's top submissions from reddit.
"""
#moya pt
#Standard imports
import sys
# import os
import json
# import urlparse
# import urllib
import signal
#Unused:
# import string

#Non Standard Imports
import praw
import requests
# from bs4 import BeautifulSoup

# REQUEST_URL formatting
if len(sys.argv) == 1:
    print 'Usage: redditop_bot.py [TOKEN_FILE]'
    sys.exit()
TOKEN_FILE = open(sys.argv[1], 'r')
REQUEST_URL = "https://api.telegram.org/bot" + TOKEN_FILE.read()
TOKEN_FILE.close()

print REQUEST_URL

# Paths
IMAGE_PATH = 'out.jpg'
GIF_PATH = 'out.gif'

# Reddit PRAW initialization
UA = "Linux:redditop.telegram:v1.0 (by /u/genericargentine)"
REDDIT = praw.Reddit(user_agent=UA)

def main():
    """Main update loop"""
    # Request inicial para limpiar pedidos colgados mientras estuvo apagado el bot.
    last_update_id = 0
    update_request = requests.get(REQUEST_URL + '/getUpdates', params={'timeout' : 0})
    data = json.loads(update_request.text)

    if data['ok'] and data['result'] != []:
        last_update_id = data['result'][-1]['update_id'] + 1

    while True:
        update_request = requests.get(
            REQUEST_URL + '/getUpdates',
            params={'offset' : last_update_id, 'timeout' : 120})

        data = json.loads(update_request.text)

        if data['ok'] and data['result'] != []:
            result = data['result'][0]
            update_id = result['update_id']

            if 'message' in result and 'text' in result['message']:
                message = result['message']
                # print update_id
                print message['text']

                # Deprecated
                # if '/quesoy' in message['text'].lower():
                #     que_soy(message)

                if '/dametop' in message['text'].lower():
                    dame_top(message)
            elif 'inline_query' in result:
                # print update_id
                print result['inline_query']['query']
                procesar_inline_query(result['inline_query'])
            else:
                print 'Unknown update!'

            last_update_id = update_id+1
        elif not data['ok']:
            # Untested!
            print 'Invalid answer sent!'
            print 'Error code: ' + str(data['error_code'])
            print 'Description: ' + data['description']
        else:
            # Timeout, nada que hacer
            pass

# Unused
# def add_params(url, params):
#     url_parts = list(urlparse.urlparse(url))
#     query = dict(urlparse.parse_qsl(url_parts[4]))
#     query.update(params)

#     url_parts[4] = urllib.urlencode(query)

#     return  urlparse.urlunparse(url_parts)

# Deprecated
# def que_soy(message):
#     """Maneja la respuesta al comando /queSoy"""
#     text = message['from']['first_name'] + '? Quien te conoce papa?'
#     chat_id = message['chat']['id']
#     if message['from']['first_name'] == 'Matias':
#         text = 'Tu nombre es Matias, asi que me parece que sos mi creador. Bien ahi!'
#     bot_send_msg(chat_id, text)

def bot_send_msg(chat_id, text):
    """Realiza un POST al chat_id indicado con el mensaje text"""
    requests.post(
        REQUEST_URL + '/sendMessage',
        data={'chat_id' : chat_id, 'text' : text})

def dame_top(message):
    """
    Handling del comando /dametop
    Envia el top weekly post del subreddit indicado por el primer parametro
    """
    text = message['text']
    text_split = text.split(' ')
    chat_id = message['chat']['id']
    link_url = ''
    submission_info = ''


    if len(text_split) >= 2:
        requested_subreddit = text_split[1]
        try:
            subreddit = REDDIT.get_subreddit(requested_subreddit, fetch=True)
        except praw.errors.HTTPException as http_exception:
            print 'NaS - ' + str(http_exception)
            bot_send_msg(chat_id, 'No existe ese subreddit aparentemente. ' + str(http_exception))
            return

        for submission in subreddit.get_top_from_week(limit=1):
            link_url = submission.url
            submission_info = '\'' + submission.title + '\'' \
                            + ' by ' + str(submission.author) \
                            + ' (' + str(submission.score) + ')'

        # Dejo esto comentado, pero ahora manda unicamente el submission_info + link
        # if 'imgur' in link_url and 'gif' not in link_url and '/a/' not in link_url:
        #     url_parts = list(urlparse.urlparse(link_url))
        #     if 'i.' not in url_parts[1]:
        #         url_parts[1] = "i." + url_parts[1]
        #         url_parts[2] = url_parts[2] + ".jpg"
        #         link_url = urlparse.urlunparse(url_parts)

        #     # Guardo la imagen
        #     save_image(link_url)

        #     # Envio
        #     files = {'photo': (IMAGE_PATH, open(IMAGE_PATH, "rb"))}
        #     requests.post(
        #         REQUEST_URL + '/sendPhoto',
        #         data={'chat_id' : chat_id, 'caption' : submission_info},
        #         files=files)

        #     # Delete al archivo
        #     os.remove(IMAGE_PATH)

        # elif '.gif' in link_url or 'gfycat' in link_url:
        #     bot_send_msg(chat_id, 'Un gif! ' + submission_info + '  ' + link_url)
        # else:
        bot_send_msg(chat_id, submission_info + '  ' + link_url)
    else:
        bot_send_msg(chat_id, 'Me tenes que pasar un subreddit troesma.')

# Unused
# def save_image(img_url):
#     image = open(IMAGE_PATH, 'wb')
#     image.write(urllib.urlopen(img_url).read())
#     image.close()
#
# def save_gif(gif_url):
#     url_gif = urllib2.urlopen(gif_url)
#     gif = open(GIF_PATH, 'w+')
#     gif.write(url_gif.read())
#     gif.close()

def procesar_inline_query(inline_query):
    """
    Handling de los inline querys.
    Envia como respuesta los 15 mejores tops de la semana del subreddit
    indicado, con thumnail segun corresponda.
    """
    query = inline_query['query']
    query_id = inline_query['id']
    if query != '' and query[-1] != '_':
        try:
            subreddit = REDDIT.get_subreddit(query, fetch=True)
        except praw.errors.HTTPException as http_exception:
            print 'NaS - ' + str(http_exception)
            return
        except praw.errors.InvalidSubreddit as invalid_subreddit_exception:
            print 'Invalid subreddit - ' + str(invalid_subreddit_exception)
            return
        except:
            print 'UNKNOWN EXCEPTION OCURRED AT INLINE_QUERY'
            return

        data = []
        i = 1
        for submission in subreddit.get_top_from_week(limit=15):
            inline_query_result = {}
            submission_info = '\'' + submission.title + '\'' \
                            + ' by ' + str(submission.author) \
                            + ' (' + str(submission.score) + ')'
            inline_query_result['type'] = 'article'
            inline_query_result['id'] = str(i)
            i += 1
            inline_query_result['title'] = submission.title
            inline_query_result['input_message_content'] = \
                {'message_text' : submission_info + ' ' + submission.url}
            if not submission.is_self \
                and str(submission.thumbnail) != 'self' \
                and str(submission.thumbnail) != 'nsfw' \
                and str(submission.thumbnail) != 'default':
                inline_query_result['thumb_url'] = str(submission.thumbnail)
            data.append(inline_query_result)

        response = requests.post(
            REQUEST_URL + '/answerInlineQuery',
            params={'inline_query_id' : query_id, 'results' : json.dumps(data)})
        response_json = json.loads(response.text)
        if not response_json['ok']:
            print 'Invalid answer sent!'
            print 'Error code: ' + str(response_json['error_code'])
            print 'Description: ' + response_json['description']
            if 'THUMB_URL_INVALID' in response_json['description']:
                for answer in data:
                    if 'thumb_url' in answer:
                        print 'thumb_url: ' + answer['thumb_url']

    elif query == '':
        pass
        #TODO : Trending subreddits?

def signal_handler(sign, frame):
    """
    Manejo del SIGINT para salir de una manera no catastrofica.
    """
    print 'Signal: ' + str(sign)
    print 'Frame : ' + str(frame)
    print 'Ctrl+C pressed. Exiting.'
    sys.exit(0)

#Catch SIGINT using signal_handler
signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    main()
