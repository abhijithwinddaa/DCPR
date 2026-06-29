-- Migration: 001_initialize_platform_schema.sql
-- Description: Sets up PostgreSQL relational tables for the DCPR platform.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'PLANNER' CHECK (role IN ('ADMIN', 'ARCHITECT', 'PLANNER', 'REGULATOR')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Uploaded Files Storage Metadata
CREATE TABLE IF NOT EXISTS uploaded_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    storage_bucket VARCHAR(100) NOT NULL,
    storage_path VARCHAR(512) UNIQUE NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    mime_type VARCHAR(100),
    sha256_checksum VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Documents Table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN ('DCPR', 'CIRCULAR', 'AMENDMENT', 'NOTIFICATION', 'ORDER')),
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    file_id UUID REFERENCES uploaded_files(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Document Versions (Lineage and Processing Status)
CREATE TABLE IF NOT EXISTS document_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    version_tag VARCHAR(50) NOT NULL,
    effective_start_date DATE NOT NULL,
    effective_end_date DATE,
    processing_status VARCHAR(50) DEFAULT 'PENDING' CHECK (processing_status IN ('PENDING', 'PROCESSING', 'FAILED', 'COMPLETED')),
    error_log TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Canonical Knowledge Entities (Modeled facts and regulations)
CREATE TABLE IF NOT EXISTS knowledge_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version_id UUID REFERENCES document_versions(id) ON DELETE CASCADE,
    entity_uri VARCHAR(255) UNIQUE NOT NULL, -- e.g., 'dcpr:scheme:33-9'
    entity_label VARCHAR(50) NOT NULL CHECK (entity_label IN ('SCHEME', 'REGULATION', 'FACT', 'FORMULA', 'TABLE', 'DEFINITION')),
    normalized_citation VARCHAR(255) NOT NULL, -- e.g., 'regulation:33:subregulation:9'
    entity_data JSONB NOT NULL, -- AST expressions, table cells, or metadata details
    effective_period_start DATE NOT NULL,
    effective_period_end DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Platform Calculations (Zoning calculations history)
CREATE TABLE IF NOT EXISTS calculations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    scheme_uri VARCHAR(255) NOT NULL,
    input_parameters JSONB NOT NULL, -- e.g. plot area, road width, zone
    output_results JSONB NOT NULL, -- e.g. applicable FSI, BUA, eligibility
    validator_status VARCHAR(50) NOT NULL CHECK (validator_status IN ('PASS', 'FAIL')),
    validation_warnings JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Audit Logs Ledger (Detailed rechecks and boundary violations)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    calculation_id UUID REFERENCES calculations(id) ON DELETE CASCADE,
    trace_step INT NOT NULL,
    rule_id VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    result_value TEXT,
    status VARCHAR(50) NOT NULL,
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Natural Language Questions History
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    calculation_id UUID REFERENCES calculations(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    question_text TEXT NOT NULL,
    explanation_text TEXT NOT NULL,
    model_name VARCHAR(100) NOT NULL, -- e.g., 'qwen3:8b'
    was_fallback BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. Regulatory Amendment Lineage
CREATE TABLE IF NOT EXISTS amendments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    amendment_version_id UUID REFERENCES document_versions(id) ON DELETE CASCADE,
    target_entity_uri VARCHAR(255) NOT NULL, -- references entity_uri (not enforced with FK to allow references before sync)
    action_type VARCHAR(50) NOT NULL CHECK (action_type IN ('ADDED', 'REMOVED', 'MODIFIED')),
    diff_data JSONB, -- JSON representation of variables, bounds, or formulas changed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indices for scaling and query optimization
CREATE INDEX IF NOT EXISTS idx_knowledge_entities_uri ON knowledge_entities(entity_uri);
CREATE INDEX IF NOT EXISTS idx_knowledge_entities_label ON knowledge_entities(entity_label);
CREATE INDEX IF NOT EXISTS idx_calculations_user ON calculations(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_calc ON audit_logs(calculation_id);
CREATE INDEX IF NOT EXISTS idx_amendments_target ON amendments(target_entity_uri);
CREATE INDEX IF NOT EXISTS idx_document_versions_dates ON document_versions(effective_start_date, effective_end_date);
