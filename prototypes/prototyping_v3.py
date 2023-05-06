import pandas as pd
import numpy as np
import json
import os
from langchain import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import datetime
import streamlit as st



# getting keys
# TODO: remove unnecessary aspects
with open('../config.json') as f:
    keys = json.load(f)
PATH = keys['path']
openai_api_key = keys['openai_api_key']
os.environ["OPENAI_API_KEY"] = openai_api_key



# Variables 

# Get the current date and time
now = datetime.datetime.now()
# Format the date and time as a string in the desired format
timestamp = now.strftime("%Y%m%d%H%M%S")



# Functions

def save_to_txt(name, input_string):
    # Define the file name with the timestamp
    # TODO: add the PATH to the filename
    filename = f"../data/{timestamp}_{name}.txt"
    # Write the string to the file
    with open(filename, "w") as file:
        file.write(input_string)

def create_feedback(code_input, teaching_style):
    # defining the prompt template for a standardized input
    # TO EXPLORE: refine prompt
    feedback_prompt = PromptTemplate(
        input_variables=["teaching_style", "code_input"],
        template="You are {teaching_style}. Please review the following code and give five recommendations with detailed explanations how to improve the programming: {code_input}?",
    )
    
    feedback_prompt = feedback_prompt.format(teaching_style=teaching_style, code_input=code_input)
    
    # initializing the LM
    # TO EXPLORE: test other LMs
    feedback_llm = OpenAI(temperature=0.5)
    
    feedback = feedback_llm(feedback_prompt)
    
    # saving the input to txt via the prepared function
    save_to_txt(name='feedback', input_string=feedback)
    
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
    
    # a simple chain taking user input, formatting the prompt and sending it to the LM
    short_feedback_chain = LLMChain(llm=short_feedback_llm, prompt=short_feedback_prompt)
    
    # Run the chain only specifying the input variable.
    short_feedback = short_feedback_chain.run(feedback)
    
    # saving the input to txt via the prepared function
    save_to_txt(name='shortfeedback', input_string=short_feedback)

def pick_latest_shortfeedbacks(directory):
    # TODO: use PATH here for directory
    
    # Get a list of all files in the directory
    files = os.listdir(directory)
    
    # Filter the list to only include files with the correct format
    files = [f for f in files if f.endswith("_shortfeedback.txt") and len(f) == 32]
    
    # if there are fewer than three files take all of them, if there are more take latest 3
    if len(files)<3:
        # Sort the list of files by date, with the most recent file first
        files.sort(reverse=True)

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
    learning_goals = learning_goal_chain.run(latest_short_feedbacks)
    
    # saving the input to txt via the prepared function
    save_to_txt(name='learninggoals', input_string=learning_goals)
    
    return learning_goals

def get_learning_goals(directory, code_input, teaching_style):
    # Get a list of all files in the directory
    files = os.listdir(directory)

    # Filter the list to only include files with the correct format
    files = [f for f in files if f.endswith("_learninggoals.txt") and len(f) == 32]

    if not files:
        st.write("You haven't defined learning goals yet. If you want, you can define some by clicking the button below.")

    # Sort the list of files by date, with the most recent file first
    files.sort(reverse=True)

    # Get the most recent file
    latest_file = files[0]
    
    return latest_file

# WIP
def
    with open(os.path.join(directory, latest_file), "r") as f:
        learning_goals = f.read()
    
    # defining the promp template to get both the latest code input and learning_goals
    evaluation_prompt = PromptTemplate(
        input_variables=["teaching_style", "code_input", "learning_goals"],
        template="You are {teaching_style}. Please compare this code: {code_input} with these learning goals: {learning_goals}. If the programmer considered the learning goals when writing the provided code, say something motivating. If the programmer didn't consider the learning goals, gently remind the person of their learning goals.",
    )
    
    # application of the template
    evaluation_prompt = evaluation_prompt.format(code_input=code_input, learning_goals=learning_goals)
    
    # llm definition
    evaluation_llm = OpenAI(temperature=0.3)
    
    evaluation = evaluation_llm(evaluation_prompt)
    
    return evaluation

def get_feedback(code_input, directory, teaching_style):
    
    # create feedback from input
    feedback = create_feedback(code_input=code_input, teaching_style=teaching_style)
    
    # stop the program if the created output is empty
    assert len(feedback) != 0, 'The created feedback was empty'
    
    # create short feedback for goal definition
    short_feedback = shorten_feedback(feedback=feedback)

    # stop the program if the created output is empty
    assert len(short_feedback) != 0, 'The created shortfeedback was empty'
    
    return feedback

def add_vertical_space(num_lines: int = 1):
    """Add vertical space to your Streamlit app."""
    for _ in range(num_lines):
        st.write("")



# streamlit page

st.title('Educator')

# default teacher style
teaching_style = 'A professional programming teacher'

if st.button('Choose your educator'):
    teaching_style = st.radio('Your educator', ['Severus Snape','Bob Ross', 'Aristoteles'])
    st.write(teaching_style)

    
    
# Code review

# feature to be added: read from Github

# add code input as text here
code_input = st.text_input("Your code")

# saving the input to txt via the prepared function
save_to_txt(name='codeinput', input_string=code_input)

# WIP
# execute only when a code is passed 
if code_input != '':
    
    feedback = get_feedback(code_input=code_input, directory='../data', teaching_style=teaching_style)
    
    # WIP
    # evaluate if the learning goals have been applied while coding
    evaluation = evaluate_code(directory=directory, code_input=code_input, teaching_style=teaching_style)
    
    st.header('Your feedback:')
    st.write(feedback)
    st.header('Your evaluation:')
    st.write(evaluation)

    
add_vertical_space(2)
    
# Set learning goals
# This has to be done once and then only if the user checks the button 

if st.button('Define learning goals'):
    # get latest short feedbacks
    latest_short_feedbacks = pick_shortfeedbacks(directory='../data', n=3)
    # define goal from latest short feedbacks
    learning_goals = define_goal(latest_short_feedbacks=latest_short_feedbacks)
    
    # stop the program if the created output is empty
    assert len(learning_goals) != 0, 'The created learning goal was empty'
    
    st.write('Your new goals are:' + learning_goals)

