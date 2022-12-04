import os
import argparse
from urllib.parse import urljoin
import logging
import imghdr

from PIL import Image
from bs4 import BeautifulSoup
import requests
from get_tweepy import get_api
from tweepy import Cursor
from selenium.webdriver import Chrome


def get_imgs(screen_name):
    url = 'http://p.twipple.jp/user/' + screen_name
    imgs = []
    while True:
        r = requests.get(url)
        s = BeautifulSoup(r.text, 'lxml')
        new = [img_tag['src'].replace('/large/', '/orig/')
               for img_tag in s.select('.simple_list_photo img')]
        imgs.extend(new)

        # Check if there exists next page
        next_links = [a for a in s.select('a') if a.text == 'next']
        if next_links:
            next_url = next_links[0]['href']
            url = urljoin(url, next_url)
        else:
            break
    return imgs


def get_followers(sn=''):
    '''Return a following users list'''
    return [u for u in Cursor(api.friends, screen_name=sn, count=200).items()]


def print_friends_photo_nums():
    us = get_followers()
    for u in us:
        imgs = get_imgs(u.screen_name)
        if imgs:
            print(len(imgs), u.name, 'http://p.twipple.jp/user/' + u.screen_name)


def download_images():
    us = get_followers('aobajo')
    for u in us:
        logger.info('User: {}(@{})'.format(u.name, u.screen_name))
        imgs = get_imgs(u.screen_name)
        for i, img in enumerate(imgs, 1):
            logger.info('Saving: [{:02d}] {}'.format(i, img))
            save_img(img, u)


def save_img(img, user):
    # Make directory if not exists
    directory = 'imgs/' + user.screen_name
    if not os.path.exists(directory):
        os.mkdir(directory)

    # Make symlink
    link = 'imgs/{}(@{})'.format(user.name.replace('/', '-'), user.screen_name)
    if not os.path.exists(link):
        os.symlink(user.screen_name, link)

    r = requests.get(img)
    ext = Image.open(Image.io.BytesIO(r.content)).format.lower()
    filename = os.path.join(directory, os.path.basename(img)) + '.' + ext
    with open(filename, 'wb') as f:
        f.write(r.content)


def print_tweet_urls(screen_name):
    imgs = get_imgs(screen_name)
    for img in imgs:
        twipple_id = img['src'].split('/')[-1]
        url = 'https://twitter.com/search?q=' + 'from:{} p.twipple.jp/{}'.format(
            screen_name, twipple_id)
        br.get(url)
        s = BeautifulSoup(br.page_source, 'lxml')
        t = s.select('.time a')
        if t:
            id = t[0]['data-conversation-id']
            print('https://twitter.com/t_arts_pretty/status/' + id)
        else:
            print(br.current_url)


if __name__ == '__main__':
    SCREEN_NAME = 'sakuramochi_0'
    api = get_api(SCREEN_NAME)
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=[
        'print_friends_photo_nums',
        'download_images',
        'print_tweet_urls',
    ])
    parser.add_argument('--screen_name')
    args = parser.parse_args()
    if args.command == 'print_friends_photo_nums':
        print_friends_photo_nums()
    elif args.command == 'download_images':
        download_images()
    elif args.command == 'print_tweet_urls':
        br = Chrome()
        print_tweet_urls(args.screen_name)
