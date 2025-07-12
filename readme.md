
# Keyword Based RAG summary

## Overview

This project is designed to take a keyword from user like artificial Intelligence, cryptography, etc. It will search various
content based on the keyword and summarizes the content for the user.

## Setup Instructions

### Step 1: Clone or download the Repository

```bash
git clone https://github.com/RaghuRam2005/article_summary.git
```

Or download it and navigate to the folder it is in

```bash
cd article_summary
```

### Step 2: Setup the API key

Generate a Gemini API key using the [AI Studio](https://aistudio.google.com/apikey) website.

### Note: This may incur some charges, so please review your API usage and billing details on the AI Studio dashboard

Create a `.env` file in `flask_app` folder and paste your API key there

```bash
GEMINI_API = <your API key>
```

### Step 3: Installing required libraries

Install the required libraries using the command

```bash
pip install -r requirements.txt
```

### Step 3: running the application

Now in `article_summmary` folder run the following commands to start and run the Application

**In Terminal 1:**

```bash
python ./flask_app/app.py
```

**In Terminal 2:**

```bash
npm install
npm run dev
```

### Step 4: Open the Application

Open your web browser and go to `http://localhost:8501`. You can now interact with the system by entering your query.

### Note

If there is any error while running the code use a virtual environment to run it.

## Project Structure

- **flask_app/**: Contains the backend Flask API and utility functions.
- **streamlit_app/**: Contains the Streamlit front-end code.
- **requirements.txt**: Lists the project dependencies.
