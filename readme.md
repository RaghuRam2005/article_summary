
# LLM-Based Article summary

## Overview

This project is designed to summarize ariticles that are on internet using a Large Language Model (LLM). The system integrates with an API to scrape content from the internet and uses an API to serve the LLM-generated answers. A simple front-end interface is provided to interact with the system.

## Process Overview

1. **User Input via Streamlit Interface**:
   - The user interacts with a Streamlit-based front-end where they can input their query.

2. **Query Sent to Flask Backend**:
   - The query entered by the user is sent from the Streamlit interface to a Flask backend via an API call.

3. **Internet Search and Article Scraping**:
   - The Flask backend searches the internet for the query using a designated API. It retrieves the top relevant articles and scrapes their content, extracting only the useful text (headings and paragraphs).

4. **Content Processing**:
   - The scraped content is processed to create a coherent input, which is then passed to the LLM for generating a response.

5. **LLM Response Generation**:
   - The processed content and the user's query are used to generate a contextual answer using the LLM. The LLM is accessed via an API, and the generated response is returned to the Flask backend.

6. **Response Sent Back to Streamlit Interface**:
   - The Flask backend sends the generated answer back to the Streamlit interface, where it is displayed to the user.

## Setup Instructions

### Step 1: Clone or download the Repository

```bash
git clone https://github.com/RaghuRam2005/llm_based_search.git
```

Or download it and navigate to the folder it is in

```bash
cd llm
```

### Step 2: Setup the API key

Go to google AI studio and generate API key and create a `.env` file in `flask_app` folder.
Note: This API key are not free and are charged based on the usages

### Step 3: Installing required libraries

We will now install the libraries required to run the program, we can do it using:

```bash
pip install -r requirements.txt
```

### Step 4: running the application

Now in `llm_based_search` folder run the following commands to start and run the Application:

```bash
python ./flask_app/app.py
```

Then open another terminal and run the command

```bash
streamlit run ./streamlit/app.py
```

### Step 4: Open the Application

Open your web browser and go to `http://localhost:8501`. You can now interact with the system by entering your query.

### Note

If there is any error while running the code use a virtual environment to run it.

## Project Structure

- **flask_app/**: Contains the backend Flask API and utility functions.
- **streamlit_app/**: Contains the Streamlit front-end code.
- **.env**: Stores API keys (make sure this file is not included in version control).
- **requirements.txt**: Lists the project dependencies.
