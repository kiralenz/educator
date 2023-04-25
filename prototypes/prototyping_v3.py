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

def create_feedback(code_input):
    # defining the prompt template for a standardized input
    # TO EXPLORE: refine prompt
    feedback_prompt = PromptTemplate(
        input_variables=["code"],
        template="Please review the following code and give five recommendations with detailed explanations how to improve the programming: {code}?",
    )
    
    # initializing the LM
    # TO EXPLORE: adjust temperature
    # TO EXPLORE: test other LMs
    feedback_llm = OpenAI(temperature=0.3)
    
    # a simple chain taking user input, formatting the prompt and sending it to the LM
    feedback_chain = LLMChain(llm=feedback_llm, prompt=feedback_prompt)
    
    # Run the chain only specifying the input variable.
    feedback = feedback_chain.run(code_input)
    
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
    # TO OPTIMIZE
    short_feedback_llm = OpenAI(temperature=0)
    
    # a simple chain taking user input, formatting the prompt and sending it to the LM
    short_feedback_chain = LLMChain(llm=short_feedback_llm, prompt=short_feedback_prompt)
    
    # Run the chain only specifying the input variable.
    short_feedback = short_feedback_chain.run(feedback)
    
    # saving the input to txt via the prepared function
    save_to_txt(name='shortfeedback', input_string=short_feedback)
    
    return short_feedback

# TODO: separate into a reading and a merging function and reuse reading function
def pick_shortfeedbacks(directory, n):
    # TODO: use PATH here for directory
    
    # Get a list of all files in the directory
    files = os.listdir(directory)
    
    # Filter the list to only include files with the correct format
    files = [f for f in files if f.endswith("_shortfeedback.txt") and len(f) == 32]
    
    # Sort the list of files by date, with the most recent file first
    files.sort(reverse=True)
    
    # Get the three most recent files
    latest_files = files[:n]
    
    # Read the contents of the two files into string variables
    file_contents = []
    for file in latest_files:
        with open(os.path.join(directory, file), "r") as f:
            file_contents.append(f.read())
            
    # Combine the two file contents into a single string variable
    latest_short_feedbacks = "\n".join(file_contents)
    
    return latest_short_feedbacks

# TODO: improve the template without making it break
def define_goal(latest_short_feedbacks):
    
    # defining the prompt template for a standardized input
    learning_goal_prompt = PromptTemplate(
        input_variables=["short_feedback"],
        template="Summarize the following points: {short_feedback}",
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

# TODO: what happens if there is no learning goal?
# it is supposed to not produce an error but only return something empty
def evaluate_code(directory, code_input):
    # Get a list of all files in the directory
    files = os.listdir(directory)

    # Filter the list to only include files with the correct format
    files = [f for f in files if f.endswith("_learninggoals.txt") and len(f) == 32]

    # Sort the list of files by date, with the most recent file first
    files.sort(reverse=True)

    # Get the most recent file
    latest_file = files[:1]

    with open(os.path.join(directory, latest_file[0]), "r") as f:
        learning_goals = f.read()
    
    # defining the promp template to get both the latest code input and learning_goals
    evaluation_prompt = PromptTemplate(
        input_variables=["code_input", "learning_goals"],
        template="Please compare this code: {code_input} with these learning goals: {learning_goals}. If the programmer considered the learning goals when writing the provided code, say something motivating. If the programmer didn't consider the learning goals, gently remind the person of their learning goals.",
    )
    
    # application of the template
    evaluation_prompt = evaluation_prompt.format(code_input=code_input, learning_goals=learning_goals)
    
    # llm definition
    evaluation_llm = OpenAI(temperature=0.3)
    
    evaluation = evaluation_llm(evaluation_prompt)
    
    return evaluation

def get_feedback(code_input, directory):
    
    # create feedback from input
    feedback = create_feedback(code_input=code_input)
    
    # stop the program if the created output is empty
    assert len(feedback) != 0, 'The created feedback was empty'
    
    # create short feedback for goal definition
    short_feedback = shorten_feedback(feedback=feedback)

    # stop the program if the created output is empty
    assert len(short_feedback) != 0, 'The created shortfeedback was empty'
    
    # evaluate if the learning goals have been applied while coding
    evaluation = evaluate_code(directory=directory, code_input=code_input)
    
    return feedback, evaluation



# streamlit page

st.title('Educator')



# Code review

# feature to be added: read from Github

# add code input as text here
code_input = st.text_input("Your code")

# saving the input to txt via the prepared function
save_to_txt(name='codeinput', input_string=code_input)

# execute only when a code is passed --> repair that
if code_input is not None:
    
    feedback, evaluation = get_feedback(code_input=code_input, directory='../data')
    
    st.header('Your feedback:')
    st.write(feedback)
    st.header('Your evaluation:')
    st.write(evaluation)

    

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

