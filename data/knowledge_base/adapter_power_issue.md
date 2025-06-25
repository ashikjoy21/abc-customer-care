{
  "issue_type": "adapter_power_issue",
  "sub_types": ["no_power", "adapter_failure", "plug_issue"],
  "troubleshooting": [
    {
      "id": "APW_001",
      "title": {
        "malayalam": "മോഡത്തിൽ വിളക്കൾ ഒന്നും തന്നെ കാണുന്നില്ല",
        "english": "No Lights Visible on Modem"
      },
      "urgency": "high",
      "category": "hardware",
      "device_types": ["fiber_modem"],
      "symptoms": {
        "malayalam": ["മോഡത്തിൽ ലൈറ്റുകൾ ഇല്ല", "മോഡം ഓൺ ആകുന്നില്ല", "പവർ ഇല്ല"],
        "english": ["no lights on modem", "modem not turning on", "no power"]
      },
      "keywords": ["no light", "no power", "adapter", "ലൈറ്റ് ഇല്ല", "പവർ ഇല്ല", "അഡാപ്റ്റർ"],
      "diagnosis": {
        "primary_check": {
          "malayalam": "മോഡത്തിൽ എന്തെങ്കിലും ലൈറ്റുകൾ കാണുന്നുണ്ടോ എന്ന് പരിശോധിക്കുക",
          "english": "Check if any lights are visible on the modem"
        },
        "questions": [
          {
            "malayalam": "പ്ലഗ് കണക്റ്റ് ചെയ്തിട്ടുണ്ടോ?",
            "english": "Is the plug connected?"
          },
          {
            "malayalam": "വേറെ പ്ലഗിൽ ടെസ്റ്റ് ചെയ്തു നോക്കിയോ?",
            "english": "Have you tried testing in a different plug socket?"
          },
          {
            "malayalam": "എപ്പോഴാണ് ഈ പ്രശ്നം തുടങ്ങിയത്?",
            "english": "When did this problem start?"
          }
        ]
      },
      "solution": {
        "immediate_action": {
          "malayalam": "ആദ്യം പ്ലഗ് സോക്കറ്റ് ഒന്ന് പരിശോധിക്കുക. വേറൊരു സോക്കറ്റിൽ ടെസ്റ്റ് ചെയ്ത് നോക്കുക. അഡാപ്റ്റർ ശരിയായി കണക്റ്റ് ചെയ്തിട്ടുണ്ടെന്ന് ഉറപ്പാക്കുക. അതിനുശേഷവും ലൈറ്റുകൾ കാണുന്നില്ലെങ്കിൽ, അഡാപ്റ്റർ പ്രശ്നമാകാം. (മോഡത്തിലെ റീസ്റ്റാർട്ട് ബട്ടൺ അമർത്തരുത്, ഇത് ഉപകരണത്തെ നശിപ്പിക്കാൻ കാരണമാകാം).",
          "english": "First, check the plug socket. Try testing in a different socket. Make sure the adapter is properly connected. If there are still no lights, it may be an adapter issue. (DO NOT press the restart button on the modem, as this may damage the device)."
        },
        "steps": [
          {
            "step": 1,
            "malayalam": "പ്ലഗ് സോക്കറ്റ് പരിശോധിക്കുക, വേറൊരു സോക്കറ്റിൽ ടെസ്റ്റ് ചെയ്ത് നോക്കുക.",
            "english": "Check the plug socket, try testing in a different socket.",
            "technical_details": "Verify if the issue is with the socket or the adapter. Ask customer to use a different plug socket if available."
          },
          {
            "step": 2,
            "malayalam": "അഡാപ്റ്റർ കണക്ഷനുകൾ ശരിയായി ഘടിപ്പിച്ചിട്ടുണ്ടോ എന്ന് ഉറപ്പാക്കുക. അഡാപ്റ്റർ മോഡത്തിൽ നിന്ന് വലിച്ചെടുത്ത് വീണ്ടും ഘടിപ്പിക്കുക.",
            "english": "Ensure adapter connections are properly fitted. Unplug and replug the adapter from the modem.",
            "technical_details": "Check for loose connections between adapter and modem. Reconnect firmly."
          },
          {
            "step": 3,
            "malayalam": "മുകളിലുള്ള നടപടികൾക്ക് ശേഷവും ലൈറ്റുകൾ വരുന്നില്ലെങ്കിൽ, അഡാപ്റ്റർ പ്രശ്നമായിരിക്കാം. ഒരു ടെക്നീഷ്യൻ സന്ദർശനം ആവശ്യമായി വരും, അവർ പുതിയ അഡാപ്റ്റർ കൊണ്ടുവരും.",
            "english": "If lights still don't appear after the above steps, it may be an adapter problem. A technician visit will be required, and they will bring a new adapter.",
            "technical_details": "Register for technician visit with priority 'high'. Mark 'replacement_adapter_needed' in technician notes."
          }
        ],
        "escalation": {
          "condition": "ലൈറ്റുകൾ വരുന്നില്ലെങ്കിൽ",
          "action": "technician_visit",
          "priority": "high",
          "technician_needs": ["replacement_adapter"],
          "visit_details": "Inform customer that technician will reach before evening or tomorrow morning. Sky Vision shop works between 10 AM to 5 PM. Do not specify exact time. Mention that technician will bring a replacement adapter."
        }
      },
      "success_indicators": ["മോഡത്തിൽ ലൈറ്റുകൾ തിരികെ വരുന്നു", "പവർ ഓൺ ആകുന്നു"],
      "resolution_time": "technician_visit_required",
      "customer_feedback_score": 4.3
    },
    {
      "id": "APW_002",
      "title": {
        "malayalam": "അഡാപ്റ്റർ ചൂടാകുന്നു",
        "english": "Adapter Getting Hot"
      },
      "urgency": "medium",
      "category": "hardware",
      "device_types": ["fiber_modem"],
      "symptoms": {
        "malayalam": ["അഡാപ്റ്റർ ചൂടാകുന്നു", "പവർ അഡാപ്റ്റർ ചൂട്", "മോഡം ചൂടാകുന്നു"],
        "english": ["adapter getting hot", "power adapter hot", "modem heating up"]
      },
      "keywords": ["hot", "heating", "adapter", "power supply", "ചൂട്", "അഡാപ്റ്റർ"],
      "diagnosis": {
        "primary_check": {
          "malayalam": "അഡാപ്റ്റർ തൊട്ടു നോക്കി അമിതമായ ചൂട് അനുഭവപ്പെടുന്നുണ്ടോ എന്ന് പരിശോധിക്കുക (കൈ കൊണ്ട് തൊടാൻ കഴിയുന്നില്ലെങ്കിൽ അത് വളരെ അപകടകരമാണ്)",
          "english": "Check if the adapter feels excessively hot to touch (if it's too hot to touch, it's dangerously hot)"
        },
        "questions": [
          {
            "malayalam": "എത്ര നേരമായി അഡാപ്റ്റർ ചൂടാകുന്നത്?",
            "english": "How long has the adapter been getting hot?"
          },
          {
            "malayalam": "ചൂടാകുമ്പോൾ ഇന്റർനെറ്റ് കണക്ഷനിൽ എന്തെങ്കിലും പ്രശ്നം ഉണ്ടാകുന്നുണ്ടോ?",
            "english": "Are there any issues with the internet connection when it gets hot?"
          }
        ]
      },
      "solution": {
        "immediate_action": {
          "malayalam": "അഡാപ്റ്റർ വളരെ ചൂടാണെങ്കിൽ, ഉടൻ തന്നെ പ്ലഗ് സ്വിച്ച് വഴി പവർ ഓഫ് ചെയ്യുക (മോഡത്തിലെ റീസ്റ്റാർട്ട് ബട്ടൺ അമർത്തരുത്). മറ്റ് വസ്തുക്കളിൽ നിന്ന് അകറ്റി, തണുക്കാൻ അനുവദിക്കുക. 30 മിനിറ്റ് കഴിഞ്ഞ് വീണ്ടും പവർ ഓൺ ചെയ്യുക. പ്രശ്നം തുടരുകയാണെങ്കിൽ, അഡാപ്റ്റർ മാറ്റേണ്ടതുണ്ട്.",
          "english": "If the adapter is very hot, immediately power off using the plug socket switch (DO NOT press the restart button on the modem). Keep it away from other objects and allow it to cool. Turn it back on after 30 minutes. If the problem persists, the adapter needs to be replaced."
        },
        "steps": [
          {
            "step": 1,
            "malayalam": "പ്ലഗ് സ്വിച്ച് വഴി പവർ ഓഫ് ചെയ്ത് അഡാപ്റ്റർ തണുക്കാൻ അനുവദിക്കുക (മോഡത്തിലെ റീസ്റ്റാർട്ട് ബട്ടൺ അമർത്തരുത്).",
            "english": "Power off using the plug socket switch and allow the adapter to cool (DO NOT press the restart button on the modem).",
            "technical_details": "Hot adapter can be a fire hazard. Instruct customer to turn off the power and let it cool down for at least 30 minutes."
          },
          {
            "step": 2,
            "malayalam": "അഡാപ്റ്റർ ഒരു എയർ വെന്റിലേറ്റഡ് സ്ഥലത്ത് വയ്ക്കുക, മറ്റ് വസ്തുക്കളിൽ നിന്ന് അകറ്റി വയ്ക്കുക.",
            "english": "Place the adapter in a well-ventilated area, away from other objects.",
            "technical_details": "Ensure adapter has proper airflow. Check if it's placed in a confined space or covered by materials that may cause overheating."
          },
          {
            "step": 3,
            "malayalam": "30 മിനിറ്റ് കഴിഞ്ഞ് വീണ്ടും പ്ലഗ് സ്വിച്ച് വഴി പവർ ഓൺ ചെയ്യുക. അമിതമായി ചൂടാകുന്നത് തുടരുകയാണെങ്കിൽ, ഒരു ടെക്നീഷ്യൻ സന്ദർശനം ആവശ്യമായി വരും.",
            "english": "Turn power back on using the plug socket switch after 30 minutes. If excessive heating continues, a technician visit will be required.",
            "technical_details": "Register for technician visit with priority 'medium'. Mark 'replacement_adapter_needed' in technician notes."
          }
        ],
        "escalation": {
          "condition": "അമിതമായി ചൂടാകുന്നത് തുടരുകയാണെങ്കിൽ",
          "action": "technician_visit",
          "priority": "medium",
          "technician_needs": ["replacement_adapter"],
          "visit_details": "Inform customer that technician will reach before evening or tomorrow morning. Sky Vision shop works between 10 AM to 5 PM. Do not specify exact time. Mention that technician will bring a replacement adapter."
        }
      },
      "success_indicators": ["അഡാപ്റ്റർ സാധാരണ താപനിലയിൽ പ്രവർത്തിക്കുന്നു"],
      "resolution_time": "30_minutes_or_technician",
      "customer_feedback_score": 4.1
    }
  ]
} 