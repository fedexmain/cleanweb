import openai
import os
import sys
import time
import random
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()  # Only needed locally

APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top

# Save File
def save_file(filename, data):
    with open(APP_ROOT+'/'+filename, 'w') as f:
        f.write(str(data))

# Retrieve File
def retrieve_file(filename):
    with open(APP_ROOT+'/'+filename, 'r') as f:
        data = f.read()
    return data

def clean_string(my_string):
    # define a list of unwanted characters
    unwanted_chars = ["!", ",", "-", " ", "\n", "\\", "/"]
    # use list comprehension to remove the unwanted characters 
    cleaned_string = ''.join([char for char in my_string if char not in unwanted_chars])
    # print the cleaned string 
    return cleaned_string

#configure settings for app
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Use GPT-3.5 as default model
default_model_id = "text-davinci-003"
def change_model():
    models = openai.Model.list()['data']
    print("\nAvailable models:")
    for model in models:
        model_num = models.index(model)
        print('\n{:3d}. {}'.format(model_num+1, model['id']))
    model_num = int(input("Choose a model id from the list above: ")) - 1
    model_id=models[model_num]['id']
    return model_id



def print_progress(progress, total, printed_chars, chat_history):
    progress_percent = progress / total * 100
    os.system('cls')
    os.system('clear')
    print()
    roller=random.choice(['/','\\','-','|'])
    sys.stdout.write(f"Generating text: {progress}/{total} ({progress_percent:.1f}%){'='*(int(progress_percent)%20)}> {roller}")
    sys.stdout.write(f"{chat_history}{printed_chars}")
    time.sleep(0.001)
    sys.stdout.flush()

def chat_fAtherGPT(prompt, model_id=default_model_id):
    try:
        completions = openai.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=1024,
            temperature=0.7,
        )
        message = completions.choices[0].text
        error=''
        return message, error

    except Exception as error:
        print(error)
        message=''
        return message,error


def main():
    model_id = default_model_id # replace with "text-davinci-3.5" to use the GPT-3.5 model
    change_default_model = input(f"\nDo you want to change model from default model ({model_id})? (y/n): ")
    if change_default_model.lower().startswith("y"):
        model_id = change_model()
    model_version = model_id.split(":")[-1]
    username=str(input('\nEnter your Username: '))
    bot_name=str(input('\nEnter your Botname: '))
    chat_history = ''
    count=0
    while True:
        print()
        print()
        prompt = input("Enter a prompt: ")
        
        chat_history+=f'\n[{username}]==>'+str(prompt)+'\n:\n'+f'[{bot_name}]==>'
        
        message = chat_fAtherGPT(chat_history, model_id)
        total_tokens = len(message)
        print(f"\nGenerated text ({total_tokens} tokens):")
        
        stripped_msg = message.strip()
        printed_chars = ''
        for i, char in enumerate(stripped_msg, 1):
            printed_chars += char
            print_progress(i, total_tokens,printed_chars,chat_history)

        chat_history+=printed_chars+'\n;\n\n'
        output_date = str(datetime.utcnow())
        output_date = output_date.replace(' ','@').replace(':','_')[:output_date.index('.')]
        
        filename = chat_fAtherGPT(f"give \n'{printed_chars}'\n the best suitable filename with suitable .extension",model_id)
        filename = clean_string(filename)
        if 'python' in chat_history.lower() or 'code' in chat_history.lower():
            save_file('output/{}'.format(filename), printed_chars)
        else:
            save_file('output/Doc_{}'.format(filename), printed_chars)

        count += 1
        if 1:#count >= 10:
            satisfaction = 'y'#input("\nDo you want to generate more text? (y/n): ")
            if not satisfaction.lower().startswith("y"):
                break
            else:
                count = 0
        if prompt == "$Quit":
            print(chat_history.replace(';','\n\n'))#chat_history=''
            save_file('chat_history_{}.txt'.format(output_date), printed_chars)
            break


if __name__ == '__main__':
    main()