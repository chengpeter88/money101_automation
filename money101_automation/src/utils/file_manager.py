import json 
import os
import pandas as pd

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def save_to_excel(data, filename):
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)

def load_from_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_from_excel(filename):
    return pd.read_excel(filename)