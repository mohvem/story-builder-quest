import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

# Set the title using StreamLit
st.title('Story Builder Quest')

# Formatting for the Text Input
st.markdown(
    """
    <style>
    .stTextInput > div > div > input {
        background-color: #f0f8ff; /* Light blue background */
        color: black;             /* Text color */
        border: 2px solid #4CAF50; /* Green border */
        padding: 5px;             /* Padding inside the box */
        border-radius: 5px;       /* Rounded corners */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize session state
if "story" not in st.session_state:
    st.session_state["story"] = []
if "current_decision" not in st.session_state:
    st.session_state["current_decision"] = None
if "step" not in st.session_state:
    st.session_state["step"] = 0
if "show_input" not in st.session_state:
    st.session_state["show_input"] = True
if "topic" not in st.session_state:
    st.session_state["topic"] = 'nothing'
if "age" not in st.session_state:
    st.session_state["age"] = 0
if "name" not in st.session_state:
    st.session_state["name"] = 'nothing'
if "age" not in st.session_state:
    st.session_state["age"] = 0
if "length" not in st.session_state:
    st.session_state["length"] = 2

# Cache for loading Wikipedia
@st.cache_data
def fetch_wikipedia_research(topic):
    # Replace this with your WikipediaAPIWrapper call
    wiki = WikipediaAPIWrapper()
    return wiki.run(topic)



from langchain.prompts import PromptTemplate

# Setting up the prompt templates
title_template = PromptTemplate(
    input_variables=['concept'], 
    template='Write a bed-time story about {concept}'
)

beginning_of_story_template = PromptTemplate(
    input_variables=['title', 'wikipedia_research', 'age', 'name'], 
    template=(
        "Write the opening of a bedtime story about the topic: {title}, crafted for a child aged {age}. "
        "Incorporate engaging details and relevant knowledge from the Wikipedia research: {wikipedia_research}, "
        "to create an imaginative and informative introduction. "
        "The story should set up an engaging scenario, introduce key characters or elements, and establish a sense of curiosity or challenge. "
        "The main character of the story should be named {name}."
        "Stop the story just before a major decision point that will decide how the story progresses."
        "Conclude by presenting the decision point clearly, but do not proceed with the resolution or outcome." 
        "Ensure that the output is only 3-5 sentences long. The decision question can be another 1-2 sentences long."
    )
)

continuing_of_story_template = PromptTemplate(
    input_variables=['title', 'wikipedia_research', 'age', 'beginning_of_story', 'decision', 'story_length'], 
    template=(
        "Continue the story about the topic: {title}, written for a child aged {age}. "
        "Build directly on the story so far: {beginning_of_story}, ensuring continuity with the existing characters, setting, and events. "
        "Incorporate the decision made by the user, which was: {decision}, and develop the narrative based on this choice. "
        "Use relevant details from the Wikipedia research: {wikipedia_research} to enrich the story, making it both engaging and educational. "
        "Do not introduce entirely new characters, settings, or plot elements unless they logically follow from the story's current state. "
        "Focus on resolving the story in a satisfying and age-appropriate way that reflects the user's decision. "
        "Ensure that the output is only 3-5 sentences long."
        # "Ensure the final segment aligns with the specified total duration of approximately {story_length} minutes, including the prior content."
    )
)

from langchain.memory import ConversationBufferMemory

# Memory setup
memoryT = ConversationBufferMemory(input_key='concept', memory_key='chat_history')
memoryS = ConversationBufferMemory(input_key='title', memory_key='chat_history')

from langchain_openai import ChatOpenAI

# Importing the large language model OpenAI via LangChain
model = ChatOpenAI(model='gpt-3.5-turbo-16k', temperature=0.7)

from langchain.chains import LLMChain

# Setting up chains
chainT = LLMChain(llm=model, prompt=title_template, verbose=True, output_key='title', memory=memoryT)
chainBOS = LLMChain(llm=model, prompt=beginning_of_story_template, verbose=True, output_key='bos_story', memory=memoryS)
chainCOS = LLMChain(llm=model, prompt=continuing_of_story_template, verbose=True, output_key='cos_story', memory=memoryS)

# Load and set up the Wikipedia API
from langchain_community.utilities import WikipediaAPIWrapper

# Define function to generate the next portion of the story
def generate_story_segment(topic, age, name, wikipedia_research, decision=None, current_story=None, length=None):
    """
    Generate the next segment of the story using a call to OpenAI and the Wikipedia API.

    Args:
        topic (str): Topic of the story.
        age (str): Age group of the child.
        wikipedia_research (str): Research data from Wikipedia.
        decision (str, optional): User's decision for the story progression.
        current_story (str, optional): The current portion of the story.
        length (str, optional): Desired length of the story.

    Returns:
        str: Next story segment.
    """
    if st.session_state.step == 0:
        return chainBOS.run(
            age=age,
            title=topic,
            wikipedia_research=wikipedia_research
            , name = name
        )
    return chainCOS.run(
        age=age,
        decision=decision,
        title=topic,
        wikipedia_research=wikipedia_research,
        beginning_of_story=current_story,
        story_length=length
    )

MAIN_FLOW = True
# Main workflow
if MAIN_FLOW:

    if st.session_state.show_input:
        # Input fields
        topic_input = st.text_input('On what topic do you want a story on?') 
        age_input = st.text_input('What age is your child?') 
        story_length_input = st.text_input('How many minutes do you want to spend?')
        name_of_child = st.text_input('What is the name of your child?')
        st.session_state.age = age_input
        st.session_state.length = story_length_input
        st.session_state.name = name_of_child
        st.session_state.topic = topic_input

    ### set up the number of prompts
    # TIME_PER_PROMPT = 3
    # n_prompts = round(ord(story_length_input) / TIME_PER_PROMPT, 0)

    ### set up the wikipedia API reader
    print(st.session_state.topic)
    wikipedia_research = fetch_wikipedia_research(st.session_state.topic)
    title = chainT.run(st.session_state.topic)

    # Generate the beginning of the story
    if st.session_state.step == 0:
        intro = generate_story_segment(
            topic=st.session_state.topic,
            age=st.session_state.age,
            wikipedia_research=wikipedia_research
            , name = st.session_state.name
        )
        st.session_state.story.append(intro)
        st.session_state.step += 1
        st.write(" ".join(st.session_state.story))

    # Provide a decision point
        st.subheader("What happens next?")

    decision = st.text_input("What happens next?")
    st.session_state.current_decision = decision
    st.session_state.show_input = False

    # Handle the user's decision
    if st.session_state.current_decision == '':
        st.write("Please make a decision to continue the story.")
    else:
        next_segment = generate_story_segment(
            topic=st.session_state.topic,
            age=st.session_state.age,
            decision=decision,
            wikipedia_research=wikipedia_research,
            current_story= " ".join(st.session_state.story),
            length=st.session_state.length
            , name = st.session_state.name
        )
        st.session_state.story.append(next_segment)
        st.session_state.step += 1
        st.session_state.current_decision = decision
        st.write(" ".join(st.session_state.story))

    with st.expander('Wikipedia-based exploration:'):
        st.info(wikipedia_research)
