--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13
-- Dumped by pg_dump version 15.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: analytics; Type: SCHEMA; Schema: -; Owner: sms_agent
--

CREATE SCHEMA analytics;


ALTER SCHEMA analytics OWNER TO sms_agent;

--
-- Name: SCHEMA analytics; Type: COMMENT; Schema: -; Owner: sms_agent
--

COMMENT ON SCHEMA analytics IS 'Analytics and metrics data';


--
-- Name: app_data; Type: SCHEMA; Schema: -; Owner: sms_agent
--

CREATE SCHEMA app_data;


ALTER SCHEMA app_data OWNER TO sms_agent;

--
-- Name: SCHEMA app_data; Type: COMMENT; Schema: -; Owner: sms_agent
--

COMMENT ON SCHEMA app_data IS 'Main application data including users and tasks';


--
-- Name: notifications; Type: SCHEMA; Schema: -; Owner: sms_agent
--

CREATE SCHEMA notifications;


ALTER SCHEMA notifications OWNER TO sms_agent;

--
-- Name: SCHEMA notifications; Type: COMMENT; Schema: -; Owner: sms_agent
--

COMMENT ON SCHEMA notifications IS 'Notification system data and templates';


--
-- Name: pg_stat_statements; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_stat_statements WITH SCHEMA public;


--
-- Name: EXTENSION pg_stat_statements; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_stat_statements IS 'track planning and execution statistics of all SQL statements executed';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: notification_status; Type: TYPE; Schema: public; Owner: sms_agent
--

CREATE TYPE public.notification_status AS ENUM (
    'pending',
    'sent',
    'delivered',
    'failed',
    'bounced'
);


ALTER TYPE public.notification_status OWNER TO sms_agent;

--
-- Name: task_priority; Type: TYPE; Schema: public; Owner: sms_agent
--

CREATE TYPE public.task_priority AS ENUM (
    'low',
    'medium',
    'high',
    'urgent'
);


ALTER TYPE public.task_priority OWNER TO sms_agent;

--
-- Name: user_tier; Type: TYPE; Schema: public; Owner: sms_agent
--

CREATE TYPE public.user_tier AS ENUM (
    'free',
    'premium',
    'enterprise'
);


ALTER TYPE public.user_tier OWNER TO sms_agent;

--
-- PostgreSQL database dump complete
--

