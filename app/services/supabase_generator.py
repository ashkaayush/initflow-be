"""
Supabase backend generator service for full-stack apps
"""
from typing import Dict, List, Any
import re


class SupabaseBackendGenerator:
    """Service for generating Supabase backend configurations and code"""
    
    def __init__(self):
        pass
    
    def generate_backend_specs(self, analysis: Dict[str, Any], project_name: str) -> Dict[str, str]:
        """Generate backend specifications including database schema and API endpoints"""
        
        if not analysis.get("needs_backend", False):
            return {}
        
        # Generate database schema
        database_schema = self._generate_database_schema(analysis, project_name)
        
        # Generate API endpoints
        api_endpoints = self._generate_api_endpoints(analysis, project_name)
        
        # Generate authentication setup
        auth_setup = self._generate_auth_setup(analysis, project_name)
        
        # Generate real-time subscriptions
        realtime_setup = self._generate_realtime_setup(analysis, project_name)
        
        # Generate real-time subscriptions
        realtime_setup = self._generate_realtime_setup(analysis, project_name)
        
        return {
            "database_schema": database_schema,
            "api_endpoints": api_endpoints,
            "auth_setup": auth_setup,
            "realtime_setup": realtime_setup
        }
    
    def _generate_database_schema(self, analysis: Dict, project_name: str) -> str:
        """Generate Supabase database schema SQL"""
        entities = analysis.get("entities", [])
        features = analysis.get("features", [])
        
        schema_sql = f"""-- {project_name} Database Schema
-- Generated for Supabase

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

"""
        
        # Generate tables based on entities
        for entity in entities:
            table_name = entity.lower() + "s"
            schema_sql += f"""-- {entity} table
CREATE TABLE {table_name} (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Add entity-specific fields based on type
"""
            
            # Add fields based on entity type
            if entity.lower() in ["user", "profile"]:
                schema_sql += """    email VARCHAR(255) UNIQUE,
    name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    bio TEXT,
"""
            elif entity.lower() in ["post", "article", "content"]:
                schema_sql += """    title VARCHAR(255) NOT NULL,
    content TEXT,
    author_id UUID REFERENCES users(id) ON DELETE CASCADE,
    published BOOLEAN DEFAULT FALSE,
"""
            elif entity.lower() in ["product", "item"]:
                schema_sql += """    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2),
    image_url TEXT,
    category VARCHAR(100),
"""
            elif entity.lower() in ["task", "todo"]:
                schema_sql += """    title VARCHAR(255) NOT NULL,
    description TEXT,
    completed BOOLEAN DEFAULT FALSE,
    due_date TIMESTAMP WITH TIME ZONE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
"""
            else:
                schema_sql += f"""    name VARCHAR(255) NOT NULL,
    description TEXT,
"""
            
            schema_sql += """);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_{table_name}_updated_at 
    BEFORE UPDATE ON {table_name}
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

"""
        
        # Add authentication-related tables if needed
        if "authentication" in features:
            schema_sql += """-- User profiles table (extends Supabase auth.users)
CREATE TABLE profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email VARCHAR(255),
    name VARCHAR(255),
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on profiles
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Profiles are viewable by users who created them
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

-- Profiles are created when a user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, name)
    VALUES (NEW.id, NEW.email, NEW.raw_user_meta_data->>'name');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

"""
        
        # Add RLS policies for other tables
        for entity in entities:
            table_name = entity.lower() + "s"
            schema_sql += f"""-- Enable RLS on {table_name}
ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;

-- Users can view all {table_name}
CREATE POLICY "Users can view {table_name}" ON {table_name}
    FOR SELECT USING (true);

-- Users can insert their own {table_name}
CREATE POLICY "Users can insert {table_name}" ON {table_name}
    FOR INSERT WITH CHECK (true);

-- Users can update their own {table_name}
CREATE POLICY "Users can update own {table_name}" ON {table_name}
    FOR UPDATE USING (true);

"""
        
        return schema_sql
    
    def _generate_api_endpoints(self, analysis: Dict, project_name: str) -> str:
        """Generate API endpoint documentation and client code"""
        entities = analysis.get("entities", [])
        
        api_doc = f"""# {project_name} API Endpoints

## Supabase Client Setup

```javascript
import {{ createClient }} from '@supabase/supabase-js'

const supabaseUrl = 'YOUR_SUPABASE_URL'
const supabaseKey = 'YOUR_SUPABASE_ANON_KEY'

export const supabase = createClient(supabaseUrl, supabaseKey)
```

## Authentication

```javascript
// Sign up
const {{ data, error }} = await supabase.auth.signUp({{
  email: 'user@example.com',
  password: 'password123',
  options: {{
    data: {{
      name: 'John Doe'
    }}
  }}
}})

// Sign in
const {{ data, error }} = await supabase.auth.signInWithPassword({{
  email: 'user@example.com',
  password: 'password123'
}})

// Sign out
const {{ error }} = await supabase.auth.signOut()

// Get current user
const {{ data: {{ user }} }} = await supabase.auth.getUser()
```

## Data Operations

"""
        
        # Generate CRUD operations for each entity
        for entity in entities:
            table_name = entity.lower() + "s"
            entity_name = entity.lower()
            
            api_doc += f"""### {entity} Operations

```javascript
// Get all {table_name}
const {{ data: {table_name}, error }} = await supabase
  .from('{table_name}')
  .select('*')

// Get single {entity_name}
const {{ data: {entity_name}, error }} = await supabase
  .from('{table_name}')
  .select('*')
  .eq('id', {entity_name}Id)
  .single()

// Create {entity_name}
const {{ data, error }} = await supabase
  .from('{table_name}')
  .insert([
    {{ 
      name: 'Example {entity}',
      description: 'Example description'
    }}
  ])
  .select()

// Update {entity_name}
const {{ data, error }} = await supabase
  .from('{table_name}')
  .update({{ name: 'Updated {entity}' }})
  .eq('id', {entity_name}Id)
  .select()

// Delete {entity_name}
const {{ data, error }} = await supabase
  .from('{table_name}')
  .delete()
  .eq('id', {entity_name}Id)
```

"""
        
        return api_doc
    
    def _generate_auth_setup(self, analysis: Dict, project_name: str) -> str:
        """Generate authentication setup guide"""
        if "authentication" not in analysis.get("features", []):
            return ""
        
        return f"""# {project_name} Authentication Setup

## Supabase Auth Configuration

### 1. Enable Authentication Providers

In your Supabase dashboard:
- Go to Authentication > Providers
- Enable Email provider
- Optionally enable social providers (Google, GitHub, etc.)

### 2. Configure Email Templates

Customize email templates in Authentication > Email Templates:
- Confirmation email
- Password reset email
- Magic link email

### 3. React Native Auth Implementation

```javascript
// hooks/useAuth.js
import {{ useState, useEffect, createContext, useContext }} from 'react'
import {{ supabase }} from '../lib/supabase'

const AuthContext = createContext({{}})

export const useAuth = () => {{
  const context = useContext(AuthContext)
  if (!context) {{
    throw new Error('useAuth must be used within AuthProvider')
  }}
  return context
}}

export const AuthProvider = ({{ children }}) => {{
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {{
    // Get initial session
    supabase.auth.getSession().then(({{ data: {{ session }} }}) => {{
      setUser(session?.user ?? null)
      setLoading(false)
    }})

    // Listen for auth changes
    const {{ data: {{ subscription }} }} = supabase.auth.onAuthStateChange(
      async (event, session) => {{
        setUser(session?.user ?? null)
        setLoading(false)
      }}
    )

    return () => subscription.unsubscribe()
  }}, [])

  const signUp = async (email, password, userData = {{}}) => {{
    const {{ data, error }} = await supabase.auth.signUp({{
      email,
      password,
      options: {{ data: userData }}
    }})
    return {{ data, error }}
  }}

  const signIn = async (email, password) => {{
    const {{ data, error }} = await supabase.auth.signInWithPassword({{
      email,
      password
    }})
    return {{ data, error }}
  }}

  const signOut = async () => {{
    const {{ error }} = await supabase.auth.signOut()
    return {{ error }}
  }}

  const value = {{
    user,
    loading,
    signUp,
    signIn,
    signOut
  }}

  return (
    <AuthContext.Provider value={{value}}>
      {{children}}
    </AuthContext.Provider>
  )
}}
```

### 4. Protected Routes

```javascript
// components/ProtectedRoute.js
import {{ useAuth }} from '../hooks/useAuth'
import {{ Navigate }} from 'react-router-native'

export const ProtectedRoute = ({{ children }}) => {{
  const {{ user, loading }} = useAuth()

  if (loading) {{
    return <LoadingScreen />
  }}

  if (!user) {{
    return <Navigate to="/login" replace />
  }}

  return children
}}
```
"""
    
    def _generate_realtime_setup(self, analysis: Dict, project_name: str) -> str:
        """Generate real-time subscriptions setup"""
        if "realtime" not in analysis.get("features", []):
            return ""
        
        entities = analysis.get("entities", [])
        
        realtime_doc = f"""# {project_name} Real-time Setup

## Enable Real-time in Supabase

1. Go to Database > Replication
2. Enable replication for tables you want to subscribe to
3. Set up Row Level Security policies

## Real-time Subscriptions

```javascript
// hooks/useRealtime.js
import {{ useEffect, useState }} from 'react'
import {{ supabase }} from '../lib/supabase'

"""
        
        for entity in entities:
            table_name = entity.lower() + "s"
            
            realtime_doc += f"""
export const use{entity}Subscription = () => {{
  const [data, setData] = useState([])

  useEffect(() => {{
    // Get initial data
    const fetchData = async () => {{
      const {{ data: initialData }} = await supabase
        .from('{table_name}')
        .select('*')
      setData(initialData || [])
    }}
    
    fetchData()

    // Subscribe to changes
    const subscription = supabase
      .channel('{table_name}_changes')
      .on('postgres_changes', 
        {{ 
          event: '*', 
          schema: 'public', 
          table: '{table_name}' 
        }}, 
        (payload) => {{
          console.log('Change received!', payload)
          
          if (payload.eventType === 'INSERT') {{
            setData(prev => [...prev, payload.new])
          }} else if (payload.eventType === 'UPDATE') {{
            setData(prev => prev.map(item => 
              item.id === payload.new.id ? payload.new : item
            ))
          }} else if (payload.eventType === 'DELETE') {{
            setData(prev => prev.filter(item => item.id !== payload.old.id))
          }}
        }}
      )
      .subscribe()

    return () => {{
      subscription.unsubscribe()
    }}
  }}, [])

  return data
}}
"""
        
        realtime_doc += """
```

## Usage in Components

```javascript
import { use{Entity}Subscription } from '../hooks/useRealtime'

export const {Entity}List = () => {
  const {entities} = use{Entity}Subscription()

  return (
    <View>
      {entities.map(item => (
        <Text key={item.id}>{item.name}</Text>
      ))}
    </View>
  )
}
```
"""
        
        return realtime_doc
    



# Singleton instance
supabase_generator = SupabaseBackendGenerator()