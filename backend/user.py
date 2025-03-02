import os
import pickle
#import SRS
import sys
import pandas as pd
import datetime as dt
sys.path.append("./srs")
from SRS import SRS
USER_ROOT = "./users"


class User:
    def load(id):
        if not os.path.exists(USER_ROOT):
            os.mkdir(USER_ROOT)
        if not os.path.exists(f"{USER_ROOT}/{id}"):
            os.mkdir(f"{USER_ROOT}/{id}")
            return User(id)
        else:
            try:
                with open(f"{USER_ROOT}/{id}/{id}.user", "rb") as file:
                    return pickle.load(file)
            except:
                return User(id)
    
    def __init__(self, id):
        self.id = id
        self.SRS = SRS()
        self.daily_stats = pd.DataFrame(columns=["known words"])
        self.messages = []
    def get_SRS(self):
        return self.SRS
    
    def update_daily_known_word_count(self, num_words):
        today = dt.date.today()
        if today not in self.daily_stats.index:
            self.daily_stats.loc[today] = 0
        self.daily_stats.loc[today,"known words"] += num_words

    def update_messages(self, prompt, res):
        self.messages.append((prompt,res))

    def save(self):
        print(self.messages)
        with open(f"{USER_ROOT}/{self.id}/{self.id}.user", "wb") as f:
            pickle.dump(self, f)
