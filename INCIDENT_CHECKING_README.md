# Incident Checking Functionality

## Overview

The bot now includes intelligent incident checking functionality that allows it to check for existing incidents in the database before escalating customer issues. This helps reduce unnecessary escalations and provides customers with relevant information about ongoing issues in their area.

## How It Works

### 1. Early Incident Detection

When a customer reports an issue, the bot immediately checks the incidents table for any relevant active incidents that might be related to their problem. This happens in parallel with other processing to minimize latency.

### 2. Relevance Scoring

The system uses a sophisticated scoring algorithm to determine how relevant an incident is to the customer's query:

- **Area Match (10 points)**: Highest priority - if the customer's area matches the incident area
- **Issue Type Match (8 points)**: If the incident type matches the reported issue
- **Keyword Match (3 points)**: If relevant keywords are found in the incident description
- **Word Match (2 points)**: If individual words from the customer's query match the incident

### 3. Customer-Friendly Information

When relevant incidents are found, the bot provides customers with:

- Information about the incident in their area
- Estimated resolution time (if available)
- Assurance that technicians are working on the issue
- Clear communication that they don't need to escalate

## Database Schema

The incidents table structure:

```sql
CREATE TABLE public.incidents (
  id uuid not null default gen_random_uuid(),
  area text not null,
  issue_type text not null,
  description text null,
  status text not null default 'active',
  priority text not null default 'medium',
  reported_by uuid null,
  assigned_to uuid null,
  reported_at timestamp with time zone null default now(),
  resolved_at timestamp with time zone null,
  affected_users integer null default 0,
  estimated_resolution timestamp with time zone null,
  resolution_notes text null,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now()
);
```

## Implementation Details

### Key Methods

#### `check_relevant_incidents(user_query, customer_area, issue_type)`

Checks for incidents relevant to the customer's query and area.

**Parameters:**
- `user_query`: The customer's reported issue
- `customer_area`: The customer's area/region
- `issue_type`: The type of issue being reported

**Returns:** List of relevant incidents with relevance scores

#### `get_incident_summary_for_customer(incidents)`

Generates customer-friendly summaries of incidents in Malayalam.

**Parameters:**
- `incidents`: List of relevant incidents

**Returns:** Malayalam text summary for the customer

### Integration Points

#### 1. Early Conversation Check

In `on_transcription()`, the bot checks for incidents early in the conversation:

```python
# Check for relevant incidents early in the conversation
incident_task = asyncio.create_task(self._check_for_incidents(text))

# If incidents found, inform customer and return early
if relevant_incidents:
    incident_message = generate_incident_message(incident_summary)
    await self.play_message(incident_message)
    return  # Don't proceed with normal troubleshooting
```

#### 2. Pre-Escalation Check

In `_check_for_escalation()`, before escalating, the bot checks for incidents:

```python
if should_escalate:
    # Check for relevant incidents before escalating
    relevant_incidents = self.supabase_manager.check_relevant_incidents(...)
    
    if relevant_incidents:
        # Inform customer about incident instead of escalating
        await self.play_message(incident_message)
        return  # Don't escalate
```

## Keyword Matching

The system recognizes these issue categories with multilingual support:

- **WiFi Issues**: `wifi`, `wireless`, `വൈഫൈ`, `വൈ ഫൈ`
- **Internet Issues**: `internet`, `നെറ്റ്`, `ഇന്റർനെറ്റ്`, `connection`, `കണക്ഷൻ`
- **Speed Issues**: `speed`, `slow`, `വേഗത`, `സ്ലോ`, `bandwidth`, `ബാൻഡ്‌വിഡ്ത്ത്`
- **Power Issues**: `power`, `പവർ`, `light`, `ലൈറ്റ്`, `adapter`, `അഡാപ്റ്റർ`
- **Fiber Issues**: `fiber`, `ഫൈബർ`, `cable`, `കേബിൾ`, `optical`
- **Outage Issues**: `outage`, `ഔട്ടേജ്`, `down`, `ഡൗൺ`, `not working`, `ഇല്ല`
- **Payment Issues**: `payment`, `പേയ്മെന്റ്`, `bill`, `ബിൽ`, `recharge`, `റീചാർജ്`

## Example Scenarios

### Scenario 1: WiFi Issue with Existing Incident

**Customer says:** "എന്റെ വൈഫൈ കണക്ഷൻ വരുന്നില്ല"

