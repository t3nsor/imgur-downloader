#!/usr/bin/env python3

import os.path
import re
import requests
import sys

def classify(url):
    match = re.fullmatch('https?://[^/]*imgur\.com/([a-zA-Z0-9]+\.(jpg|jpeg|png|webm|mp4))', url)
    if match:
        return ('direct', match.group(1))

    match = re.fullmatch('https?://[^/]*imgur\.com/([a-zA-Z0-9]+)\.(gif|gifv)', url)
    if match:
        return ('gif', match.group(1))

    match = re.fullmatch('https?://[^/]*imgur\.com/(r/[^/]+/)?([a-zA-Z0-9]+)', url)
    if match:
        return ('autodetect', match.group(2))

    match = re.fullmatch('https?://[^/]*imgur\.com/a/([a-zA-Z0-9]+)', url)
    if match:
        return ('album', match.group(1))

    match = re.fullmatch('https?://[^/]*imgur\.com/gallery/([a-zA-Z0-9]+)(/new)?', url)
    if match:
        return ('gallery', match.group(1))

    return ('unknown', '')

count = 0

def direct_download(filename, dest_filename=None):
    if dest_filename is None:
        dest_filename = filename
    canonical_url = 'http://i.imgur.com/' + filename
    r = requests.get(canonical_url)
    if not r.ok:
        print('status code %d from %s' % (r.status_code, canonical_url))
        return
    with open(dest_filename, 'wb') as f:
        f.write(r.content)

def gif_download(image_id, album_id=None):
    # try webm first because it's easier to reupload, then mp4 if that fails
    # (webm and mp4 have similar file sizes, while gif is unnecessarily huge)
    webm_filename = '%s.webm' % (image_id,)
    webm_url = 'http://i.imgur.com/' + webm_filename
    r = requests.get(webm_url)
    if r.ok:
        if album_id is None:
            dest_filename = webm_filename
        else:
            dest_filename = album_id + '.webm'
        with open(dest_filename, 'wb') as f:
            f.write(r.content)
        return

    mp4_filename = '%s.mp4' % (image_id,)
    mp4_url = 'http://i.imgur.com/' + mp4_filename
    r = requests.get(mp4_url)
    if r.ok:
        if album_id is None:
            dest_filename = mp4_filename
        else:
            dest_filename = album_id + '.mp4'
        with open(dest_filename, 'wb') as f:
            f.write(r.content)
        return
    if r.status_code != 400:
        print('status code %d from %s' % (r.status_code, mp4_url))
        return

    # 400 means this is a non-animated gif, therefore there is no mp4
    gif_filename = '%s.gif' % (image_id,)
    gif_url = 'http://i.imgur.com/' + gif_filename
    r = requests.get(gif_url)
    if r.ok:
        if album_id is None:
            dest_filename = gif_filename
        else:
            dest_filename = album_id + '.gif'
        with open(dest_filename, 'wb') as f:
            f.write(r.content)
    else:
        print('status code %d from %s' % (r.status_code, gif_url))

def autodetect_download(canonical_url, album_id):
    r = requests.get(canonical_url)
    if not r.ok:
        print('status code %d from %s' % (r.status_code, canonical_url))
        return
    match = re.search('<meta property="og:[^>]*https?://i\.imgur\.com/([a-zA-Z0-9]+)\.(jpg|jpeg|png|mp4|gif)', r.text)
    if not match:
        if '<title>' in r.text:
            print('no image url found in %s' % (canonical_url,))
        # if <title> not found, likely crypto-404
        return
    image_id = match.group(1)
    extension = match.group(2)
    if extension == 'mp4' or extension == 'gif':
        # note that imgur never gives a webm url even if the image was uploaded
        # as a webm, so we always try webm first then mp4
        gif_download(image_id, album_id)
    else:
        direct_download(image_id + '.' + extension,
                        album_id + '.' + extension)

def album_download(album_id, original_url):
    if (os.path.isfile(album_id + '.jpg') or
        os.path.isfile(album_id + '.jpeg') or
        os.path.isfile(album_id + '.png') or
        os.path.isfile(album_id + '.mp4') or
        os.path.isfile(album_id + '.webm') or
        os.path.isfile(album_id + '.gif') or
        os.path.isfile(album_id + '.zip')):
        return

    filename = album_id + '.zip'
    zip_url = 'http://imgur.com/a/' + album_id + '/zip'
    r = requests.get(zip_url)
    if r.ok:
        with open(filename, 'wb') as f:
            f.write(r.content)
        return
    else:
        # this sometimes happens in the case of a single-image gallery
        autodetect_download(original_url, album_id)

for line in sys.stdin:
    if count > 0 and count % 100 == 0:
        print('processed %d urls' % (count,))
    count += 1
    url = line.rstrip('\n')
    urltype = classify(url)
    if urltype[0] == 'direct':
        filename = urltype[1]
        if not os.path.isfile(filename):
            direct_download(filename)
    elif urltype[0] == 'gif':
        image_id = urltype[1]
        if (os.path.isfile(image_id + '.webm') or
            os.path.isfile(image_id + '.mp4') or
            os.path.isfile(image_id + '.gif')):
            continue
        gif_download(urltype[1])
    elif urltype[0] == 'autodetect':
        image_id = urltype[1]
        if (os.path.isfile(image_id + '.jpg') or
            os.path.isfile(image_id + '.jpeg') or
            os.path.isfile(image_id + '.png') or
            os.path.isfile(image_id + '.mp4') or
            os.path.isfile(image_id + '.webm') or
            os.path.isfile(image_id + '.gif')):
            continue
        autodetect_download('http://imgur.com/' + image_id, image_id)
    elif urltype[0] == 'album':
        album_id = urltype[1]
        album_download(album_id, 'http://imgur.com/a/' + album_id)
    elif urltype[0] == 'gallery':
        # can download as album, but be careful: sometimes the album doesn't
        # exist (I've only seen this in the special case of a single image,
        # though)
        album_id = urltype[1]
        album_download(album_id, 'http://imgur.com/gallery/' + album_id)
    else:
        print('unrecognized format %s' % (url,))
