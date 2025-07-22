-- PostgreSQL Database Initialization Script
-- This script runs automatically when the PostgreSQL container starts

-- Create database user if not exists (fallback, usually created by environment variables)
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'sms_agent') THEN
      
      CREATE ROLE sms_agent LOGIN PASSWORD 'secure_password_123';
   END IF;
END
$do$;

-- Create database if not exists (fallback, usually created by environment variables)
SELECT 'CREATE DATABASE sms_agent_db OWNER sms_agent'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'sms_agent_db')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE sms_agent_db TO sms_agent;

-- Connect to the database
\c sms_agent_db;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas for organization
CREATE SCHEMA IF NOT EXISTS app_data;
CREATE SCHEMA IF NOT EXISTS notifications;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Grant schema permissions
GRANT ALL ON SCHEMA app_data TO sms_agent;
GRANT ALL ON SCHEMA notifications TO sms_agent;
GRANT ALL ON SCHEMA analytics TO sms_agent;

-- Set default schema search path
ALTER ROLE sms_agent SET search_path = app_data, notifications, analytics, public;

-- Create custom types
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_tier') THEN
        CREATE TYPE user_tier AS ENUM ('free', 'premium', 'enterprise');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_priority') THEN
        CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'urgent');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notification_status') THEN
        CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'delivered', 'failed', 'bounced');
    END IF;
END $$;

-- Create indexes for better performance
-- (Tables will be created by the application, indexes added here for optimization)

COMMENT ON DATABASE sms_agent_db IS 'Enhanced SMS-to-Cursor AI Agent Database';
COMMENT ON SCHEMA app_data IS 'Main application data including users and tasks';
COMMENT ON SCHEMA notifications IS 'Notification system data and templates';
COMMENT ON SCHEMA analytics IS 'Analytics and metrics data'; 