**Database has:** Active incident in customer's area: "WiFi connectivity issue in Kochi area"

**Bot response:** 
```
നിങ്ങളുടെ പ്രശ്നത്തെക്കുറിച്ച് ഞാൻ പരിശോധിച്ചു. 
Kochi പ്രദേശത്ത് ഒരു വൈഫൈ പ്രശ്നം റിപ്പോർട്ട് ചെയ്തിട്ടുണ്ട്. 
ഞങ്ങളുടെ ടെക്നീഷ്യൻ ടീം ഇത് പരിഹരിക്കാൻ ശ്രമിക്കുന്നുണ്ട്. 
ദയവായി കുറച്ച് സമയം കാത്തിരിക്കൂ. 
ഇത് പരിഹരിക്കപ്പെടുമ്പോൾ നിങ്ങൾക്ക് സ്വയമേവ അറിയിക്കാം.
```

### Scenario 2: No Relevant Incidents

**Customer says:** "എന്റെ ഇന്റർനെറ്റ് വരുന്നില്ല"

**Database has:** No relevant incidents in customer's area

**Bot response:** Proceeds with normal troubleshooting flow

## Benefits

1. **Reduced Escalations**: Customers get immediate information about known issues
2. **Better Customer Experience**: Clear communication about ongoing problems
3. **Efficient Resource Usage**: Technicians aren't overwhelmed with duplicate reports
4. **Proactive Communication**: Customers feel informed and valued
5. **Multilingual Support**: Works with both English and Malayalam queries

## Testing

Run the test script to verify functionality:

```bash
python test_incident_checking.py
```

This will test:
- Incident creation and resolution
- Relevance scoring for different issue types
- Customer summary generation
- Area-based matching
- Multilingual keyword recognition

## Configuration

### Environment Variables

Ensure your Supabase configuration is properly set:

```bash
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### Database Permissions

The service role key needs these permissions:
- `SELECT` on `incidents` table
- `INSERT` on `incidents` table (for creating incidents)
- `UPDATE` on `incidents` table (for resolving incidents)

## Monitoring

The system logs incident checking activities:

- Incident matches found
- Relevance scores
- Customer area matching
- Summary generation
- Error handling

Check logs for entries like:
```
Found 2 relevant incidents for query: 'എന്റെ വൈഫൈ കണക്ഷൻ വരുന്നില്ല'
Relevant incident: wifi_issue in Kochi (score: 13)
```

## Future Enhancements

1. **Real-time Updates**: Notify customers when incidents are resolved
2. **Predictive Incident Detection**: Identify potential issues before they become widespread
3. **Customer Notification System**: SMS/email notifications about incident status
4. **Incident Analytics**: Track incident patterns and resolution times
5. **Automated Incident Creation**: Create incidents based on multiple similar reports 

def ml_to_en_tech_terms(text: str) -> str:
    mapping = {
        "ഫൈബർ": "fiber",
        "കേബിൾ": "cable",
        "പവർ": "power",
        "ലൈറ്റ്": "light",
        "ചുവപ്പ്": "red",
        "വൈഫൈ": "wifi",
        "ഇന്റർനെറ്റ്": "internet",
        "കണക്ഷൻ": "connection",
        "വേഗത": "speed",
        "സ്ലോ": "slow",
        "ഡൗൺ": "down",
        "പ്രശ്നം": "issue",
        "കട്ട്": "cut",
        "ഔട്ടേജ്": "outage",
    }
    for ml, en in mapping.items():
        text = text.replace(ml, en)
    return text 

# Before calling check_relevant_incidents
query_for_incident = ml_to_en_tech_terms(user_text)
relevant_incidents = self.supabase_manager.check_relevant_incidents(
    user_query=query_for_incident,
    customer_area=customer_area,
    issue_type=issue_type
) 

critical_types = {"fiber cut", "power outage", "equipment failure"}
for incident in relevant_incidents:
    if incident.get("issue_type", "").lower() in critical_types:
        await self.play_message(
            f"നിങ്ങളുടെ പ്രദേശത്ത് ഒരു പ്രധാന പ്രശ്നം ({incident.get('issue_type')}) റിപ്പോർട്ട് ചെയ്തിട്ടുണ്ട്. "
            "ഞങ്ങളുടെ ടെക്നീഷ്യൻ ഉടൻ എത്തും. ദയവായി കാത്തിരിക്കുക."
        )
        # Optionally, update call memory and return here
        return 