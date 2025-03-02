import os
import pickle
#import SRS
import sys
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

    def get_SRS(self):
        return self.SRS

    def save(self):
        with open(f"{USER_ROOT}/{self.id}/{self.id}.user", "wb") as f:
            pickle.dump(self, f)
