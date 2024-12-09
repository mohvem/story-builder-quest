import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

from gtts import gTTS
import tempfile
import openai
from PIL import Image
import requests
from io import BytesIO

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

       /* Style for Buttons */
    div.stButton > button {
        background-color: #1db954; /* Green background */
        color: white;              /* White text */
        border: none;              /* Remove border */
        padding: 10px 20px;        /* Add padding */
        text-align: center;        /* Center the text */
        text-decoration: none;     /* Remove underline */
        display: inline-block;     /* Inline-block for layout */
        font-size: 16px;           /* Text size */
        margin: 4px 2px;           /* Margin */
        cursor: pointer;           /* Pointer cursor */
        border-radius: 8px;        /* Rounded corners */
        transition: background-color 0.3s ease; /* Smooth hover effect */
    }

    <style>
    .logo-container {
        position: fixed;
        top: 10px;
        right: 10px; /* Adjust 'right' to 'left' if you want it on the left */
        z-index: 1000; /* Ensure it stays on top */
    }
    .logo-container img {
        width: 100px; /* Adjust size */
        height: auto;
        border-radius: 8px; /* Optional: rounded corners */
    }

    [data-testid="stSidebar"] {
        background-color: #191414; /* Green background */
        color: white; /* White text */
    }
    </style>
    <div class="logo-container">
        <img src="https://play-lh.googleusercontent.com/Xd1MS1QFXz_yy2SRpfx_DsMNla5ijTyCe5cYjR1bGbZt34aNQKGKYLlkdI2JMekAug" alt="Logo">
    </div>
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
    st.session_state["topic"] = None
if "age" not in st.session_state:
    st.session_state["age"] = None
if "name" not in st.session_state:
    st.session_state["name"] = None
if "age" not in st.session_state:
    st.session_state["age"] = None
if "length" not in st.session_state:
    st.session_state["length"] = None
if "num_prompts" not in st.session_state:
    st.session_state["num_prompts"] = 0
if "is_last" not in st.session_state:
    st.session_state["is_last"] = False
if "current_num_prompts" not in st.session_state:
    st.session_state["current_num_prompts"] = 1
if "sidebar_state" not in "st.session_state":
    st.session_state.sidebar_state = None

@st.cache_data
def speak_text(text):
    """
    Convert text to speech using gTTS and save it as an audio file.
    
    Args:
        text (str): The text to convert into speech.
        
    Returns:
        str: Path to the generated audio file.
    """
    # Generate speech
    tts = gTTS(text=text, lang="en")
    
    # Save to a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    temp_file_path = temp_file.name
    tts.save(temp_file_path)
    
    return temp_file_path

# Cache for loading Wikipedia
@st.cache_data
def fetch_wikipedia_research(topic):
    # Replace this with your WikipediaAPIWrapper call
    wiki = WikipediaAPIWrapper()
    return wiki.run(topic)

# Cache for the total number of prompts required
@st.cache_data
def fetch_num_prompts(length, time_per_prompt):
    ''' Function to define the total number of prompts needed for the story.'''
    return round(int(length) / time_per_prompt, 0)


# Cache for initial set up of the sidebars
def fetch_sidebars():
    st.sidebar.button("Story Builder Quest", key=f"response_{st.session_state.step}")
    st.sidebar.button("My Stories", key=f"response_{st.session_state.step}")
    return None


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
        "Ensure that the main character in the story is named {name} and guess its gender based on Wikipedia research: {wikipedia_research}."
        "Stop the story just before a major decision point that will decide how the story progresses."
        "Conclude by presenting the decision point clearly, but do not proceed with the resolution or outcome." 
        "Ensure that the output is only 3-5 sentences long. The decision question can be another 1-2 sentences long."
    )
)

