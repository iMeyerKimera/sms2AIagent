-- SMS AI Agent Database Initialization
-- This script is executed when the PostgreSQL container starts for the first time

-- Ensure UTF8 encoding and proper locale
SET client_encoding = 'UTF8';

-- Create additional indexes for performance (Django will create the main tables)
-- These are supplementary indexes for common query patterns

-- Log startup message
SELECT 'SMS AI Agent PostgreSQL database initialized successfully' as message;

-- Show database configuration
SELECT 
    version() as postgresql_version,
    current_database() as database_name,
    current_user as database_user,
    inet_server_addr() as server_address,
    inet_server_port() as server_port; 