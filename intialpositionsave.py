import pickle

def load_initial_positions():
    with open("initial_positions.dat", 'rb') as f:
        return pickle.load(f)
    
print(load_initial_positions())