"""
Redditop Bot v1.0.

This bot's purpose is to give an inline method of seeing and
sharing the week's top submissions from reddit.
"""

# Standard imports
import json
import signal
import sys

# Non Standard Imports
import praw

import requests

# REQUEST_URL formatting
if len(sys.argv) < 4:
    print ('Usage: redditop_bot.py [TOKEN_FILE] [CLIENT_ID_FILE] [CLIENT_SECRET_FILE]')
    sys.exit()
TOKEN_FILE = open(sys.argv[1], 'r')
REQUEST_URL = "https://api.telegram.org/bot" + TOKEN_FILE.read().rstrip('\n')
TOKEN_FILE.close()

print (REQUEST_URL)

# Reddit PRAW initialization
CLIENT_ID_FILE = open(sys.argv[2], 'r')
CLIENT_SECRET_FILE = open(sys.argv[3], 'r')
UA = "Linux:redditop.telegram:v1.0 (by /u/genericargentine)"
REDDIT = praw.Reddit(client_id=CLIENT_ID_FILE.read().rstrip('\n'),
                     client_secret=CLIENT_SECRET_FILE.read().rstrip('\n'),
                     user_agent=UA)
CLIENT_SECRET_FILE.close()
CLIENT_ID_FILE.close()


def main():
    """Main update loop."""
    # Request inicial para limpiar pedidos colgados mientras estuvo apagado el bot.
    last_update_id = 0
    validjson = True
    update_request = requests.get(
        REQUEST_URL + '/getUpdates',
        params={'timeout': 0})

    try:
        data = json.loads(update_request.text)
    except json.decoder.JSONDecodeError:
        print ("Invalid JSON Object.")
        validjson = False
    else:
        validjson = True

    if validjson and data['ok'] and data['result'] != []:
        last_update_id = data['result'][-1]['update_id'] + 1

    while True:
        update_request = requests.get(
            REQUEST_URL + '/getUpdates',
            params={
                'offset': last_update_id,
                'timeout': 3600,
                'allowed_updates' : ['message', 'inline_query']
            })

        try:
            data = json.loads(update_request.text)
        except json.decoder.JSONDecodeError:
            print ("Invalid JSON Object.")
            validjson = False
        else:
            validjson = True

        if not validjson:
            print ("Invalid JSON")
        elif data['ok'] and data['result'] != []:
            result = data['result'][0]
            update_id = result['update_id']

            if 'message' in result and 'text' in result['message']:
                message = result['message']
                try:
                    print (message['text'])
                except:
                    print ("Invalid message text")

                if '/dametop' in message['text'].lower():
                    handle_dame_top(message)
            elif 'inline_query' in result:
                print (result['inline_query']['query'])
                handle_inline_query(result['inline_query'])
            else:
                print ('Unknown update!')

            last_update_id = update_id + 1
        elif not data['ok']:
            # Untested!
            print ('Invalid answer sent!')
            print ('Error code: ' + str(data['error_code']))
            print ('Description: ' + data['description'])
        else:
            # Timeout, nada que hacer
            pass


def bot_send_msg(chat_id, text):
    """Realiza un POST al chat_id indicado con el mensaje text."""
    requests.post(
        REQUEST_URL + '/sendMessage',
        data={'chat_id': chat_id, 'text': text})


def fetch_subreddit(query):
    subreddit = None
    try:
        subreddit = REDDIT.subreddit(query)
    except praw.exceptions.APIException as api_exception:
        print ('API Exception - ' + str(api_exception))
    except praw.exceptions.ClientException as client_exception:
        print ('Client Exception - ' + str(client_exception))
    except:
        print ('Unknown exception when fetching ' + str(query))
    return subreddit


def fetch_submissions(subreddit, lim=1):
    submissions = []
    try:
        submissions = subreddit.top('week', limit=lim)
    except praw.exceptions.APIException as api_exception:
        print ('API Exception - ' + str(api_exception))
    except praw.exceptions.ClientException as client_exception:
        print ('Client Exception - ' + str(client_exception))
    except:
        print ('Unknown exception when fetching submissions from subreddit ' + str(subreddit.display_name))

    try:
        submissions = [subm for subm in submissions]
    except:
        submissions = []
        print ('Exception parsing submissions from subreddit ' + str(subreddit.display_name))

    return submissions


def get_inline_list_from_subreddit(subreddit):
    data = []
    i = 1
    submissions = fetch_submissions(subreddit, 15)
    for submission in submissions:
        inline_query_result = {}
        submission_info = '\'' + submission.title + '\'' +\
                ' by ' + str(submission.author) +\
                ' (' + str(submission.score) + ')'
        inline_query_result['type'] = 'article'
        inline_query_result['id'] = str(i)
        i += 1
        inline_query_result['title'] = submission.title
        inline_query_result['input_message_content'] = \
            {'message_text': submission_info + '  ' + submission.url}
        if not submission.is_self \
            and str(submission.thumbnail) != 'self' \
            and str(submission.thumbnail) != 'nsfw' \
                and str(submission.thumbnail) != 'default':
            inline_query_result['thumb_url'] = str(submission.thumbnail)
        data.append(inline_query_result)

    return data


def handle_dame_top(message):
    """
    Handling del comando /dametop.

    Envia el top weekly post del subreddit indicado por el primer parametro
    """
    text = message['text']
    text_split = text.split(' ')
    chat_id = message['chat']['id']
    link_url = ''
    submission_info = ''

    if len(text_split) >= 2:
        requested_subreddit = text_split[1]
        subreddit = fetch_subreddit(requested_subreddit)
        if subreddit is None:
            return

        submissions = fetch_submissions(subreddit)
        for submission in submissions:
            link_url = submission.url
            submission_info = '\'' + submission.title + '\'' +\
                ' by ' + str(submission.author) +\
                ' (' + str(submission.score) + ')'
        
        if submission_info == '':
            bot_send_msg(chat_id, 'No encontre nada interesante')
        else:
            bot_send_msg(chat_id, submission_info + '  ' + link_url)
    else:
        bot_send_msg(chat_id, 'Me tenes que pasar un subreddit troesma.')


def handle_inline_query(inline_query):
    """
    Handling de los inline querys.

    Envia como respuesta los 15 mejores tops de la semana del subreddit
    indicado, con thumbnail segun corresponda.
    """
    query = inline_query['query']
    query_id = inline_query['id']
    if query != '' and query[-1] != '_':
        subreddit = fetch_subreddit(query)
        if subreddit is None:
            return
    elif query == '':
        subreddit = fetch_subreddit('all')
        if subreddit is None:
            return
    else:
        print ('Subreddit invalido.')
        return

    data = get_inline_list_from_subreddit(subreddit)

    response = requests.post(
        REQUEST_URL + '/answerInlineQuery',
        params={'inline_query_id': query_id, 'results': json.dumps(data)})
    response_json = json.loads(response.text)

    if not response_json['ok']:
        print ('Invalid answer sent!')
        print ('Error code: ' + str(response_json['error_code']))
        print ('Description: ' + response_json['description'])
        if 'THUMB_URL_INVALID' in response_json['description']:
            for answer in data:
                if 'thumb_url' in answer:
                    print ('thumb_url: ' + answer['thumb_url'])


def signal_handler(sign, frame):
    """Manejo del SIGINT para salir de una manera no catastrofica."""
    print ('Signal: ' + str(sign))
    print ('Frame : ' + str(frame))
    print ('Ctrl+C pressed. Exiting.')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    main()
