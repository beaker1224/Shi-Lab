import json

def save_to_json(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file)

def load_from_json(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)
    
#def main():

def interpreter():


# this will directly ask how user want to set up things, should be avaliable in the future

#if __name__ == "__main__":
#    main()

# this will interpret the data in parameter.txt file into json format
if __name__ == "__parameter_interpreter.py__":
    interpreter()