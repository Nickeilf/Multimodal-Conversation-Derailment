import argparse
import json
from pathlib import Path
from tqdm import tqdm

from utils import get_comments_by_ids, get_title_by_id, download_image, preprocess_text, mask_ot


def fetch(args):
    raw_data = []
    with open(args.input_file, 'r') as f:
        for line in f:
            raw_data.append(json.loads(line))

    out_dir = Path(args.image_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # fetch data using pushshift API
    retrieved_data = []
    missed_title_ids = []
    missed_target_ids = []
    missed_image_ids = []
    for conversation in tqdm(raw_data):
        title_id = conversation['title_id']
        utterance_ids = conversation['utterance_ids']
        target_id = conversation['target_id']
        image_url = conversation['img_url']
        image_name = conversation['img']
        comment_ids = utterance_ids + [target_id]
        
        title = get_title_by_id(title_id)
        comments = get_comments_by_ids(comment_ids)
        
        # data might be removed from Reddit by the author and due to policy they are not retrievable by PushshiftAPI
        if title != "[removed]" and comments[-1] != "[removed]" and image_url != "[removed]":
            conversation['title'] = preprocess_text(title)
            conversation['text'] = mask_ot(preprocess_text(comments[-1]))
            conversation['utterances'] = [preprocess_text(uttr) for uttr in comments[:-1]]

            valid_image = download_image(out_dir, image_url, title_id.split("_")[1], image_name)
            if valid_image:
                retrieved_data.append(conversation)
            else:
                print(
                    f"Conversation with target id {target_id} is not retrievable with missed images.")
                missed_image_ids.append(target_id)
        else:
            if comments[-1] == "[removed]":
                print(
                    f"Conversation with target id {target_id} is not retrievable with missed target text.")
                missed_target_ids.append(target_id)
            elif title == "[removed]":
                print(
                    f"Conversation with target id {target_id} is not retrievable with missed title text.")
                missed_title_ids.append(target_id)
            else:
                print(
                    f"Conversation with target id {target_id} is not retrievable with missed images.")
                missed_image_ids.append(target_id)
        
    with open(args.output_file, 'w') as f:
        for data_example in retrieved_data:
            f.write(json.dumps(data_example, ensure_ascii=False) + "\n")
    
    with open("missed_title_conversations.txt", 'w') as title_f, open("missed_image_conversations.txt", 'w') as image_f, open("missed_target_conversations.txt", 'w') as target_f:
        for target_id in missed_title_ids:
            title_f.write(target_id + "\n")
        
        for target_id in missed_image_ids:
            image_f.write(target_id + "\n")
        
        for target_id in missed_target_ids:
            target_f.write(target_id + "\n")

    print("Data retrieval finished! {}/{} conversations successfully retrieved.".format(
        len(retrieved_data), len(raw_data)))
    print("{} conversations are missing because of missed title.".format(len(missed_title_ids)))
    print("{} conversations are missing because of missed image.".format(
        len(missed_image_ids)))
    print("{} conversations are missing because of missed target.".format(
        len(missed_target_ids)))
    print("For raw data including removed texts/images, please contact the dataset author.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_file", default="data.jsonl", help="Name of input jsonl file")
    parser.add_argument("-o", "--output_file", help="Name of output jsonl file to store texts retrieved from Reddit")
    parser.add_argument("-id", "--image_dir", help="Output directory to store images retrieved from Reddit")

    args = parser.parse_args()
    
    fetch(args)
