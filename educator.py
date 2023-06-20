import pandas as pd
import numpy as np
import json
import os
import datetime
from langchain import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    HumanMessage,
    SystemMessage
)
import streamlit as st
from PIL import Image



# getting keys
# TODO: remove unnecessary aspects
with open('config.json') as f:
    keys = json.load(f)
PATH = keys['path']
openai_api_key = keys['openai_api_key']
os.environ["OPENAI_API_KEY"] = openai_api_key
directory = '/data' # replace this when working with PATH



# Variables 

# Get the current date and time
now = datetime.datetime.now()
# Format the date and time as a string in the desired format
timestamp = now.strftime("%Y%m%d%H%M%S")
# the available teachers and their characteristic style
teachers_dict = {
    'Severus Snape': 'Very sarcastic',
    'Aristoteles': 'wise, philosophical',
    'A professional programming teacher':'neutral',
    'Bob Ross':'very kind, understanding'
}



# Functions

def save_to_txt(name, input_string, timestamp):
    # Define the directory path
    directory = "Documents/educator/data/"
    # Create the directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    # Define the file name with the timestamp
    filename = f"{directory}{timestamp}_{name}.txt"
    # Write the string to the file
    with open(filename, "w") as file:
        file.write(input_string)

def create_feedback(teacher, style, code_input):
    # defining the prompt templates for a standardized input
    template="You are {teacher} and you teach programming learners. You review code and give {style} feedback like {teacher} would phrase it."
    system_message_prompt = SystemMessagePromptTemplate.from_template(template)
    human_template="{code_input}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

    # get a chat completion from the formatted messages
    chat_prompt.format_prompt(teacher=teacher, style=style, code_input=code_input).to_messages()

    llm = ChatOpenAI(temperature=0.9)
    chain = LLMChain(llm=llm, prompt=chat_prompt)

    feedback = (chain.run({
        'teacher':teacher, 
        'style':style, 
        'code_input':code_input
        }))

    return feedback

def shorten_feedback(feedback): 
    # defining the prompt template for a standardized input
    short_feedback_prompt = PromptTemplate(
        input_variables=["feedback"],
        template="Please shorten the aspects of the following feeback: {feedback}?",
    )
    # initializing the LM
    # TO OPTIMIZE THE TEMPERATURE
    short_feedback_llm = OpenAI(temperature=0)
    # a simple chain taking the formatted the prompt and sending it to the LM
    short_feedback_chain = LLMChain(llm=short_feedback_llm, prompt=short_feedback_prompt)
    # Run the chain only specifying the input = short feedback.
    short_feedback = short_feedback_chain.run(feedback)
    return short_feedback

# retrieve learning goals from the saved files
def get_latest_goal(directory):
    # Get a list of all files in the directory
    files = os.listdir(directory)
    # Filter the list to only include files with the correct format
    files = [f for f in files if f.endswith("_learninggoals.txt") and len(f) == 32]
    if not files:
        latest_goal = None
    else:
        # Get the most recent file
        files.sort(reverse=True)
        latest_file = files[0]
        # Read the contents of the file into the latest_goal variable
        with open(os.path.join(directory, latest_file), "r") as f:
            latest_goal = f.read()
    return latest_goal

# uses the learning goals retrieved in `get_latest_goal` if available and evaluates the code
def evaluate_code(teacher, style, code_input, latest_goal):
    if latest_goal is not None:
        # defining the prompt templates for a standardized input
        template = "You are {teacher} and you review code and give {style} feedback like {teacher} would phrase it. You compare learning goals of your student with submitted code. If necessary, you remind your student what they wanted to learn."
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        human_template = "Please compare my code input: {code_input} with my learning goals: {latest_goal}. Did I improve my style and follow what I wanted to achieve?"
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

        # get a chat completion from the formatted messages
        chat_prompt.format_prompt(
            teacher=teacher, style=style, code_input=code_input, latest_goal=latest_goal
        ).to_messages()

        llm = ChatOpenAI(temperature=0.9)
        chain = LLMChain(llm=llm, prompt=chat_prompt)

        evaluation = chain.run(
            {
                "teacher": teacher,
                "style": style,
                "code_input": code_input,
                "latest_goal": latest_goal,
            }
        )
    else:
        evaluation = "You haven't defined learning goals yet. If you want, you can define some by clicking the button below."
    return evaluation

