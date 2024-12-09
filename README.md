# story-builder-quest
Generative AI streamlit app to iteratively tell bed time stories for kids.

App overview:
A problem I noticed as an aunt of a 3-year old is that entertaining and engaging young kids can be very challenging, especially as a busy working parent. This inspired to dig deeper to design a streaming solution for parents to keep their kids engaged.

I conducted 20 user interviews to learn more about user preferences and identified user needs that I aimed to solve for with this app. Analyzing this further, narrowed me down into an interactive, audio-only tool that could iteratively create stories based on inputs from the kids. The key insights, product strategy, and GTM strategy is captured in the product pitch PDF.

This app creates the interactive and iterative story-builder and allows the user to save the output. Based on my testing, it seems to do this effectively. 

User inputs:
- Topic that they want to generate a story about. 
- The age of the child playing.
- The number of minutes they want the story to be. This is used to calculate the number of prompts (assuming each prompt takes about 2 minutes to get through).
- Their child's name. The intent is that the generated story will replace the main character's name with the child in question.

The model will leverage research from Wikipedia and Langchain to come up with story chunks of length of about 3-5 sentences. Until it reaches the last chunk, the model will generate chunks that end in a prompt for the user to continue the story and display an area to make the choice for how the story should continue. The model then takes this input, and continues the story for the next chunk. In the last chunk, the model is supposed to conclude the story. 

Key Class Concepts Used:
- Langchain to build the random story outputs based on user input.
- Streamlit to design the front end for the app. 
- Prompt engineering to design the prompts for the Langchain.
- Temperature of 0.8 to allow for a balance between randomness so that each time the stories are different but also controlling for ensuring that the stories are actually about the topic the user specified and truly age-appropriate.

App risks and shortcomings:
Sometimes the output generated by the model isn't perfect -- in particular, two trends I noticed is that each output didn't always adhere to the 3-5 sentence limit and the main character's name wasn't always what the user provided. 

In addition, in terms of bias, often times the story presented misgendered the main character's name and presented concepts that may not be entirely factually accurate. This is likely a reflection of sourcing the data from the Wikipedia API, which is a crowd-sourced information resource. While it allows the model flexibility to create stories on a wide array of topics, the information used is not always unbiased or accurate. However, in my testing, I found that these cases were limited and did not greatly limit the user experience.

With more time, these are issues I could further refine with fine-tuning. In particular, I would provide the user with the ability to provide feedback on the stories created and use that data to iterate on the model's efficacy. Another way I could do this is by creating a story success metric based on which stories the user saves and use that dataset to further refine my model's output. 

I could also explore leveraging other input data sources outside of just Wikipedia that may be a better source for children's stories to ensure that the output is age-appropriate.

The files included can be found in this github:

https://github.com/mohvem/story-builder-quest


