import requests
import config as cfg
import re

# OpenRouter Chat API
def chat_request(prompt):
    headers = {
        "Authorization": f"Bearer {cfg.API_KEY}",
        "Content-Type": "application/json"
    }

    template = "Summarize briefly, avoiding extra details. Respond in simple, plain text without formatting."

    data = {
        "model": cfg.MODEL,
        "messages": [
            {"role": "system", "content": template}, 
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "max_tokens": 500,  # Reduce to prevent cutoff issues
        "stop": ["\n\n", "\n"],  # Encourage early stopping
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )

        response_json = response.json()
        choices = response_json.get("choices", [])

        print(f"🔹 API Response: {response.text.strip()}")  # Debugging

        # Handle empty responses
        if not choices or not choices[0]["message"].get("content", "").strip():
            return "⚠️ AI couldn't generate a valid response. Try rephrasing your query."

        return choices[0]["message"]["content"].strip()

    except requests.Timeout:
        return "⚠️ AI is taking too long. Try again later."
    except requests.RequestException as e:
        return f"⚠️ API request failed: {e}"


# Fetch chat summary
import datetime
from telethon.tl.functions.messages import GetHistoryRequest

async def fetch_chat_summary(app, chat_id, limit=100, user_id=None, keyword=None, time_range=None):
    """
    Fetches and summarizes chat messages with optional filters.
    
    :param app: Telegram client
    :param chat_id: Group or chat ID
    :param limit: Number of messages to fetch
    :param user_id: Summarize messages from a specific user (optional)
    :param keyword: Summarize messages containing a specific keyword (optional)
    :param time_range: Time window in hours (optional)
    :return: Summarized text
    """
    messages = []
    now = datetime.datetime.utcnow()

    async for message in app.iter_messages(chat_id, limit=limit):
        if not message.text:
            continue  # Skip non-text messages

        # Filter by user ID
        if user_id and message.sender_id != user_id:
            continue

        # Filter by keyword
        if keyword and keyword.lower() not in message.text.lower():
            continue

        # Filter by time range
        if time_range:
            time_diff = now - message.date.replace(tzinfo=None)
            if time_diff.total_seconds() > time_range * 3600:
                continue

        messages.append(message.text)

    if not messages:
        return "No relevant messages found for summarization."

    # Send messages to AI model for summarization
    headers = {
        "Authorization": f"Bearer {cfg.API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": cfg.MODEL,
        "messages": [
            {"role": "system", "content": "Summarize the following messages concisely."},
            {"role": "user", "content": "\n".join(messages)}
        ],
        "stream": False
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            return response.json().get("choices", [{}])[0].get("message", {}).get("content", "No summary available.")
        print(f"Summarization API Error: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"Summarization Request Error: {e}")

    return "Summarization failed."

# Keyword Tracking
def keyword_alert(text):
    keywords = cfg.TRACKED_KEYWORDS  # Example: ["crypto", "bitcoin", "update"]
    matched = [kw for kw in keywords if kw.lower() in text.lower()]

    if matched:
        return f"🚀 **Keyword Alert!** These topics were mentioned: {', '.join(matched)}"
    
    return None
