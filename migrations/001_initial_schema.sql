
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    tier VARCHAR(20) NOT NULL DEFAULT 'free',
    credits_remaining INTEGER NOT NULL DEFAULT 100,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    tier VARCHAR(20) NOT NULL,
    sandbox_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Spec files table
CREATE TABLE spec_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    file_type VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    UNIQUE(project_id, file_type, version)
);

-- Spec versions table (for history)
CREATE TABLE spec_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    spec_file_id UUID REFERENCES spec_files(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    changes_summary TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    agent_type VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    input_context JSONB,
    output JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Code changes table
CREATE TABLE code_changes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    change_type VARCHAR(20) NOT NULL,
    diff TEXT NOT NULL,
    agent_type VARCHAR(20) NOT NULL,
    reasoning TEXT,
    approved BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sandboxes table
CREATE TABLE sandboxes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    e2b_sandbox_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    preview_url VARCHAR(500),
    qr_code TEXT,
    cache_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW()
);

-- Memory items table (with pgvector for embeddings)
CREATE TABLE memory_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    item_type VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for vector similarity search
CREATE INDEX ON memory_items USING ivfflat (embedding vector_cosine_ops);
WITH (lists = 100);

-- Marketplace components table (disabled for now)
CREATE TABLE marketplace_components (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    tags TEXT[],
    preview_url VARCHAR(500),
    spec_template JSONB NOT NULL,
    code_template JSONB NOT NULL,
    dependencies TEXT[],
    downloads INTEGER DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Build jobs table
CREATE TABLE build_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    platform VARCHAR(20) NOT NULL,
    status VARCHAR(50) NOT NULL,
    build_url VARCHAR(500),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Chat messages table
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    attachments JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- PROJECT MEMORY
CREATE TABLE project_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_spec_files_project_id ON spec_files(project_id);
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_code_changes_task_id ON code_changes(task_id);
CREATE INDEX idx_sandboxes_project_id ON sandboxes(project_id);
CREATE INDEX idx_memory_items_project_id ON memory_items(project_id);
CREATE INDEX idx_chat_messages_project_id ON chat_messages(project_id);
CREATE INDEX idx_project_memory_project_id ON project_memory(project_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_spec_files_updated_at BEFORE UPDATE ON spec_files
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_code_changes_updated_at BEFORE UPDATE ON code_changes
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sandboxes_updated_at BEFORE UPDATE ON sandboxes
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();    


-- Row Level Security (RLS) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE spec_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_changes ENABLE ROW LEVEL SECURITY;
ALTER TABLE sandboxes ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_memory ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY users_select_own ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY users_update_own ON users FOR UPDATE USING (auth.uid() = id);

-- Projects policies
CREATE POLICY projects_select_own ON projects FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY projects_insert_own ON projects FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY projects_update_own ON projects FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY projects_delete_own ON projects FOR DELETE USING (auth.uid() = user_id);

-- Spec files policies (through projects)
CREATE POLICY spec_files_select_own ON spec_files FOR SELECT 
    USING (EXISTS (SELECT 1 FROM projects WHERE projects.id = spec_files.project_id AND projects.user_id = auth.uid()));
CREATE POLICY spec_files_insert_own ON spec_files FOR INSERT 
    WITH CHECK (EXISTS (SELECT 1 FROM projects WHERE projects.id = spec_files.project_id AND projects.user_id = auth.uid()));
CREATE POLICY spec_files_update_own ON spec_files FOR UPDATE 
    USING (EXISTS (SELECT 1 FROM projects WHERE projects.id = spec_files.project_id AND projects.user_id = auth.uid()));

-- Similar policies for other tables...
-- (Add more RLS policies as needed for production)
-- TASKS RLS
CREATE POLICY tasks_select_own ON tasks FOR SELECT 
USING (EXISTS (SELECT 1 FROM projects WHERE projects.id = tasks.project_id AND projects.user_id = auth.uid()));
CREATE POLICY tasks_insert_own ON tasks FOR INSERT 
WITH CHECK (EXISTS (SELECT 1 FROM projects WHERE projects.id = tasks.project_id AND projects.user_id = auth.uid()));
CREATE POLICY tasks_update_own ON tasks FOR UPDATE 
USING (EXISTS (SELECT 1 FROM projects WHERE projects.id = tasks.project_id AND projects.user_id = auth.uid()));
CREATE POLICY tasks_delete_own ON tasks FOR DELETE 
USING (EXISTS (SELECT 1 FROM projects WHERE projects.id = tasks.project_id AND projects.user_id = auth.uid()));

-- CODE CHANGES RLS
CREATE POLICY code_changes_select_own ON code_changes FOR SELECT
USING (EXISTS (SELECT 1 FROM tasks JOIN projects p ON tasks.project_id = p.id WHERE tasks.id = code_changes.task_id AND p.user_id = auth.uid()));
CREATE POLICY code_changes_insert_own ON code_changes FOR INSERT
WITH CHECK (EXISTS (SELECT 1 FROM tasks JOIN projects p ON tasks.project_id = p.id WHERE tasks.id = code_changes.task_id AND p.user_id = auth.uid()));

-- SANDBOXES RLS
CREATE POLICY sandboxes_select_own ON sandboxes FOR SELECT
USING (EXISTS (SELECT 1 FROM projects WHERE projects.id = sandboxes.project_id AND projects.user_id = auth.uid()));

-- MEMORY ITEMS RLS
CREATE POLICY memory_items_select_own ON memory_items FOR SELECT
USING (EXISTS (SELECT 1 FROM projects WHERE projects.id = USING (EXISTS (SELECT 1 FROM projects WHERE projects.id = memory_items.project_id AND projects.user_id = auth.uid()));
CREATE POLICY memory_items_insert_own ON memory_items FOR INSERT
WITH CHECK (EXISTS (SELECT 1 FROM projects WHERE projects.id = memory_items.project_id AND projects.user_id = auth.uid()));

-- CHAT MESSAGES RLS
CREATE POLICY chat_messages_select_own ON chat_messages FOR SELECT
USING (EXISTS (SELECT 1 FROM projects WHERE projects.id = chat_messages.project_id AND projects.user_id = auth.uid()));
CREATE POLICY chat_messages_insert_own ON chat_messages FOR INSERT
WITH CHECK (EXISTS (SELECT 1 FROM projects WHERE projects.id = chat_messages.project_id AND projects.user_id = auth.uid()));

-- PROJECT MEMORY RLS
CREATE POLICY project_memory_select_own ON project_memory FOR SELECT
USING (EXISTS (SELECT 1 FROM projects WHERE projects.id = project_memory.project_id AND projects.user_id = auth.uid()));
CREATE POLICY project_memory_insert_own ON project_memory FOR INSERT
WITH CHECK (EXISTS (SELECT 1 FROM projects WHERE projects.id = project_memory.project_id AND projects.user_id = auth.uid()));gcd 
