# LLM Provider Configuration Guide

This application supports multiple Large Language Model (LLM) providers for its chat functionality. You can switch between **Google Gemini** and **OpenAI** by configuring environment variables.

## Configuration Steps

Follow these steps to configure the LLM provider and API keys:

### 1. Create the Environment File

In the project root directory, you will find a file named `.env.example`. This is a template for your environment variables.

First, create a copy of this file and name it `.env`:

```bash
cp .env.example .env
```

### 2. Edit the `.env` File

Now, open the newly created `.env` file in your text editor. It will look like this:

```
# LLM Provider Settings
# Choose between "google" or "openai"
LLM_PROVIDER=google

# API Keys
# Add your API keys here. These will be loaded into the application environment.
GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"

# You can also specify the OpenAI model to use (optional)
# OPENAI_MODEL="gpt-4o"
```

### 3. Set the Variables

Modify the variables in the `.env` file according to your needs:

*   **`LLM_PROVIDER`**:
    *   Set this to `google` to use Google Gemini.
    *   Set this to `openai` to use OpenAI's models (e.g., GPT-4o).

*   **`GOOGLE_API_KEY`**:
    *   If you are using `google`, paste your API key obtained from [Google AI Studio](https://aistudio.google.com/app/apikey).

*   **`OPENAI_API_KEY`**:
    *   If you are using `openai`, paste your API key obtained from the [OpenAI Platform](https://platform.openai.com/api-keys).

*   **`OPENAI_MODEL`** (Optional):
    *   If you are using `openai`, you can uncomment and specify a model name, for example: `OPENAI_MODEL="gpt-4o"`. If left commented out, it will default to `gpt-4o`.

**Important:** The `.env` file is listed in `.gitignore` and will not be committed to your Git repository. This is a security measure to protect your API keys.

### 4. Restart the Application

After you have modified and saved the `.env` file, you need to restart the Docker containers for the changes to take effect.

Run the following commands in your terminal at the project root:

```bash
docker-compose down
docker-compose up --build -d
```

Your application will now be running with the LLM provider you configured.