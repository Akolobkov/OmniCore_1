<h1>OmniCore - a self-tool-creating agent</h1>
Warning! the project is on the early development stages. The best support is feedback.
The agent on current stage is able to one-shot create AND use tools fitting for the task to complete it, therefore being able to complete a vast spectre of simple tasks including web search, parsing, working with documents, running code, scraping, etc.  
<h2>Setup</h2>
Ollama - the project was build and tested using gemma4

Langchain (python library) - agent framework

The web search tool uses Talordata api (api provider can be changed)

Example tool (create_gradient_image) uses Pillow (for now, all external dependencies for created tools must be installed maually)

dotenv (for web search api key)
<h2>How to use:</h2>
Just run it! (No interface exept console right now)

Example:

Let's assume we want some arts of beautiful Evelyn from Zenless Zone Zero. 
We write a prompt:

"Find a pinterest page with Evelyn arts from Zenless Zone Zero in the internet. Scrape all the images and save them into folder, then compress the folder into zip file. Important: in pinterest the images are loaded like: \<link rel="preload" as="image" imagesrcset="https://i.pinimg.com/236x/1d/9b/cf/example1.jpg 1x, https://i.pinimg.com/474x/1d/9b/cf/example2.jpg 2x, https://i.pinimg.com/originals/1d/9b/example3.jpg 4x" fetchpriority="auto">. You need the THIRD ONE since it has better quality. "

It's important to specify the possible bottlenecks in the tasks while usng my agent. But if the prompt is good enough, the magic begins:

Step 1: tool listing.

<img width="603" height="72" alt="image" src="https://github.com/user-attachments/assets/d3ec0bbb-c496-4ced-aefe-8b6a6ea7d820" />

The agent tries to list the self-created tools tools he currently has. He sees he has nothing related to the task. This step is first and mandatory, now the agent will make his own decisions.

Step 2: Web search.

<img width="729" height="368" alt="image" src="https://github.com/user-attachments/assets/7c516dab-af38-46b1-9681-65c5a160b041" />

Currently I use a simple Langchain + SERP Talordata API module. This is a built-in module always avaliable for the agent. As you see, the agent forms a query by himself and gets the results he will use later.

Step 3: The tool creation.

<img width="1782" height="312" alt="image" src="https://github.com/user-attachments/assets/647efab2-95dc-4d74-9b10-b25e77e40599" />

Agent creates the python file with a tool he needs to fulfill the request. Then he includes it using the corresponding built-in tools. Then he just calls the newly created tool with a link from his memory and fulfills the request!

Step 4: Summary.

<img width="1517" height="303" alt="image" src="https://github.com/user-attachments/assets/b7c3eb56-c591-4dbb-b069-974b8c54c7e6" />

Agent just makes the summary of his actions.

The resulting art folder (not arts, mostly just screenshots and there are copies, but it's not agent's fault)

<img width="1752" height="986" alt="image" src="https://github.com/user-attachments/assets/d00845e9-673f-4e3a-87d7-f1d9cac5e6a3" />

Resulting project structure:

<img width="401" height="408" alt="image" src="https://github.com/user-attachments/assets/064e2341-5316-4fee-b972-8eab1a536595" />

You can see the new tool, the folder and the archive.


By the way, if we ask the agent the same task while the tool exists, he won't create new and straight up include the previously created tool.

<img width="1783" height="804" alt="image" src="https://github.com/user-attachments/assets/5051a8f0-1541-41a0-a864-bacdc8b5a7b6" />
