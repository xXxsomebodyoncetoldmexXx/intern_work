import pickle

SECRET_CHECK = b"\xff\xfe"

new_version = {
    "Major": 3,
    "Minor": 1,
    "Patch": 3
}

with open("update.txt", "wb") as f:
  f.write(SECRET_CHECK)
  f.write(pickle.dumps(new_version))
