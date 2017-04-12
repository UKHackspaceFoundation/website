from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import telegram
import json, datetime
import sys
from django.conf import settings

@csrf_exempt
@require_POST
def hook(request):

    try:
        jsondata = request.body.decode('utf-8')
        body = json.loads(jsondata)

        bot = telegram.Bot(token= getattr(settings, "TELEGRAM_BOT_TOKEN", None) )

        msg = ""

        if request.META['HTTP_X_DISCOURSE_EVENT_TYPE'] == 'topic' and body['topic']['archetype'] == 'regular':
            url = request.META['HTTP_X_DISCOURSE_INSTANCE'] + '/t/' + body['topic']['slug']
            msg = "Forum: [" + request.META['HTTP_X_DISCOURSE_EVENT']
            msg += ' by ' + body['user']['name']
            msg += ' in ' + body['topic']['title']
            msg += ']('+ url +')'

        else:
            url = request.META['HTTP_X_DISCOURSE_INSTANCE'] + '/t/' + body['topic']['slug'] + '/' + str(body['topic']['id']) + '/' + str(body['topic']['posts_count'])
            msg = "Forum: [" + request.META['HTTP_X_DISCOURSE_EVENT']
            msg += ' by ' + body['post']['name']
            msg += ' in ' + body['topic']['title']
            msg += ']('+ url +')'

        bot.sendMessage(chat_id=getattr(settings, "TELEGRAM_BOT_CHAT_ID", None), text=msg, parse_mode=telegram.ParseMode.MARKDOWN)

        return HttpResponse(status=200)
    except Exception as e:
        msg = "Error: " + str(e)
        return HttpResponse(msg, status=500)
