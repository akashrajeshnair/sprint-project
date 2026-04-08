--
-- PostgreSQL database dump
--

\restrict zMgB9814eBuSkKpwnyhMIsCTwOkKE9cxdsrhpR9YZWLLmw75gzYBwnY5Hhbngh9

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

ALTER TABLE ONLY public.student_progress DROP CONSTRAINT student_progress_student_profile_id_fkey;
ALTER TABLE ONLY public.student_profiles DROP CONSTRAINT student_profiles_user_id_fkey;
ALTER TABLE ONLY public.sessions DROP CONSTRAINT sessions_user_id_fkey;
ALTER TABLE ONLY public.messages DROP CONSTRAINT messages_session_id_fkey;
ALTER TABLE ONLY public.learning_paths DROP CONSTRAINT learning_paths_student_profile_id_fkey;
ALTER TABLE ONLY public.users DROP CONSTRAINT users_pkey;
ALTER TABLE ONLY public.student_progress DROP CONSTRAINT unique_progress;
ALTER TABLE ONLY public.student_progress DROP CONSTRAINT student_progress_pkey;
ALTER TABLE ONLY public.student_profiles DROP CONSTRAINT student_profiles_user_id_key;
ALTER TABLE ONLY public.student_profiles DROP CONSTRAINT student_profiles_pkey;
ALTER TABLE ONLY public.sessions DROP CONSTRAINT sessions_pkey;
ALTER TABLE ONLY public.messages DROP CONSTRAINT messages_pkey;
ALTER TABLE ONLY public.learning_paths DROP CONSTRAINT learning_paths_pkey;
ALTER TABLE public.users ALTER COLUMN user_id DROP DEFAULT;
ALTER TABLE public.student_profiles ALTER COLUMN student_profile_id DROP DEFAULT;
ALTER TABLE public.sessions ALTER COLUMN session_id DROP DEFAULT;
ALTER TABLE public.messages ALTER COLUMN message_id DROP DEFAULT;
ALTER TABLE public.learning_paths ALTER COLUMN learning_path_id DROP DEFAULT;
DROP SEQUENCE public.users_user_id_seq;
DROP TABLE public.users;
DROP TABLE public.student_progress;
DROP SEQUENCE public.student_profiles_student_profile_id_seq;
DROP TABLE public.student_profiles;
DROP SEQUENCE public.sessions_id_seq;
DROP TABLE public.sessions;
DROP SEQUENCE public.messages_message_id_seq;
DROP TABLE public.messages;
DROP SEQUENCE public.learning_paths_id_seq;
DROP TABLE public.learning_paths;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: learning_paths; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.learning_paths (
    learning_path_id integer NOT NULL,
    student_profile_id integer NOT NULL,
    subject text,
    topics_sequence jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: learning_paths_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.learning_paths_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: learning_paths_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.learning_paths_id_seq OWNED BY public.learning_paths.learning_path_id;


--
-- Name: messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.messages (
    message_id integer NOT NULL,
    session_id integer NOT NULL,
    role text,
    content text,
    tool_calls_used jsonb,
    tokens_used integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: messages_message_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.messages_message_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: messages_message_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.messages_message_id_seq OWNED BY public.messages.message_id;


--
-- Name: sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sessions (
    session_id integer NOT NULL,
    user_id integer NOT NULL,
    subject text,
    topic text,
    difficulty_level text,
    started_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sessions_id_seq OWNED BY public.sessions.session_id;


--
-- Name: student_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_profiles (
    student_profile_id integer NOT NULL,
    user_id integer NOT NULL,
    grade_level text,
    learning_style text,
    subjects_enrolled jsonb,
    xp_points integer DEFAULT 0,
    last_active_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: student_profiles_student_profile_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.student_profiles_student_profile_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: student_profiles_student_profile_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.student_profiles_student_profile_id_seq OWNED BY public.student_profiles.student_profile_id;


--
-- Name: student_progress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_progress (
    student_progress_id integer NOT NULL,
    student_profile_id integer NOT NULL,
    subject text,
    topic text,
    score double precision,
    updated_at timestamp with time zone
);


--
-- Name: student_progress_student_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.student_progress ALTER COLUMN student_progress_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.student_progress_student_progress_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    name character varying(255),
    email character varying(255),
    password character varying(255),
    role character varying(50),
    subject character varying(255),
    "timestamp" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone,
    CONSTRAINT check_role_subject CHECK (((((role)::text = 'teacher'::text) AND (subject IS NOT NULL)) OR (((role)::text = 'student'::text) AND (subject IS NULL)) OR ((role)::text = 'admin'::text)))
);


--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- Name: learning_paths learning_path_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_paths ALTER COLUMN learning_path_id SET DEFAULT nextval('public.learning_paths_id_seq'::regclass);


--
-- Name: messages message_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages ALTER COLUMN message_id SET DEFAULT nextval('public.messages_message_id_seq'::regclass);


--
-- Name: sessions session_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions ALTER COLUMN session_id SET DEFAULT nextval('public.sessions_id_seq'::regclass);


--
-- Name: student_profiles student_profile_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles ALTER COLUMN student_profile_id SET DEFAULT nextval('public.student_profiles_student_profile_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- Data for Name: learning_paths; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.learning_paths (learning_path_id, student_profile_id, subject, topics_sequence, created_at, updated_at) FROM stdin;
1	1	Mathematics	["Algebra Basics", "Linear Equations", "Quadratic Equations", "Polynomials"]	2026-04-08 12:22:28.40004+05:30	2026-04-08 12:22:28.40004+05:30
2	2	Physics	["Units and Measurements", "Kinematics", "Laws of Motion", "Work and Energy"]	2026-04-08 12:22:28.40004+05:30	2026-04-08 12:22:28.40004+05:30
4	3	History	["Indus Valley Civilization", "Vedic Period", "Mauryan Empire", "Chola Empire"]	2026-04-08 12:24:28.365077+05:30	2026-04-08 12:24:28.365077+05:30
\.


--
-- Data for Name: messages; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.messages (message_id, session_id, role, content, tool_calls_used, tokens_used, created_at) FROM stdin;
1	1	user	Can you explain linear equations?	\N	25	2026-04-08 12:29:11.28555+05:30
2	1	assistant	A linear equation is an equation of the form ax + b = 0.	\N	40	2026-04-08 12:29:11.28555+05:30
3	1	assistant	Let’s solve an example: 2x + 4 = 0 → x = -2.	\N	35	2026-04-08 12:29:11.28555+05:30
4	2	user	What is kinematics?	\N	20	2026-04-08 12:29:11.28555+05:30
5	2	assistant	Kinematics is the study of motion without considering forces.	\N	45	2026-04-08 12:29:11.28555+05:30
6	2	assistant	It includes concepts like velocity, acceleration, and displacement.	\N	38	2026-04-08 12:29:11.28555+05:30
7	3	user	Tell me about ancient civilizations.	\N	22	2026-04-08 12:29:11.28555+05:30
8	3	assistant	Ancient civilizations include Mesopotamia, Egypt, Indus Valley, and China.	\N	50	2026-04-08 12:29:11.28555+05:30
9	3	assistant	They developed writing, agriculture, and early governance systems.	\N	42	2026-04-08 12:29:11.28555+05:30
\.


--
-- Data for Name: sessions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sessions (session_id, user_id, subject, topic, difficulty_level, started_at, updated_at) FROM stdin;
1	6	Mathematics	Linear Equations	easy	2026-04-08 12:27:33.274217+05:30	2026-04-08 12:27:33.274217+05:30
2	7	Physics	Kinematics	medium	2026-04-08 12:27:33.274217+05:30	2026-04-08 12:27:33.274217+05:30
3	8	History	Ancient Civilizations	hard	2026-04-08 12:27:33.274217+05:30	2026-04-08 12:27:33.274217+05:30
\.


--
-- Data for Name: student_profiles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.student_profiles (student_profile_id, user_id, grade_level, learning_style, subjects_enrolled, xp_points, last_active_at) FROM stdin;
1	6	10	theoretical	["Mathematics", "Physics"]	120	2026-04-08 12:21:22.678266+05:30
2	7	9	theoretical	["Chemistry", "Biology"]	80	2026-04-08 12:21:22.678266+05:30
3	8	11	example-based	["History", "Mathematics"]	200	2026-04-08 12:21:22.678266+05:30
4	9	10	example-based	["Physics", "Chemistry"]	150	2026-04-08 12:21:22.678266+05:30
5	10	12	theoretical	["Mathematics", "History"]	300	2026-04-08 12:21:22.678266+05:30
\.


--
-- Data for Name: student_progress; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.student_progress (student_progress_id, student_profile_id, subject, topic, score, updated_at) FROM stdin;
1	1	Mathematics	Algebra Basics	0.75	2026-04-08 12:25:58.403377+05:30
2	1	Mathematics	Linear Equations	0.6	2026-04-08 12:25:58.403377+05:30
3	2	Physics	Kinematics	0.8	2026-04-08 12:25:58.403377+05:30
4	2	Physics	Laws of Motion	0.65	2026-04-08 12:25:58.403377+05:30
5	3	History	Ancient Civilizations	0.9	2026-04-08 12:25:58.403377+05:30
6	3	History	Medieval Period	0.7	2026-04-08 12:25:58.403377+05:30
7	4	Chemistry	Atomic Structure	0.55	2026-04-08 12:25:58.403377+05:30
8	4	Chemistry	Periodic Table	0.68	2026-04-08 12:25:58.403377+05:30
9	5	Mathematics	Quadratic Equations	0.85	2026-04-08 12:25:58.403377+05:30
10	5	History	Modern History	0.78	2026-04-08 12:25:58.403377+05:30
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (user_id, name, email, password, role, subject, "timestamp", updated_at) FROM stdin;
1	admin	admin@gmail.com	admin123	admin	\N	2026-04-08 10:59:33.510393+05:30	\N
2	Alice Sharma	alice.sharma@gmail.com	pass123	teacher	Mathematics	2026-04-08 12:16:27.001227+05:30	\N
3	Ravi Kumar	ravi.kumar@gmail.com	pass123	teacher	Physics	2026-04-08 12:16:27.001227+05:30	\N
4	Neha Iyer	neha.iyer@gmail.com	pass123	teacher	Chemistry	2026-04-08 12:16:27.001227+05:30	\N
5	Arjun Reddy	arjun.reddy@gmail.com	pass123	teacher	History	2026-04-08 12:16:27.001227+05:30	\N
6	Rahul Verma	rahul.verma@gmail.com	pass123	student	\N	2026-04-08 12:16:37.436184+05:30	\N
7	Sneha Patel	sneha.patel@gmail.com	pass123	student	\N	2026-04-08 12:16:37.436184+05:30	\N
8	Kiran Das	kiran.das@gmail.com	pass123	student	\N	2026-04-08 12:16:37.436184+05:30	\N
9	Ananya Gupta	ananya.gupta@gmail.com	pass123	student	\N	2026-04-08 12:16:37.436184+05:30	\N
10	Vikram Singh	vikram.singh@gmail.com	pass123	student	\N	2026-04-08 12:16:37.436184+05:30	\N
\.


--
-- Name: learning_paths_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.learning_paths_id_seq', 4, true);


--
-- Name: messages_message_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.messages_message_id_seq', 9, true);


--
-- Name: sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sessions_id_seq', 3, true);


--
-- Name: student_profiles_student_profile_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.student_profiles_student_profile_id_seq', 5, true);


--
-- Name: student_progress_student_progress_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.student_progress_student_progress_id_seq', 10, true);


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_user_id_seq', 10, true);


--
-- Name: learning_paths learning_paths_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_paths
    ADD CONSTRAINT learning_paths_pkey PRIMARY KEY (learning_path_id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (message_id);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (session_id);


--
-- Name: student_profiles student_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_pkey PRIMARY KEY (student_profile_id);


--
-- Name: student_profiles student_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_user_id_key UNIQUE (user_id);


--
-- Name: student_progress student_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_progress
    ADD CONSTRAINT student_progress_pkey PRIMARY KEY (student_progress_id);


--
-- Name: student_progress unique_progress; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_progress
    ADD CONSTRAINT unique_progress UNIQUE (student_profile_id, subject, topic);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: learning_paths learning_paths_student_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_paths
    ADD CONSTRAINT learning_paths_student_profile_id_fkey FOREIGN KEY (student_profile_id) REFERENCES public.student_profiles(student_profile_id) ON DELETE CASCADE;


--
-- Name: messages messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(session_id) ON DELETE CASCADE;


--
-- Name: sessions sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: student_profiles student_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: student_progress student_progress_student_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_progress
    ADD CONSTRAINT student_progress_student_profile_id_fkey FOREIGN KEY (student_profile_id) REFERENCES public.student_profiles(student_profile_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict zMgB9814eBuSkKpwnyhMIsCTwOkKE9cxdsrhpR9YZWLLmw75gzYBwnY5Hhbngh9

