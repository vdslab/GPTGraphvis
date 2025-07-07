-- Create the database if it doesn't exist
CREATE DATABASE networkdb;

-- Connect to the database
\c networkdb

-- Create the users table (this will be handled by SQLAlchemy, but we'll include it for completeness)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
