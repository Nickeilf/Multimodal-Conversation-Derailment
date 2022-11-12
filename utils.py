import os
import wget
import re
import socket
import shutil
import time
from imgur_downloader import ImgurDownloader
from psaw import PushshiftAPI

# set timeout limit for wget
socket.setdefaulttimeout(30)

api = PushshiftAPI()


# comment_ids: list of ids
def get_comments_by_ids(comment_ids):
    time.sleep(0.5)
    gen = api.search_comments(ids=comment_ids)
    comments = list(gen)
    comments = [c._asdict() for c in comments]

    # sort returned comments by original ids, otherwise it will be shuffled
    retrieved_texts = []
    for id in comment_ids:
        text_found = False
        for comment in comments:
            if comment['id'] == id.split("_")[1]:
                retrieved_texts.append(comment['body'])
                text_found = True
        if not text_found:
            retrieved_texts.append("[removed]")
        
    return retrieved_texts


def get_title_by_id(title_id):
    time.sleep(0.5)
    gen = api.search_submissions(ids=title_id)
    result = list(gen)
    # non empty result
    if result:
        submission = result[0]
        return submission._asdict()['title']
    else:
        return "[removed]"


def download_imgur_image(dir, url, title_id, image_name):
    try:
        downloader = ImgurDownloader(
            url, dir_download=dir, delete_dne=True, file_name=title_id)
        good_images, skipped = downloader.save_images()

        if len(good_images) == 0:
            return False

        if len(good_images) > 1:
            for i, filename in enumerate(good_images):
                image_idx = image_name.split(".")[0].split("_")[1]
                image_idx = int(image_idx)
                
                if i == image_idx:
                    os.rename(dir / title_id / filename, dir / image_name)

            # remove other images
            shutil.rmtree(dir / title_id)
        return True

    except Exception as e:
        print(f"Image from {url} not retrievable. Error: {e}")
        return False


def download_image(dir, url, title_id, image_name):
    if not os.path.exists(dir):
        os.makedirs(dir)

    filename = dir / image_name

    # check if image already downloaded
    if os.path.exists(filename):
        return True

    # download from imgur if successful
    if "imgur" in url:
        valid_image = download_imgur_image(dir, url, title_id, image_name)
        if valid_image:
            return True

    # download direct image link
    try:
        wget.download(url=url, out=str(filename))
    except Exception as e:
        print(f"Image from {url} not retrievable. Error: {e}")
        return False
    return True


def preprocess_text(str):
    # replace \n
    # remove URLs
    if not str:
        str = ''
    str = remove_url(str)
    str = re.sub('\s+', ' ', str)
    return str


def mask_ot(str):
    str = str.replace('off topic', '')
    str = str.replace('off-topic', '')
    str = re.sub('\s+', ' ', str)
    return str


def remove_url(str):
    return re.sub('\(?https?://[^\s]+\)?', '<URL>', str)
