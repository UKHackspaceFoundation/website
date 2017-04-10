from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import telegram
import json, datetime
import sys

@csrf_exempt
@require_POST
def hook(request):

    try:
        jsondata = request.body.decode('utf-8')
        body = json.loads(jsondata)

        bot = telegram.Bot(token='360648398:AAG-vPZv-0GwPkqRkIs3sVogfM4M3wKxkFg')

        url = request.META['HTTP_X_DISCOURSE_INSTANCE'] + '/t/' + body['topic']['slug'] + '/' + str(body['topic']['id']) + '/' + str(body['topic']['posts_count'])
        msg = "Forum: [" + request.META['HTTP_X_DISCOURSE_EVENT']
        msg += ' by ' + body['post']['name']
        msg += ' in ' + body['topic']['title']
        msg += ']('+ url +')'

        bot.sendMessage(chat_id=-150366976, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)

        return HttpResponse(status=200)
    except Exception as e:
        msg = "Error: " + str(e)
        return HttpResponse(msg, status=500)
