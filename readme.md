## *Tell Me Where You Are*: Multimodal LLMs Meet Place Recognition
Zonglin Lyu, Juexiao Zhang, Mingxuan Lu, Yiming Li, Chen Feng

### Try LLM-VPR
```
Save your Coarse retrieval results (with supervised models) as the followng structures:
└──── <working directory>/
    ├──── data_name/
    |   ├──── Query.png
    |   ├──── Top1_True/False.png
    |   ├──── ...
```
If the retrieval results is correct, the set is as True, otherwise False. This **does not** intend to tell MLLMs about the results. Instead, it is easier for you to compute whether MLLM imrpoves the performance or not. The True/False will be removed when they are fed to the MLLM.

Then write your own api keys and change the fill the directory of the saved data in ```main.py``` and run:

```
python main.py
```

This will generate .txt files with descriptions and reasonings. 
