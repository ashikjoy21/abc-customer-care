# Sat Vision Customer Support Bot

This is a customized implementation of the customer support bot for Sat Vision cable TV company. The bot welcomes customers, verifies their identity using their phone number, and provides troubleshooting assistance for cable TV issues.

## Features

- **Sat Vision Branding**: The bot identifies itself as a Sat Vision support agent
- **Phone Number Verification**: Asks for and verifies customer phone numbers at the start of the conversation
- **Customer Recognition**: Greets customers by name after verification
- **Troubleshooting Assistance**: Provides solutions for common cable TV issues
- **Multilingual Support**: Communicates in Malayalam and English
- **Content Filtering**: Filters inappropriate content and handles speech recognition errors

## Implementation Details

The following changes were made to the original bot:

1. Updated the bot's introduction to identify as Sat Vision
2. Modified the initial greeting to ask for the customer's phone number
3. Added automatic phone number collection at the start of each call
4. Updated the operator name to "Sat Vision" in customer information
5. Added reminders for phone number entry if the user speaks instead of using DTMF
6. Created a simplified demo script that shows the conversation flow
7. Added a content filtering system to handle inappropriate content and speech recognition errors

## Content Filtering

The bot includes a comprehensive content filtering system that:

- Filters out inappropriate words from transcribed speech
- Detects potentially inappropriate queries
- Provides appropriate responses when inappropriate content is detected
- Logs filtered content for monitoring

For more details, see [CONTENT_FILTER.md](CONTENT_FILTER.md).

## Usage

### Running the Demo

```bash
python sat_vision_demo.py
```

This will run a simulated conversation showing how the bot interacts with customers.

### Running the Full Bot

```bash
python main.py
```

This will start the full voicebot server that can handle incoming calls.

## Troubleshooting

If you encounter dependency issues with sentence-transformers or huggingface_hub, you can use the simplified RAG implementation:

```bash
python simple_demo.py
```

This uses a simplified version of the RAG system that doesn't require external embedding libraries.

## Sample Conversation

1. **Bot**: "സാറ്റ് വിഷനിലേക്ക് സ്വാഗതം! ഞങ്ങൾ നിങ്ങളെ സഹായിക്കാൻ സന്തോഷിക്കുന്നു. നിങ്ങളുടെ അക്കൗണ്ട് പരിശോധിക്കുന്നതിന് ദയവായി നിങ്ങളുടെ 10 അക്ക ഫോൺ നമ്പർ നൽകുക."
   (Welcome to Sat Vision! We're happy to help you. Please enter your 10-digit phone number to verify your account.)

2. **User**: *enters phone number via keypad*

3. **Bot**: "നമസ്കാരം [Customer Name]! സാറ്റ് വിഷനിൽ നിന്നും സ്വാഗതം. എന്താണ് പ്രശ്നം?"
   (Hello [Customer Name]! Welcome from Sat Vision. What's the problem?)

4. **User**: "എന്റെ ടിവിയിൽ സിഗ്നൽ കിട്ടുന്നില്ല. റെഡ് ലൈറ്റ് കാണിക്കുന്നു."
   (I'm not getting a signal on my TV. It's showing a red light.)

5. **Bot**: *provides troubleshooting steps* 