continuing_of_story_template = PromptTemplate(
    input_variables=['title', 'wikipedia_research', 'age', 'beginning_of_story', 'decision', 'is_last'], 
    template=(
        "Continue the story about the topic: {title}, written for a child aged {age}. "
        "Build directly on the story so far: {beginning_of_story}, maintaining consistency with the existing characters, setting, and events. "
        "Incorporate the decision made by the user: {decision}, and develop the narrative to reflect the consequences of this choice in an engaging and meaningful way. "
        "Use relevant details from the Wikipedia research: {wikipedia_research} to make the story imaginative, educational, and rich with detail. "
        "Avoid introducing entirely new characters, settings, or plot elements unless they naturally follow from the current story. "
        "If {is_last} is True, bring the story to a satisfying and age-appropriate conclusion, fully resolving the narrative while reflecting the user's decision. "
        "If {is_last} is False, end the segment just before a pivotal moment that leaves the characters facing a clear choice or challenge. "
        "The output should be concise, limited to 3-5 sentences, while maintaining an engaging and immersive tone."
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
def generate_story_segment(topic, age, name, is_last, wikipedia_research, decision=None, current_story=None):
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
        is_last = is_last
    )

MAIN_FLOW = True
TIME_PER_PROMPT = 2
# fetch_sidebars()
# Main workflow for story builder quest
if MAIN_FLOW:

    # Set up the Sidebars
    st.sidebar.button("Story Builder Quest")
    if st.sidebar.button("Saved Stories"):
        st.session_state.sidebar_state = "saved"
    else:
        st.session_state.sidebar_state = "quest"

    # Main Flow    
    if st.session_state.sidebar_state == "quest":
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

        ### set up the wikipedia API reader
            title = chainT.run(st.session_state.topic)

        # Generate the beginning of the story
        if st.session_state.step == 0 and st.session_state.topic and st.session_state.age and st.session_state.name and st.session_state.length:
            ### set up the number of prompts
            st.session_state.num_prompts = fetch_num_prompts(length = st.session_state.length, time_per_prompt= TIME_PER_PROMPT )
            intro = generate_story_segment(
                topic=st.session_state.topic,
                age=st.session_state.age,
                wikipedia_research=fetch_wikipedia_research(st.session_state.topic)
                , name = st.session_state.name
                , is_last= st.session_state.is_last
            )
            st.session_state.story.append(intro)
            st.session_state.step += 1
            st.write(" ".join(st.session_state.story))
            audio_path = speak_text(intro)
            # image_url = generate_image(intro)
            st.write("### Listen to the Story...")
            st.audio(audio_path, format="audio/mp3")

        if st.session_state.current_num_prompts <= st.session_state.num_prompts and st.session_state.step > 0:

            st.subheader("What happens next?")
            decision = st.text_input("What happens next?", key=f"response_{st.session_state.step}")
            st.session_state.current_decision = decision
            st.session_state.show_input = False
            
            if st.session_state.current_num_prompts > 1:
                st.session_state.current_decision = decision

            # Handle the user's decision
            if st.session_state.current_decision == '':
                st.write("Please make a decision to continue the story.")
            else:
                st.write(st.session_state.is_last)
                next_segment = generate_story_segment(
                    topic=st.session_state.topic,
                    age=st.session_state.age,
                    decision=decision,
                    wikipedia_research=fetch_wikipedia_research(st.session_state.topic),
                    current_story= " ".join(st.session_state.story)
                    , name = st.session_state.name
                    , is_last = st.session_state.is_last
                )
                st.session_state.story.append(next_segment)
                st.session_state.current_decision = decision
                st.session_state.current_num_prompts += 1
                st.session_state.step += 1


                st.write(" ".join(st.session_state.story))
                audio_path = speak_text(next_segment)
                st.write("### Listen to the Next Part of the Story...")
                st.audio(audio_path, format="audio/mp3")

            if st.session_state.current_num_prompts == st.session_state.num_prompts - 1:
                st.session_state.is_last = True
                st.button("Continue to the next prompt?")
            elif st.session_state.current_num_prompts == st.session_state.num_prompts:
                st.write("The story is complete!")
                st.write("Want to save this story?")
                st.button("Yes.")
                if st.button("No"):
                    st.write("Thanks for writing a story today!")
                    st.session_state.clear()
                else:
                    filename = f"audio_{st.session_state.topic}.mp3"
                    audio_path = gTTS(" ".join(st.session_state.story))
                    file_path = os.path.join("audio_outputs", filename)
                    audio_path.save(file_path)
                    st.session_state.clear()
            elif st.session_state.current_num_prompts > 2:
                st.button("Continue to the next prompt?")
    elif st.session_state.sidebar_state == "saved":
        audio_files = [f for f in os.listdir("audio_outputs") if f.endswith('.mp3')]
        if audio_files:
            for audio_file in audio_files:
                file_path = os.path.join("audio_outputs", audio_file)
                st.write(f"Play: {audio_file}")
                st.audio(file_path, format="audio/mp3")
        else:
            st.write("Create a story in Story Builder Quest!")