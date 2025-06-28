# Supabase Migration Guide

This document outlines the migration from Redis to Supabase for the ABC Customer Care Voicebot System.

## Overview

The system has been migrated from Redis to Supabase to provide:
- Better data persistence
- Built-in authentication
- Real-time subscriptions
- Better scalability
- SQL query capabilities

## Configuration Changes

### Environment Variables

Replace Redis configuration with Supabase configuration in your `.env` file:

```bash
# Old Redis Configuration (remove these)
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_DB=0

# New Supabase Configuration (add these)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### Database Schema

Create the following tables in your Supabase database:

```sql
-- Call sessions table
CREATE TABLE call_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    customer_phone TEXT,
    customer_info JSONB,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    duration INTEGER,
    status TEXT DEFAULT 'active',
    resolution TEXT,
    transcript JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Incidents table
CREATE TABLE incidents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    incident_id TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,
    location TEXT,
    status TEXT DEFAULT 'active',
    affected_zones TEXT,
    affected_regions TEXT,
    affected_areas TEXT,
    affected_services TEXT,
    message_ml TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Call logs table
CREATE TABLE call_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    event_type TEXT NOT NULL,
    event_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Code Changes

### Main Application (`main.py`)

- Replaced Redis client with Supabase manager
- Updated initialization and shutdown logic
- Modified health check functions

### Utilities (`utils.py`)

- Removed Redis-specific functions
- Updated incident creation to use Supabase
- Modified data formatting functions

### New Files

- `supabase_client.py` - Supabase client wrapper with all database operations

## Installation

1. Install the new dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your Supabase project:
   - Create a new project at https://supabase.com
   - Get your project URL and API keys
   - Create the database tables using the SQL above

3. Update your environment variables

4. Test the connection:
```bash
python -c "from supabase_client import check_supabase; print(check_supabase())"
```

## Migration Steps

1. **Backup existing data** from Redis
2. **Create Supabase tables** using the provided SQL
3. **Update configuration** with Supabase credentials
4. **Test the new system** with a few calls
5. **Migrate existing data** (if needed)
6. **Deploy the updated system**

## Benefits

- **Data Persistence**: Data is stored in PostgreSQL and backed up automatically
- **Real-time Features**: Built-in real-time subscriptions for live updates
- **Better Querying**: SQL queries for complex data analysis
- **Scalability**: Automatic scaling with Supabase
- **Security**: Row-level security and built-in authentication

## Troubleshooting

### Connection Issues
- Verify your Supabase URL and API keys
- Check if your IP is whitelisted in Supabase
- Ensure the database tables exist

### Data Migration
- Use the provided migration scripts to move data from Redis
- Verify data integrity after migration
- Keep Redis running during transition period

## Support

For issues with the migration, check:
1. Supabase documentation: https://supabase.com/docs
2. System logs for error messages
3. Database connection status 