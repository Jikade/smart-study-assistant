--
-- PostgreSQL database dump
--

\restrict Y3BDQ39YKPhfAlVbddbh2JxoegfyyqboKGcn5D7gDVjigxQdRhBe8mwZvq9Kqxw

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: badges; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.badges (id, code, name, description, icon_url, criteria, xp_reward, is_active, created_at) OVERRIDING SYSTEM VALUE VALUES (1, 'FIRST_QUIZ', 'First Quiz', 'Complete the first quiz', NULL, '{"quiz_completed": 1}', 50, true, '2026-09-07 01:21:59.681424+07');
INSERT INTO public.badges (id, code, name, description, icon_url, criteria, xp_reward, is_active, created_at) OVERRIDING SYSTEM VALUE VALUES (2, 'PERFECT_SCORE', 'Quiz Master', 'Achieve 100% on a quiz', NULL, '{"quiz_score": 100}', 100, true, '2026-09-07 01:21:59.681424+07');
INSERT INTO public.badges (id, code, name, description, icon_url, criteria, xp_reward, is_active, created_at) OVERRIDING SYSTEM VALUE VALUES (3, 'STREAK_7', '7 Day Streak', 'Study for 7 consecutive days', NULL, '{"streak_days": 7}', 150, true, '2026-09-07 01:21:59.681424+07');
INSERT INTO public.badges (id, code, name, description, icon_url, criteria, xp_reward, is_active, created_at) OVERRIDING SYSTEM VALUE VALUES (4, 'FLASHCARD_100', 'Memory Master', 'Review 100 flashcards', NULL, '{"flashcards_reviewed": 100}', 100, true, '2026-09-07 01:21:59.681424+07');


--
-- Name: badges_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.badges_id_seq', 4, true);


--
-- PostgreSQL database dump complete
--

\unrestrict Y3BDQ39YKPhfAlVbddbh2JxoegfyyqboKGcn5D7gDVjigxQdRhBe8mwZvq9Kqxw

