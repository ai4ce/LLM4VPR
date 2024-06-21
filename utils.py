import os
from time import sleep
import base64
import numpy as np


def find_image_pairs(folder_path):
    # List to store the pairs
    image_pairs = []

    # Find the query image
    query_image = None
    for file in os.listdir(folder_path):
        if file.lower() == "query.png":
            query_image = os.path.join(folder_path, file)
            break

    # If the query image is found, pair it with each candidate
    if query_image:
        for file in os.listdir(folder_path):
            if file.startswith("Top") and file.endswith(".png"):
                candidate_image = os.path.join(folder_path, file)
                image_pairs.append((query_image, candidate_image))

    return image_pairs


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def generate_reranking(image_pairs,client,temperature = 0.2):
    
    prompt = f"I have 2 images of outdoor scenes: a query and a candidate. In this task, you must not talk about weather,lighting, vehicles, people, or animals. Refrain from mentioning any elements that are not directly observable or are obscure. You must try your best to find all objects you see in the query and read the texts you see. Then, for every object you see in the query, you should do the following: \n1. You should find all objects you see in the query.\n2. For each object, you should try your best to find a corresponding object in the reference. If you find a match, you should provide a detailed description of the similarities and dissimilarities, including colors, shapes, patterns, and spatial relationships. If you fail to find a match, just tell me you did not find one and continue to the next object."

    #prompt = f"I have 2 images of outdoor scenes: a query and a candidate. In this task, you must not talk about weather,lighting, vehicles, people, or animals. Refrain from mentioning any elements that are not directly observable or are obscure. You should do the following: \n1. You should provide a detailed description of the similarities and dissimilarities, including colors, shapes, patterns, and spatial relationships."
    ## this one removes object matching
    
    #prompt = f"I have 2 images of outdoor scenes: a query and a candidate. You should do the following: \n1. You should provide a detailed description of the similarities and dissimilarities, including colors, shapes, patterns, and spatial relationships."
    ## this one removes all constriants
    
    for pair in image_pairs:
        sleep(10)
        query_image = encode_image(pair[0])
        db_image = encode_image(pair[1])
        response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {"role":"system",
            "content":[
                {
                   "type":"text",
                    "text":f"You are an expert to analyze images. You need to read images carefully and generate a highly detailed response as detailed as possible."
                }
            ]
            },
            
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": prompt
                },
                {
                "type": "image_url",
                "image_url": {
                    
                    "url":f"data:image/png;base64,{query_image}"
                },
                },
                {
                "type": "image_url",
                "image_url": {
                    
                    "url":f"data:image/png;base64,{db_image}"
                },
                },
            ],
            }
        ],
        max_tokens=4096,
        temperature = temperature
        )
        folder_path = os.path.split(pair[0])[0]
        result_file = os.path.join(folder_path, "text.txt")
        with open(result_file, 'a', encoding='utf-8') as f:
            f.write(os.path.split(pair[1])[-1].replace(".png", "").replace("_True","").replace("_False","") + ":\n" + response.choices[0].message.content + "\n\n")

    return result_file




def rerank(result_file,client,temperature=0.2):

    try:
        with open(result_file, 'r', encoding='utf-8') as file:
            content = file.read()
    except FileNotFoundError:
        print("File not found. Please check the file path.")
    except Exception as e:
        print(f"An error occurred: {e}")

    # First round of conversation
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {
            "role":"system",
            "content":[
                {
                   "type":"text",
                    "text":"You are an expert in text-based place recognition. You need to read texts carefully."
                }
            ]
            },
            
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": "I am using a VPR model to retrieve the most similar images to a given query image. However, it possibly gives me wrong results. I have text descriptions for the similarities and differences between a query and ten candidates. I will provide you the text description of each query-candidate pair, and you should return a ranking of the likelihood that a candidate is at the sample place with the query. Keep in mind that weather, lighting, time, season, and viewpoint does not influence VPR results. Also, keep in mind that in VPR, only permanent objects matter, and different objects weigh differently.  Make sure you have detailed and thorough reasoning." + "\n\n" + content
                },
            ],
            }
        ],
        max_tokens=4096,
        temperature = temperature
        )

    first_round_reply = response.choices[0].message.content
    directory = os.path.split(result_file)[0]
    reply_file = os.path.join(directory,'rerank.txt')
    with open(reply_file, 'a', encoding='utf-8') as f:
            f.write(first_round_reply)
    sleep(0.5)
    return first_round_reply


def from_text_to_rank(first_round_reply,client,temperature = 0.2):
    response = client.chat.completions.create(
    model="gpt-4-1106-preview",
    messages=[
        {
        "role":"system",
        "content":[
            {
                "type":"text",
                "text":"You only should return integers seperated by spaces."
            }
        ]
        },
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": """
             You need to summarize the following rankings in a sequence of integers, and return me only the integers seperated by spaces""" 
            + "\n\n" + first_round_reply
            },
        ],
        }
    ],
    max_tokens=2048,
    temperature = temperature
    )

    second_round_reply = response.choices[0].message.content
    
    return second_round_reply

def get_topk(second_round_reply,image_pairs,Top_K):
    try:
        reranked = np.array(second_round_reply.split(',')).astype(int).reshape(-1,1)
    except:
        reranked = np.array(second_round_reply.split(' ')).astype(int).reshape(-1,1)
    GT = []
    for p in image_pairs:
        tmp = os.path.split(p[1])[-1].replace('.png','').replace('Top','').split('_')
        if 'True' in tmp:
            GT.append(int(tmp[0]))
    i = 0
    for k in [1,5,10]:
        if (np.array(GT).reshape(1,-1) == reranked[:k]).any():
            Top_K[i] += 1
        i += 1
    return Top_K

def get_ind(folder_name):
    folders = os.listdir(folder_name)
    folder_int =[]
    for f in folders:
        folder_int.append(int(f))
    ind = sorted(folder_int)
    return ind