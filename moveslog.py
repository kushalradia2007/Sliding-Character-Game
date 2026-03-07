import pickle

def load_moves():
    with open("moves.dat", 'rb') as k:
        return pickle.load(k)

recorded_moves = load_moves()
print(recorded_moves)