def pick_latest_shortfeedbacks(directory):
    # TODO: use PATH here for directory
    # Get a list of all files in the directory
    files = os.listdir(directory)
    # Filter the list to only include files with the correct format
    files = [f for f in files if f.endswith("_shortfeedback.txt") and len(f) == 32]
    # if there are fewer than three files take all of them, if there are more take latest 3
    if len(files)<3:
        # Get the three most recent files
        latest_files = files
    else:
        # Sort the list of files by date, with the most recent file first
        files.sort(reverse=True)
        # Get the three most recent files
        latest_files = files[:3]
    return latest_files

# takes a list of latest files and appends their content
def append_shortfeedbacks(latest_files):
    # Read the contents of the two files into string variables
    file_contents = []
    for file in latest_files:
        with open(os.path.join(directory, file), "r") as f:
            file_contents.append(f.read())
    # Combine the three file contents into a single string variable
    latest_short_feedbacks = "\n".join(file_contents)
    return latest_short_feedbacks

def define_goal(latest_short_feedbacks):
    # defining the prompt template for a standardized input
    learning_goal_prompt = PromptTemplate(
        input_variables=["short_feedback"],
        template="Please summarize the following points: {short_feedback}",
    )
    # initializing the LM
    # TODO: check for optimal LLM
    learning_goal_llm = OpenAI(temperature=0.5)
    # a simple chain taking user input, formatting the prompt and sending it to the LM
    learning_goal_chain = LLMChain(llm=learning_goal_llm, prompt=learning_goal_prompt)
    # Run the chain only specifying the input variable.
    learning_goal = learning_goal_chain.run(latest_short_feedbacks)
    # saving the input to txt via the prepared function
    save_to_txt(name='learninggoals', input_string=learning_goal, timestamp=timestamp)
    return learning_goal

def add_vertical_space(num_lines: int = 1):
    """Add vertical space to your Streamlit app."""
    for _ in range(num_lines):
        st.write("")

        

# streamlit page
st.set_page_config(
    page_title="The Educator",
    layout="wide",
)

def main():

    st.sidebar.image('background.png', use_column_width=True)

    
    st.title('Educator')

    # default teacher style
    teacher = 'Aristoteles'

    # two columns to design the page split
    col1, col2 = st.columns([3,1])

    with col1:
        st.write('')
    with col2:
        with st.expander("Choose your educator here"):
            # overwrite if wanted:
            teacher = st.radio(label='Who do you want to teach you?', options=[
                'Aristoteles', 'Severus Snape', 'A professional programming teacher', 'Bob Ross'
            ])

        # Accessing the style of the selected or default teacher via the dict
        style = teachers_dict[teacher]

    # two columns to keep the page split
    col3, col4 = st.columns([3,1])
    with col3:
        # Code review
        # add code input as text here
        code_input = st.text_area("Your code")

        # saving the input to txt via the prepared function
        save_to_txt(name='codeinput', input_string=code_input, timestamp=timestamp)

        # execute only when a code is passed 
        if code_input != '':
            # generate the feedback to the submitted code
            feedback = create_feedback(teacher, style, code_input)
            # saving the feedback to txt
            save_to_txt(name='feedback', input_string=feedback, timestamp=timestamp)
            # create shorter versions of the feedback for better further use
            short_feedback = shorten_feedback(feedback)
            # saving the short feedback to txt via the prepared function
            save_to_txt(name='shortfeedback', input_string=short_feedback, timestamp=timestamp)

            st.header('Your feedback:')
            st.write(feedback)

            # retrieving the current leaning goals for evaluation
            latest_goal = get_latest_goal(directory=directory)
            # evaluating the code against the current learning goals and 
            # prints out a reminder if no learning goals have been defined yet
            evaluation = evaluate_code(teacher, style, code_input, latest_goal)
            st.subheader('Think of your learning goals:')
            st.write(evaluation)


        add_vertical_space(2)


        # Set learning goals
        # This has to be done only if the user checks the button 
        if st.button('Define learning goals'):
            # selecting the last three feedbacks in their short form
            latest_files = pick_latest_shortfeedbacks(directory)
            # combining the content of these files in one string
            latest_short_feedbacks = append_shortfeedbacks(latest_files=latest_files)
            # defining the new learning goals from the last feedbacks
            new_learning_goal = define_goal(latest_short_feedbacks=latest_short_feedbacks)
            assert len(new_learning_goal) != 0, 'The created learning goal was empty'
            st.write('Your new goals are:' + new_learning_goal)

    with col4:
        image_name = str('teacher_images/') + teacher + str('.png')
        image = Image.open(image_name)
        st.image(image)


if __name__ == '__main__':
    main()

