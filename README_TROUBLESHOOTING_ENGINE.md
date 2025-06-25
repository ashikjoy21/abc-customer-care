# Structured Troubleshooting Engine

This document outlines the implementation of the structured troubleshooting framework for the Stavision Bot, designed to improve issue resolution and reduce unnecessary escalations.

## Overview

The structured troubleshooting framework introduces a systematic approach to troubleshooting customer issues. It consists of several key components:

1. **TroubleshootingEngine**: Core engine that manages troubleshooting flows
2. **CallMemoryEnhanced**: Enhanced call memory that integrates with the troubleshooting engine
3. **ExotelBotEnhanced**: Enhanced bot that uses the structured troubleshooting framework
4. **IssueClassifier**: Advanced issue classifier that identifies main issues and sub-issues
5. **StepPrioritizer**: Intelligent prioritization of troubleshooting steps

## Components

### TroubleshootingEngine

The `TroubleshootingEngine` class is responsible for:

- Loading troubleshooting flows from knowledge base files
- Classifying issues based on user input
- Managing step-by-step troubleshooting flows
- Determining when to escalate issues
- Tracking troubleshooting progress and success rates
- Prioritizing steps based on multiple factors

Key features:
- Issue classification based on keywords and conversation history
- Structured decision trees for troubleshooting steps
- Smart escalation criteria
- Troubleshooting summary generation
- Integration with advanced issue classification
- Step prioritization based on success probability and customer profile

### CallMemoryEnhanced

The `CallMemoryEnhanced` class extends the original `CallMemory` class with:

- Integration with the troubleshooting engine
- Enhanced tracking of troubleshooting steps
- Improved context management for issue resolution
- Detailed troubleshooting summaries
- Customer technical profile management
- Sub-issue tracking and confidence scoring

### ExotelBotEnhanced

The `ExotelBotEnhanced` class enhances the original `ExotelBot` with:

- Integration with the structured troubleshooting framework
- Improved conversation flow
- Better escalation handling
- Enhanced call summaries
- Technical level assessment for customers
- Prioritized troubleshooting steps

### IssueClassifier

The `IssueClassifier` class provides advanced issue classification:

- Multi-language keyword-based classification (Malayalam and English)
- Sub-issue detection for more specific troubleshooting
- Confidence scoring for classification results
- Technical context extraction from user descriptions
- Conversation history analysis for better context

### StepPrioritizer

The `StepPrioritizer` class intelligently prioritizes troubleshooting steps:

- Success probability calculation based on historical data
- Step complexity assessment
- Technical level matching with customer profile
- Time estimation for steps
- Dependency management between steps
- Self-learning from success/failure outcomes

## Knowledge Base Structure

The troubleshooting engine uses structured knowledge base files in the `data/knowledge_base` directory. These files define:

- Decision trees for issue classification
- Step-by-step troubleshooting flows
- Escalation criteria
- Success indicators

Example structure of a knowledge base file:

```json
{
  "common_patterns": {
    "escalation_triggers": ["multiple_devices", "business_customer", "recurring_issue"],
    "immediate_resolution": ["check_payment", "restart_modem"]
  },
  "decision_tree": {
    "root_question": {
      "malayalam": "എന്താണ് പ്രശ്നം?",
      "english": "What is the issue?"
    },
    "branches": [
      {
        "condition": "no internet",
        "route_to": "internet_down_scenario"
      },
      {
        "condition": "slow internet",
        "route_to": "slow_internet_scenario"
      }
    ]
  },
  "scenarios": [
    {
      "id": "internet_down_scenario",
      "description": "Internet not working at all",
      "solution": {
        "steps": [
          {
            "step": 1,
            "malayalam": "മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക",
            "english": "Restart your modem",
            "technical_details": "Power cycle the modem to clear temporary issues"
          },
          {
            "step": 2,
            "malayalam": "കേബിൾ കണക്ഷനുകൾ പരിശോധിക്കുക",
            "english": "Check cable connections",
            "technical_details": "Ensure all cables are properly connected"
          }
        ],
        "escalation": {
          "condition": "If problem persists after all steps",
          "priority": "medium"
        }
      }
    }
  ]
}
```

## How It Works

1. **Issue Classification**:
   - When a customer describes their problem, the system classifies it into predefined issue types
   - Classification uses keyword matching and conversation context
   - Sub-issues are detected for more specific troubleshooting
   - Confidence scores indicate the reliability of classification

2. **Customer Technical Profile**:
   - The system assesses the customer's technical level
   - Technical level is determined from customer history or interaction patterns
   - Profile includes patience level and success history

3. **Structured Troubleshooting**:
   - The system starts with a root question to confirm the issue
   - Based on the response, it navigates through a decision tree
   - Each step provides instructions in Malayalam and English
   - The system tracks success/failure of each step

4. **Special Case Handling**:
   - The system handles special cases like "Normal lights but no internet"
   - For these cases, it checks if the WiFi name is the same or different
   - Based on the WiFi name check, it determines if a technician visit is required
   - Both same name and different name scenarios may require technician visits for different reasons

5. **Step Prioritization**:
   - Steps are prioritized based on:
     - Historical success probability
     - Step complexity vs. customer technical level
     - Estimated time to complete
     - Dependencies between steps
   - The most promising steps are tried first

6. **Smart Escalation**:
   - The system uses multiple criteria to decide when to escalate:
     - Number of failed troubleshooting steps
     - Presence of escalation triggers in the conversation
     - Exhaustion of all troubleshooting steps
     - Detection of specific sub-issues requiring technician
     - Customer explicitly requesting escalation
   - When escalating to a technician visit:
     - Inform customers that technicians will reach before evening or tomorrow morning
     - Note that Sky Vision shop works between 10 AM to 5 PM
     - Never specify exact times for technician visits
     - Always provide realistic timeframes
     - Do not ask for customer's preferred time

7. **Progress Tracking**:
   - All troubleshooting steps are tracked in the call memory
   - Success and failure rates are calculated
   - Detailed summaries are generated for technicians

## Usage

To use the enhanced bot with structured troubleshooting:

```bash
python main_enhanced.py
```

Optional arguments:
- `--host`: Host to bind the WebSocket server (default: localhost)
- `--port`: Port to bind the WebSocket server (default: 8765)

## Benefits

1. **Increased First-Call Resolution**: By exhausting all troubleshooting options before escalation
2. **Reduced Technician Visits**: By solving more issues remotely
3. **Improved Customer Experience**: Through structured, step-by-step guidance
4. **Enhanced Knowledge Base**: Through tracking of successful troubleshooting patterns
5. **Operational Efficiency**: By allowing technicians to focus on complex issues
6. **Personalized Support**: By adapting to customer technical level
7. **Continuous Improvement**: Through self-learning from outcomes

## Future Enhancements

1. **Self-Learning Capabilities**: Automatically update success probabilities based on historical data
2. **Multi-Issue Handling**: Handle multiple issues in a single call
3. **Personalized Troubleshooting**: Further adapt flows based on customer technical level
4. **Integration with Diagnostic Tools**: Automatically check network status and device diagnostics
5. **Predictive Issue Resolution**: Anticipate issues before they occur based on patterns