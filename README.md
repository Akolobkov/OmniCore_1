<img width="603" height="362" alt="image" src="https://github.com/user-attachments/assets/9aa5000c-ac4e-4310-bac8-9eac9fe02f91" /><h1>OmniCore - a self-tool-creating agent</h1>
Warning! the project is on the early development stages. The best support is feedback.
The agent on current stage is able to one-shot create AND use tools fitting for the task to complete it, therefore being able to complete a vast spectre of simple tasks including web search, parsing, working with documents, running code, scraping, etc.  
<h2>Setup</h2>
Ollama - the project was build and tested using gemma4
Langchain (python library) - agent framework
The web search tool uses Talordata api (api provider can be changed)
Example tool (create_gradient_image) uses Pillow (for now, all externl dependencies for created tools must be installed maually)
dotenv (for web search api key)
<h2>How to use:</h2>
Just run it! (No iterface exept console RN)
Example:
