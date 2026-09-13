-- Run this ONCE while Query Tool is connected to the default `postgres` database.
-- Do not run it while connected to smart_study_assistant itself.

CREATE DATABASE smart_study_assistant
    WITH
    ENCODING = 'UTF8'
    TEMPLATE = template0;
