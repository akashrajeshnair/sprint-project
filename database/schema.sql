--
-- PostgreSQL database dump
--

\restrict KjkBUYwhr7V472cXx7GsrnFq2RhhJH6CmmJxkNMbAqsKU1d5QslHOHcw3Socj8h

-- Dumped from database version 16.13
-- Dumped by pg_dump version 16.13

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

ALTER TABLE ONLY public.users DROP CONSTRAINT users_username_key;
ALTER TABLE ONLY public.users DROP CONSTRAINT users_pkey;
ALTER TABLE ONLY public.users DROP CONSTRAINT users_email_key;
ALTER TABLE ONLY public.models DROP CONSTRAINT models_pkey;
ALTER TABLE public.users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.models ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE public.users_id_seq;
DROP TABLE public.users;
DROP SEQUENCE public.models_id_seq;
DROP TABLE public.models;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: models; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.models (
    id integer NOT NULL,
    model_name character varying(255) NOT NULL,
    total_tokens integer,
    tokens_used integer
);


--
-- Name: models_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.models_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: models_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.models_id_seq OWNED BY public.models.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(255) NOT NULL,
    password character varying(255) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: models id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.models ALTER COLUMN id SET DEFAULT nextval('public.models_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: models; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.models (id, model_name, total_tokens, tokens_used) FROM stdin;
1	gpt-oss	3000	500
2	gemma-3b	10000	250
3	mistral-7b	7500	30
4	sarvam-9b	100000	20000
5	gpt-5	10000	2000
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, username, email, password, created_at, updated_at) FROM stdin;
1	alice	alice@email.com	password1	2026-04-07 11:15:46.701785	2026-04-07 11:15:46.701785
2	bob	bob@email.com	password2	2026-04-07 11:15:46.701785	2026-04-07 11:15:46.701785
3	charlie	charlie@email.com	password3	2026-04-07 11:15:46.701785	2026-04-07 11:15:46.701785
4	diana	diana@email.com	password4	2026-04-07 11:15:46.701785	2026-04-07 11:15:46.701785
5	eve	eve@email.com	password5	2026-04-07 11:15:46.701785	2026-04-07 11:15:46.701785
\.


--
-- Name: models_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.models_id_seq', 5, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 5, true);


--
-- Name: models models_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.models
    ADD CONSTRAINT models_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- PostgreSQL database dump complete
--

\unrestrict KjkBUYwhr7V472cXx7GsrnFq2RhhJH6CmmJxkNMbAqsKU1d5QslHOHcw3Socj8h

