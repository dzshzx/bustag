from bottle import route, run, template, static_file, request, response, redirect
import bottle
import os
import sys
from collections import defaultdict
from bustag.spider.db import get_items, RATE_TYPE, RATE_VALUE, ItemRate, Item
import bustag.model.classifier as clf
from bustag.util import logger
dirname = os.path.dirname(os.path.realpath(__file__))
bottle.TEMPLATE_PATH.insert(0, dirname+'/views/')


@route('/static/<filepath:path>')
def send_static(filepath):
    return static_file(filepath, root=dirname+'/static/')


@route('/')
def index():
    rate_type = RATE_TYPE.SYSTEM_RATE.value
    rate_value = int(request.query.get('like', RATE_VALUE.LIKE.value))
    page = int(request.query.get('page', 1))
    items, page_info = get_items(
        rate_type=rate_type, rate_value=rate_value, page=page)
    for item in items:
        Item.get_tags_dict(item)
    return template('index', items=items, page_info=page_info, like=rate_value, path=request.path)


@route('/tagit')
def tagit():
    rate_value = request.query.get('like', None)
    rate_value = None if rate_value == 'None' else rate_value
    rate_type = None
    if rate_value:
        rate_value = int(rate_value)
        rate_type = RATE_TYPE.USER_RATE
    page = int(request.query.get('page', 1))
    items, page_info = get_items(
        rate_type=rate_type, rate_value=rate_value, page=page)
    for item in items:
        Item.get_tags_dict(item)
    return template('tagit', items=items, page_info=page_info, like=rate_value, path=request.path)


@route('/tag/<id:int>', method='POST')
def tag(id):
    if request.POST.submit:
        item_rate = ItemRate.get_by_itemid(id)
        rate_value = request.POST.submit
        if not item_rate:
            rate_type = RATE_TYPE.USER_RATE
            item = Item.getit(id)
            ItemRate.saveit(rate_type, rate_value, item)
            logger.debug(f'add new item_rate for id:{id}')
        else:
            item_rate.rate_value = rate_value
            item_rate.save()
            logger.debug(f'updated item_rate for id:{id}')
    page = int(request.query.get('page', 1))
    like = request.query.get('like')
    url = f'/tagit?page={page}&like={like}'
    print(url)
    redirect(url)


@route('/correct/<id:int>', method='POST')
def correct(id):
    if request.POST.submit:
        is_correct = int(request.POST.submit)
        item_rate = ItemRate.get_by_itemid(id)
        if item_rate:
            item_rate.rate_type = RATE_TYPE.USER_RATE
            if not is_correct:
                rate_value = item_rate.rate_value
                rate_value = 1 if rate_value == 0 else 0
                item_rate.rate_value = rate_value
            item_rate.save()
            logger.debug(
                f'updated item_id: {id}, {"and correct the rate_value" if not is_correct else ""}')
    page = int(request.query.get('page', 1))
    like = int(request.query.get('like', 1))
    url = f'/?page={page}&like={like}'
    print(url)
    redirect(url)


@route('/other')
def other_settings():
    try:
        _, model_scores = clf.load()
    except FileNotFoundError:
        model_scores = None
    return template('other', path=request.path, model_scores=model_scores)


@route('/do-training')
def do_training():
    error_msg = None
    model_scores = None
    try:
        _, model_scores = clf.train()
    except ValueError as ex:
        error_msg = ' '.join(ex.args)
    return template('other', path=request.path, model_scores=model_scores, error_msg=error_msg)


app = bottle.default_app()

if __name__ == "__main__":
    # run(host='0.0.0.0', port=8080, server='gunicorn')
    run(host='0.0.0.0', port=8080, debug=True, reloader=True)
