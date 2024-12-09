# story-builder-quest
Generative AI streamlit app to iteratively tell bed time stories for kids.

User inputs:
- Topic that they want to generate a story about. 
- The age of the child playing.
- The number of minutes they want the story to be. This is used to calculate the number of prompts (assuming each prompt takes about 2 minutes to get through).
- Their child's name. The intent is that the generated story will replace the main character's name with the child in question.

The model will leverage research from Wikipedia and Langchain to come up with story chunks of length of about 3-5 sentences. Until it reaches the last chunk, the model will generate chunks that end in a prompt for the user to continue the story and display an area to make the choice for how the story should continue. The model then takes this input, and continues the story for the next chunk. In the last chunk, the model is supposed to conclude the story. 
