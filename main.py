import os
from openai import OpenAI
from time import sleep
import openai
import base64
import requests
import numpy as np
from utils import *


api_keys = ['your api key']
counter = 0


factor = 5000 # request per day // 10

folder_name = "your/path/to/saved/images"
ind = get_ind(folder_name=folder_name)

for file_ind in ind:
    if counter == len(api_keys)*factor:
        print(f'{file_ind} has not been finished')
        break
    api_key = api_keys[counter//factor]
    client = OpenAI(api_key = api_key)
    folder_path = os.path.join(folder_name,f"{file_ind}")
    if 'text.txt' in os.listdir(folder_path):

        continue
    else:
        print(f'redoing {folder_path}')
    image_pairs = find_image_pairs(folder_path)
    image_pairs.sort()
    result_file = generate_reranking(image_pairs,client)## generate reranking texts
    reply = rerank(result_file,client)## generate reranking response
    counter += 1


Top_K = np.zeros(3)

counter = 0
factor = 5000 # request per day // 10
for file_ind in ind:

    
    api_key = api_keys[counter//factor]
    client = OpenAI(api_key = api_key)
    folder_path = os.path.join(folder_name,f"{file_ind}")
    image_pairs = find_image_pairs(folder_path)
    if 'rerank.txt' in os.listdir(folder_path):
        with open(os.path.join(folder_path,'rerank.txt'),encoding='utf-8') as f:
            reply = f.read()
        ranking = from_text_to_rank(reply,client,0.1)## from text response to ranking
        orig_topk = Top_K.copy()
        Top_K = get_topk(ranking,image_pairs,Top_K)## from list to topk
        
        if Top_K[0] - orig_topk[0] == 0:
            print(f'Top 1 wrong at {file_ind}')
            print(ranking)
        if Top_K[1] - orig_topk[1] == 0:
            print(f'Top 5 wrong at {file_ind}')
            print(ranking)
        
        counter += 1
print(f"Accuracy is: {Top_K/1000}")