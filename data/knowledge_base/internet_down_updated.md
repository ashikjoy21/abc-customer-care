{
  "knowledge_base": {
    "metadata": {
      "version": "1.0",
      "language": ["malayalam", "english"],
      "domain": "network_troubleshooting",
      "last_updated": "2024-06-14",
      "total_scenarios": 8,
      "avg_resolution_time": "15-30 minutes"
    },
    "scenarios": [
      {
        "id": "NET_001",
        "title": {
          "malayalam": "മോഡം പവർ പ്രശ്‌നം",
          "english": "Modem Power Issue"
        },
        "urgency": "high",
        "category": "hardware",
        "device_types": ["fiber_modem", "adsl_modem"],
        "symptoms": {
          "malayalam": ["മോഡത്തിൽ ലൈറ്റ് വരുന്നില്ല", "മോഡം ഓൺ ആകുന്നില്ല", "പവർ ഇല്ല"],
          "english": ["no lights on modem", "modem not turning on", "no power"]
        },
        "keywords": ["modem", "power", "light", "adapter", "ലൈറ്റ്", "പവർ", "മോഡം", "അഡാപ്റ്റർ"],
        "diagnosis": {
          "primary_check": {
            "malayalam": "മോഡത്തിൽ ലൈറ്റ് വരുന്നുണ്ടോ എന്ന് പരിശോധിക്കുക",
            "english": "Check if modem lights are on"
          },
          "questions": [
            {
              "malayalam": "മോഡത്തിൽ എന്തെങ്കിലും ലൈറ്റുകൾ കാണുന്നുണ്ടോ, അതിൽ ഏതെങ്കിലും ചുവന്ന ലൈറ്റ് ഉണ്ടോ?",
              "english": "Are there any lights on the modem, and is any of them red?"
            },
            {
              "malayalam": "മോഡത്തിൽ എന്തെങ്കിലും ചുവന്ന ലൈറ്റ് ഉണ്ടോ?",
              "english": "Is there any red light on the modem?"
            },
            {
              "malayalam": "മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്തിട്ടുണ്ടോ? മോഡം പൂർണ്ണമായും ഓൺലൈൻ ആകാൻ 5 മിനിറ്റ് എടുക്കും. ദയവായി 5 മിനിറ്റ് കാത്തിരിക്കുക. 5 മിനിറ്റിനു ശേഷവും പ്രശ്നം നിലനിൽക്കുന്നുവെങ്കിൽ മാത്രം, ഞങ്ങളെ വീണ്ടും വിളിക്കുക.",
              "english": "Have you powered off and on the modem through the plug switch? The modem takes about 5 minutes to be fully online. Please wait for 5 minutes. ONLY call us back if the issue persists after 5 minutes."
            }
          ]
        },
        "solution": {
          "steps": [
            {
              "step": 1,
              "malayalam": "അഡാപ്റ്റർ കണക്ഷൻ പരിശോധിക്കുക",
              "english": "Check adapter connection",
              "technical_details": "Verify power adapter is securely connected to modem and wall outlet"
            },
            {
              "step": 2,
              "malayalam": "വൈദ്യുതി സപ്ലൈ പരിശോധിക്കുക",
              "english": "Check power supply",
              "technical_details": "Test wall outlet with another device"
            },
            {
              "step": 3,
              "malayalam": "മോഡം കംപ്ലൈന്റ് രജിസ്റ്റർ ചെയ്യുക",
              "english": "Register modem complaint",
              "technical_details": "Log hardware replacement request"
            }
          ],
          "escalation": {
            "condition": "അഡാപ്റ്റർ പരിശോധനയ്ക്ക് ശേഷവും പ്രശ്‌നം പരിഹരിക്കപ്പെടുന്നില്ലെങ്കിൽ",
            "action": "technician_visit",
            "priority": "high",
            "visit_details": "Inform customer that technician will reach before evening or tomorrow morning. Sky Vision shop works between 10 AM to 5 PM. Do not specify exact time."
          }
        },
        "success_indicators": ["മോഡം ലൈറ്റുകൾ തെളിയുന്നു", "പവർ സ്റ്റേബിൾ ആണ്"],
        "resolution_time": "immediate_or_technician",
        "customer_feedback_score": 4.2
      },
      {
        "id": "NET_002",
        "title": {
          "malayalam": "ഫൈബർ ബ്രേക്ക് പ്രശ്‌നം",
          "english": "Fiber Break Issue"
        },
        "urgency": "critical",
        "category": "infrastructure",
        "device_types": ["fiber_modem"],
        "symptoms": {
          "malayalam": ["റെഡ് ലൈറ്റ് തെളിയുന്നു", "ചുവന്ന ലൈറ്റ് കാണുന്നു", "സിഗ്നൽ ഇല്ല"],
          "english": ["red light showing", "fiber signal lost", "no connection"]
        },
        "keywords": ["red light", "fiber", "break", "signal", "റെഡ് ലൈറ്റ്", "ഫൈബർ", "സിഗ്നൽ"],
        "diagnosis": {
          "primary_check": {
            "malayalam": "മോഡത്തിൽ റെഡ് ലൈറ്റ് തെളിഞ്ഞിട്ടുണ്ടോ എന്ന് പരിശോധിക്കുക",
            "english": "Check if red light is showing on modem"
          },
          "questions": [
            {
              "malayalam": "മോഡത്തിൽ എന്തെങ്കിലും ലൈറ്റുകൾ കാണുന്നുണ്ടോ, അതിൽ ഏതെങ്കിലും ചുവന്ന ലൈറ്റ് ഉണ്ടോ?",
              "english": "Are there any lights on the modem, and is any of them red?"
            },
            {
              "malayalam": "മോഡത്തിൽ എന്തെങ്കിലും ചുവന്ന ലൈറ്റ് ഉണ്ടോ?",
              "english": "Is there any red light on the modem?"
            },
            {
              "malayalam": "എപ്പോൾ മുതൽ ഈ പ്രശ്‌നം ഉണ്ട്?",
              "english": "Since when has this problem existed?"
            }
          ]
        },
        "solution": {
          "immediate_action": {
            "malayalam": "ആദ്യം മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക. മോഡം പൂർണ്ണമായും ഓൺലൈൻ ആകാൻ 5 മിനിറ്റ് എടുക്കും. 5 മിനിറ്റിനു ശേഷവും പ്രശ്നം നിലനിൽക്കുന്നുവെങ്കിൽ, ദയവായി ഞങ്ങളെ വീണ്ടും വിളിക്കുക.",
            "english": "First, power off and on the modem through the plug switch. The modem takes about 5 minutes to be fully online. If the issue persists after 5 minutes, please call us back."
          },
          "steps": [
            {
              "step": 1,
              "malayalam": "മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക. മോഡം പൂർണ്ണമായും ഓൺലൈൻ ആകാൻ 5 മിനിറ്റ് എടുക്കും.",
              "english": "Power off and on the modem through the plug switch. The modem takes about 5 minutes to be fully online.",
              "technical_details": "Power off from the plug switch, wait for 30 seconds, then power on. Modem will take about 5 minutes to be fully online."
            },
            {
              "step": 2,
              "malayalam": "5 മിനിറ്റിനു ശേഷവും പ്രശ്നം നിലനിൽക്കുന്നുവെങ്കിൽ, ദയവായി ഞങ്ങളെ വീണ്ടും വിളിക്കുക, അപ്പോൾ ഫൈബർ ബ്രേക്ക് കംപ്ലൈന്റ് രജിസ്റ്റർ ചെയ്യും",
              "english": "If the issue persists after 5 minutes, please call us back and we will register a fiber break complaint",
              "technical_details": "Priority complaint - infrastructure team notification"
            }
          ],
          "escalation": {
            "condition": "5 മിനിറ്റിനു ശേഷവും റെഡ് ലൈറ്റ് കാണുന്നുവെങ്കിൽ",
            "action": "technician_visit",
            "priority": "critical"
          }
        },
        "success_indicators": ["റെഡ് ലൈറ്റ് ഓഫ് ആകുന്നു", "നോർമൽ കണക്റ്റിവിറ്റി പുനഃസ്ഥാപിക്കപ്പെടുന്നു"],
        "resolution_time": "4-24_hours",
        "customer_feedback_score": 4.0
      },
      {
        "id": "NET_003",
        "title": {
          "malayalam": "WiFi നെയിം മാറ്റം (റീസെറ്റ് പ്രശ്‌നം)",
          "english": "WiFi Name Change (Reset Issue)"
        },
        "urgency": "medium",
        "category": "configuration",
        "device_types": ["wifi_router", "fiber_modem"],
        "symptoms": {
          "malayalam": ["വ്യത്യസ്ത WiFi പേര് കാണുന്നു", "പുതിയ നെറ്റ്‌വർക്ക് പേര്"],
          "english": ["different wifi name showing", "new network name"]
        },
        "keywords": ["wifi", "name", "reset", "configuration", "വൈഫൈ", "പേര്", "റീസെറ്റ്"],
        "diagnosis": {
          "primary_check": {
            "malayalam": "WiFi ലിസ്റ്റിൽ നെറ്റ്‌വർക്ക് പേര് പരിശോധിക്കുക",
            "english": "Check network name in WiFi list"
          },
          "questions": [
            {
              "malayalam": "മോഡത്തിന്റെ അടുത്ത് കണക്റ്റ് ആകുന്നുണ്ടോ?",
              "english": "Does it connect near the modem?"
            },
            {
              "malayalam": "എത്ര ദൂരം വരെ കണക്റ്റ് ആകുന്നു?",
              "english": "Up to what distance does it connect?"
            },
            {
              "malayalam": "മുമ്പ് ഇത്രയും ദൂരെ കണക്റ്റ് ആയിരുന്നോ?",
              "english": "Did it connect this far before?"
            }
          ]
        },
        "solution": {
          "condition_analysis": {
            "if_same_name": {
              "malayalam": "സേം പേര് കാണുന്നെങ്കിൽ മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക. മോഡം പൂർണ്ണമായും ഓൺലൈൻ ആകാൻ 5 മിനിറ്റ് എടുക്കും. 5 മിനിറ്റിനു ശേഷവും പ്രശ്നം നിലനിൽക്കുന്നുവെങ്കിൽ, ദയവായി ഞങ്ങളെ വീണ്ടും വിളിക്കുക.",
              "english": "If same name shows, power off and on the modem through the plug switch. The modem takes about 5 minutes to be fully online. If the issue persists after 5 minutes, please call us back.",
              "action": "restart_modem_then_technician_if_needed"
            },
            "if_different_name": {
              "malayalam": "വ്യത്യസ്ത പേര് കാണുന്നെങ്കിൽ ആദ്യം മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക. മോഡം പൂർണ്ണമായും ഓൺലൈൻ ആകാൻ 5 മിനിറ്റ് എടുക്കും. 5 മിനിറ്റിനു ശേഷവും പ്രശ്നം നിലനിൽക്കുന്നുവെങ്കിൽ, ദയവായി ഞങ്ങളെ വീണ്ടും വിളിക്കുക.",
              "english": "If different name shows, first power off and on the modem through the plug switch. The modem takes about 5 minutes to be fully online. If the issue persists after 5 minutes, please call us back.",
              "action": "restart_modem_then_technician_if_needed"
            }
          },
          "steps": [
            {
              "step": 1,
              "malayalam": "മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക. മോഡം പൂർണ്ണമായും ഓൺലൈൻ ആകാൻ 5 മിനിറ്റ് എടുക്കും. 5 മിനിറ്റിനു ശേഷവും പ്രശ്നം നിലനിൽക്കുന്നുവെങ്കിൽ, ദയവായി ഞങ്ങളെ വീണ്ടും വിളിക്കുക.",
              "english": "Power off and on the modem through the plug switch. The modem takes about 5 minutes to be fully online. If the issue persists after 5 minutes, please call us back.",
              "technical_details": "Power off from the plug switch, wait for 30 seconds, then power on. Modem will take about 5 minutes to be fully online. Ask customer to call back if issue persists after 5 minutes."
            },
            {
              "step": 2,
              "malayalam": "കോൺഫിഗറേഷൻ റീസ്റ്റോർ ചെയ്യാൻ ടെക്‌നീഷ്യനെ അയക്കുക",
              "english": "Send technician to restore configuration",
              "technical_details": "Reconfigure WiFi name, password, and other settings. Inform customer that technician will reach before evening or tomorrow morning. Sky Vision shop works between 10 AM to 5 PM. Do not specify exact time."
            }
          ],
          "escalation": {
            "condition": "കോൺഫിഗറേഷൻ റീസെറ്റ് ആയാൽ",
            "action": "technician_visit",
            "priority": "medium"
          }
        },
        "success_indicators": ["യഥാർത്ഥ WiFi പേര് പുനഃസ്ഥാപിക്കപ്പെടുന്നു"],
        "resolution_time": "technician_visit_required",
        "customer_feedback_score": 4.1
      },
      {
        "id": "NET_004",
        "title": {
          "malayalam": "സ്ലോ ഇന്റർനെറ്റ് പ്രശ്‌നം",
          "english": "Slow Internet Issue"
        },
        "urgency": "medium",
        "category": "performance",
        "device_types": ["fiber_modem", "wifi_router"],
        "symptoms": {
          "malayalam": ["നെറ്റ് സ്ലോ ആണ്", "പേജ് കയറ്റിക്കൊണ്ടിരിക്കുന്നു", "സ്പീഡ് കുറവാണ്"],
          "english": ["internet is slow", "pages loading slowly", "low speed"]
        },
        "keywords": ["slow", "speed", "performance", "loading", "സ്ലോ", "സ്പീഡ്", "പേജ്"],
        "diagnosis": {
          "primary_check": {
            "malayalam": "കണക്റ്റിവിറ്റി സ്റ്റാറ്റസും സ്പീഡും പരിശോധിക്കുക",
            "english": "Check connectivity status and speed"
          },
          "questions": [
            {
              "malayalam": "എത്ര ഡിവൈസുകൾ കണക്റ്റ് ചെയ്തിട്ടുണ്ട്?",
              "english": "How many devices are connected?"
            },
            {
              "malayalam": "എല്ലാ ഡിവൈസിലും സ്ലോ ആണോ?",
              "english": "Is it slow on all devices?"
            },
            {
              "malayalam": "പേജുകൾ ലോഡ് ആകുന്നുണ്ടോ അതോ വേണ്ടത്ര ഫാസ്റ്റ് അല്ലേ?",
              "english": "Are pages loading but slowly, or not loading at all?"
            }
          ]
        },
        "solution": {
          "troubleshooting_steps": [
            {
              "step": 1,
              "malayalam": "മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക. മോഡം പൂർണ്ണമായും ഓൺലൈൻ ആകാൻ 5 മിനിറ്റ് എടുക്കും. 5 മിനിറ്റിനു ശേഷവും പ്രശ്നം നിലനിൽക്കുന്നുവെങ്കിൽ, ദയവായി ഞങ്ങളെ വീണ്ടും വിളിക്കുക.",
              "english": "Power off and on the modem through the plug switch. The modem takes about 5 minutes to be fully online. If the issue persists after 5 minutes, please call us back.",
              "technical_details": "Power off from the plug switch, wait for 30 seconds, then power on. Modem will take about 5 minutes to be fully online. Ask customer to call back if issue persists after 5 minutes."
            },
            {
              "step": 2,
              "malayalam": "കണക്റ്റ് ചെയ്ത ഡിവൈസുകളുടെ എണ്ണം പരിശോധിക്കുക",
              "english": "Check number of connected devices",
              "technical_details": "Disconnect unnecessary devices"
            },
            {
              "step": 3,
              "malayalam": "വയർഡ് കണക്ഷൻ ടെസ്റ്റ് ചെയ്യുക",
              "english": "Test wired connection",
              "technical_details": "Direct ethernet connection to modem"
            }
          ],
          "escalation": {
            "condition": "അടിസ്ഥാന ട്രബിൾഷൂട്ടിംഗിന് ശേഷവും പ്രശ്‌നം നിലനിൽക്കുന്നെങ്കിൽ",
            "action": "technician_visit",
            "priority": "medium",
            "visit_details": "Inform customer that technician will reach before evening or tomorrow morning. Sky Vision shop works between 10 AM to 5 PM. Do not specify exact time."
          }
        },
        "success_indicators": ["നോർമൽ സ്പീഡ് ലഭിക്കുന്നു", "പേജുകൾ വേഗത്തിൽ ലോഡ് ആകുന്നു"],
        "resolution_time": "15-30_minutes_or_technician",
        "customer_feedback_score": 3.8
      },
      {
        "id": "NET_005",
        "title": {
          "malayalam": "WiFi റേഞ്ച് പ്രശ്‌നം",
          "english": "WiFi Range Issue"
        },
        "urgency": "low",
        "category": "coverage",
        "device_types": ["wifi_router"],
        "symptoms": {
          "malayalam": ["റേഞ്ച് കിട്ടുന്നില്ല", "ദൂരെ കണക്റ്റ് ആകുന്നില്ല", "സിഗ്നൽ കുറവാണ്"],
          "english": ["no range", "can't connect from distance", "weak signal"]
        },
        "keywords": ["range", "distance", "signal", "weak", "റേഞ്ച്", "ദൂരം", "സിഗ്നൽ"],
        "diagnosis": {
          "primary_check": {
            "malayalam": "WiFi സിഗ്നൽ സ്ട്രെന്ത്തും കവറേജും പരിശോധിക്കുക",
            "english": "Check WiFi signal strength and coverage"
          },
          "questions": [
            {
              "malayalam": "മോഡത്തിന്റെ അടുത്ത് കണക്റ്റ് ആകുന്നുണ്ടോ?",
              "english": "Does it connect near the modem?"
            },
            {
              "malayalam": "എത്ര ദൂരം വരെ കണക്റ്റ് ആകുന്നു?",
              "english": "Up to what distance does it connect?"
            },
            {
              "malayalam": "മുമ്പ് ഇത്രയും ദൂരെ കണക്റ്റ് ആയിരുന്നോ?",
              "english": "Did it connect this far before?"
            }
          ]
        },
        "solution": {
          "assessment": {
            "malayalam": "WiFi റേഞ്ച് പ്രശ്‌നങ്ങൾ സാധാരണയായി ഫിസിക്കൽ ലിമിറ്റേഷനുകളാണ്",
            "english": "WiFi range issues are usually physical limitations"
          },
          "steps": [
            {
              "step": 1,
              "malayalam": "മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക. മോഡം പൂർണ്ണമായും ഓൺലൈൻ ആകാൻ 5 മിനിറ്റ് എടുക്കും. 5 മിനിറ്റിനു ശേഷവും പ്രശ്നം നിലനിൽക്കുന്നുവെങ്കിൽ, ദയവായി ഞങ്ങളെ വീണ്ടും വിളിക്കുക.",
              "english": "Power off and on the modem through the plug switch. The modem takes about 5 minutes to be fully online. If the issue persists after 5 minutes, please call us back.",
              "technical_details": "Power off from the plug switch, wait for 30 seconds, then power on. Modem will take about 5 minutes to be fully online. Ask customer to call back if issue persists after 5 minutes."
            },
            {
              "step": 2,
              "malayalam": "മോഡത്തിന്റെ പൊസിഷൻ ഒപ്റ്റിമൈസ് ചെയ്യുക",
              "english": "Optimize modem position",
              "technical_details": "Central location, elevated, away from obstacles"
            },
            {
              "step": 3,
              "malayalam": "WiFi എക്സ്റ്റെൻഡർ/റിപ്പീറ്റർ സൊല്യൂഷൻ നിർദ്ദേശിക്കുക",
              "english": "Suggest WiFi extender/repeater solution",
              "technical_details": "Additional hardware for extended coverage"
            }
          ],
          "escalation": {
            "condition": "വിപുലമായ കവറേജ് ആവശ്യമെങ്കിൽ",
            "action": "sales_consultation",
            "priority": "low"
          }
        },
        "success_indicators": ["ആവശ്യമുള്ള ഏരിയയിൽ കണക്റ്റിവിറ്റി", "സ്റ്റേബിൾ സിഗ്നൽ"],
        "resolution_time": "consultation_or_additional_equipment",
        "customer_feedback_score": 3.5
      },
      {
        "id": "NET_006",
        "title": {
          "malayalam": "മോഡം ലൈറ്റ് ശരിയാണെങ്കിലും ഇന്റർനെറ്റ് കിട്ടുന്നില്ല",
          "english": "No Internet Despite Normal Modem Lights"
        },
        "urgency": "medium",
        "category": "configuration",
        "device_types": ["fiber_modem", "wifi_router"],
        "symptoms": {
          "malayalam": ["മോഡത്തിൽ ലൈറ്റ് ശരിയാണ്", "ബ്ലൂ/ഗ്രീൻ ലൈറ്റ് കാണുന്നു", "എന്നാൽ ഇന്റർനെറ്റ് കിട്ടുന്നില്ല"],
          "english": ["modem lights are normal", "blue/green lights showing", "but no internet"]
        },
        "keywords": ["normal lights", "blue light", "green light", "no internet", "ലൈറ്റ് ശരിയാണ്", "ബ്ലൂ ലൈറ്റ്", "ഗ്രീൻ ലൈറ്റ്", "ഇന്റർനെറ്റ് ഇല്ല"],
        "diagnosis": {
          "primary_check": {
            "malayalam": "മോഡത്തിലെ ലൈറ്റുകളുടെ നിറം പരിശോധിക്കുക",
            "english": "Check the color of modem lights"
          },
          "questions": [
            {
              "malayalam": "മോഡത്തിൽ എന്തെങ്കിലും ലൈറ്റുകൾ കാണുന്നുണ്ടോ, അതിൽ ഏതെങ്കിലും ചുവന്ന ലൈറ്റ് ഉണ്ടോ?",
              "english": "Are there any lights on the modem, and is any of them red?"
            },
            {
              "malayalam": "മോഡത്തിൽ എന്തെങ്കിലും ചുവന്ന ലൈറ്റ് ഉണ്ടോ?",
              "english": "Is there any red light on the modem?"
            },
            {
              "malayalam": "മോഡം റീസ്റ്റാർട്ട് ചെയ്തിട്ടുണ്ടോ?",
              "english": "Have you restarted the modem?"
            },
            {
              "malayalam": "ഫോണിലെ WiFi ലിസ്റ്റിൽ നിങ്ങളുടെ സാധാരണ WiFi പേര് കാണുന്നുണ്ടോ അതോ വേറെ പേരാണോ?",
              "english": "In your phone's WiFi list, do you see your usual WiFi name or a different name?"
            }
          ]
        },
        "solution": {
          "troubleshooting_steps": [
            {
              "step": 1,
              "malayalam": "മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക. മോഡം പൂർണ്ണമായും ഓൺലൈൻ ആകാൻ 5 മിനിറ്റ് എടുക്കും. 5 മിനിറ്റിനു ശേഷവും പ്രശ്നം നിലനിൽക്കുന്നുവെങ്കിൽ, ദയവായി ഞങ്ങളെ വീണ്ടും വിളിക്കുക.",
              "english": "Power off and on the modem through the plug switch. The modem takes about 5 minutes to be fully online. If the issue persists after 5 minutes, please call us back.",
              "technical_details": "Power off from the plug switch, wait for 30 seconds, then power on. Modem will take about 5 minutes to be fully online. Ask customer to call back if issue persists after 5 minutes."
            },
            {
              "step": 2,
              "malayalam": "ഫോണിലെ WiFi ലിസ്റ്റിൽ നിങ്ങളുടെ സാധാരണ WiFi പേര് പരിശോധിക്കുക",
              "english": "Check if your usual WiFi name appears in your phone's WiFi list",
              "technical_details": "Determine if modem configuration has been reset"
            }
          ],
          "condition_analysis": {
            "if_red_light": {
              "malayalam": "ചുവന്ന ലൈറ്റ് കാണുന്നെങ്കിൽ, ആദ്യം മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക. മോഡം പൂർണ്ണമായും ഓൺലൈൻ ആകാൻ 5 മിനിറ്റ് എടുക്കും. 5 മിനിറ്റിനു ശേഷവും പ്രശ്നം നിലനിൽക്കുന്നുവെങ്കിൽ, ദയവായി ഞങ്ങളെ വീണ്ടും വിളിക്കുക, അപ്പോൾ ടെക്നീഷ്യനെ അയക്കുന്നതാണ്.",
              "english": "If red light is showing, first power off and on the modem through the plug switch. The modem takes about 5 minutes to be fully online. If the issue persists after 5 minutes, please call us back and we will send a technician.",
              "action": "restart_modem_then_technician_if_needed",
              "visit_details": "If customer calls back after restart, inform them that technician will reach before evening or tomorrow morning. Sky Vision shop works between 10 AM to 5 PM. Do not specify exact time."
            },
            "if_same_name": {
              "malayalam": "സേം WiFi പേര് കാണുന്നെങ്കിൽ ആദ്യം മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക. മോഡം പൂർണ്ണമായും ഓൺലൈൻ ആകാൻ 5 മിനിറ്റ് എടുക്കും. 5 മിനിറ്റിനു ശേഷവും പ്രശ്നം നിലനിൽക്കുന്നുവെങ്കിൽ, ദയവായി ഞങ്ങളെ വീണ്ടും വിളിക്കുക.",
              "english": "If the same WiFi name is showing, first power off and on the modem through the plug switch. The modem takes about 5 minutes to be fully online. If the issue persists after 5 minutes, please call us back.",
              "action": "restart_modem_then_technician_if_needed",
              "visit_details": "If customer calls back after restart, inform them that technician will reach before evening or tomorrow morning. Sky Vision shop works between 10 AM to 5 PM. Do not specify exact time."
            },
            "if_different_name": {
              "malayalam": "വ്യത്യസ്ത WiFi പേര് കാണുന്നെങ്കിൽ ആദ്യം മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക. മോഡം പൂർണ്ണമായും ഓൺലൈൻ ആകാൻ 5 മിനിറ്റ് എടുക്കും. 5 മിനിറ്റിനു ശേഷവും പ്രശ്നം നിലനിൽക്കുന്നുവെങ്കിൽ, ദയവായി ഞങ്ങളെ വീണ്ടും വിളിക്കുക.",
              "english": "If a different WiFi name is showing, first power off and on the modem through the plug switch. The modem takes about 5 minutes to be fully online. If the issue persists after 5 minutes, please call us back.",
              "action": "restart_modem_then_technician_if_needed",
              "visit_details": "If customer calls back after restart, inform them that technician will reach before evening or tomorrow morning. Sky Vision shop works between 10 AM to 5 PM. Do not specify exact time."
            },
            "if_no_connection": {
              "malayalam": "WiFi പേര് കാണുന്നുണ്ടെങ്കിലും കണക്റ്റ് ആകുന്നില്ലെങ്കിൽ ആദ്യം മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക. മോഡം പൂർണ്ണമായും ഓൺലൈൻ ആകാൻ 5 മിനിറ്റ് എടുക്കും. 5 മിനിറ്റിനു ശേഷവും പ്രശ്നം നിലനിൽക്കുന്നുവെങ്കിൽ, ദയവായി ഞങ്ങളെ വീണ്ടും വിളിക്കുക.",
              "english": "If WiFi name is visible but cannot connect, first power off and on the modem through the plug switch. The modem takes about 5 minutes to be fully online. If the issue persists after 5 minutes, please call us back.",
              "action": "restart_modem_then_technician_if_needed",
              "visit_details": "If customer calls back after restart, inform them that technician will reach before evening or tomorrow morning. Sky Vision shop works between 10 AM to 5 PM. Do not specify exact time."
            }
          },
          "escalation": {
            "condition": "മോഡം റീസ്റ്റാർട്ട് ചെയ്ത ശേഷവും പ്രശ്‌നം നിലനിൽക്കുന്നെങ്കിൽ",
            "action": "technician_visit",
            "priority": "medium"
          }
        },
        "success_indicators": ["ഇന്റർനെറ്റ് കണക്ഷൻ പുനഃസ്ഥാപിക്കപ്പെടുന്നു"],
        "resolution_time": "technician_visit_required",
        "customer_feedback_score": 3.9
      }
    ],
    "decision_tree": {
      "root_question": {
        "malayalam": "നെറ്റ് കിട്ടുന്നില്ല എന്നാൽ എന്താണ് പ്രശ്‌നം?",
        "english": "No internet - what exactly is the problem?"
      },
      "branches": [
        {
          "condition": "modem_no_lights",
          "route_to": "NET_001",
          "probability": 0.3
        },
        {
          "condition": "red_light_showing",
          "route_to": "NET_002",
          "probability": 0.25
        },
        {
          "condition": "wifi_name_changed",
          "route_to": "NET_003",
          "probability": 0.2
        },
        {
          "condition": "slow_internet",
          "route_to": "NET_004",
          "probability": 0.15
        },
        {
          "condition": "range_issues",
          "route_to": "NET_005",
          "probability": 0.1
        },
        {
          "condition": "normal_lights_no_internet",
          "route_to": "NET_006",
          "probability": 0.1
        }
      ]
    },
    "common_patterns": {
      "escalation_triggers": [
        "red_light_detected",
        "hardware_failure_confirmed",
        "configuration_reset_detected",
        "basic_troubleshooting_failed"
      ],
      "immediate_resolution": [
        "simple_restart_fixes",
        "connection_issues",
        "user_education"
      ],
      "recurring_issues": [
        "power_adapter_failures",
        "fiber_breaks_in_area",
        "configuration_resets",
        "normal_lights_no_internet"
      ]
    },
    "multilingual_support": {
      "primary_languages": ["malayalam", "english"],
      "fallback_language": "english",
      "translation_confidence": 0.95,
      "cultural_context": "Kerala_telecom_customer_service"
    },
    "performance_metrics": {
      "avg_resolution_time": "20_minutes",
      "first_call_resolution_rate": "75%",
      "customer_satisfaction": 4.1,
      "technician_dispatch_rate": "40%"
    },
    "technician_visit_info": {
      "shop_hours": "10:00 AM - 5:00 PM",
      "standard_response": {
        "malayalam": "ടെക്‌നീഷ്യൻ വൈകുന്നേരത്തിനു മുമ്പോ അല്ലെങ്കിൽ നാളെ രാവിലെയോ എത്തിച്ചേരും",
        "english": "The technician will reach before evening or tomorrow morning"
      },
      "notes": "Do not specify exact time. Always provide realistic timeframes for technician visits. Do not ask for customer's preferred time."
    }
  }
}
