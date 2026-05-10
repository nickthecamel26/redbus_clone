--
-- PostgreSQL database dump
--

\restrict nEjWGOqnWJiD5P27CA3JC1Drxee5ShNWsE78Wv0Gw412uKUfEw8hAfWXlED2h0K

-- Dumped from database version 15.17
-- Dumped by pg_dump version 15.17

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
-- Name: bookingstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.bookingstatus AS ENUM (
    'CONFIRMED',
    'PENDING',
    'CANCELLED',
    'EXPIRED'
);


ALTER TYPE public.bookingstatus OWNER TO postgres;

--
-- Name: bustype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.bustype AS ENUM (
    'AC_SLEEPER',
    'NON_AC_SLEEPER',
    'AC_SEATER',
    'NON_AC_SEATER'
);


ALTER TYPE public.bustype OWNER TO postgres;

--
-- Name: deck; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.deck AS ENUM (
    'LOWER',
    'UPPER'
);


ALTER TYPE public.deck OWNER TO postgres;

--
-- Name: seattype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.seattype AS ENUM (
    'SLEEPER',
    'SEATER'
);


ALTER TYPE public.seattype OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: booking_seats; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.booking_seats (
    booking_id integer NOT NULL,
    seat_id integer NOT NULL
);


ALTER TABLE public.booking_seats OWNER TO postgres;

--
-- Name: bookings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bookings (
    id integer NOT NULL,
    user_id integer NOT NULL,
    trip_id integer NOT NULL,
    seat_id integer NOT NULL,
    status public.bookingstatus,
    booking_date timestamp with time zone DEFAULT now(),
    total_price numeric(10,2) DEFAULT 0.00 NOT NULL
);


ALTER TABLE public.bookings OWNER TO postgres;

--
-- Name: bookings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bookings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.bookings_id_seq OWNER TO postgres;

--
-- Name: bookings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bookings_id_seq OWNED BY public.bookings.id;


--
-- Name: buses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.buses (
    id integer NOT NULL,
    name character varying NOT NULL,
    bus_type public.bustype NOT NULL,
    total_seats integer NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.buses OWNER TO postgres;

--
-- Name: buses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.buses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.buses_id_seq OWNER TO postgres;

--
-- Name: buses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.buses_id_seq OWNED BY public.buses.id;


--
-- Name: routes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.routes (
    id integer NOT NULL,
    source_city character varying NOT NULL,
    destination_city character varying NOT NULL,
    distance_km numeric(10,2) NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.routes OWNER TO postgres;

--
-- Name: routes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.routes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.routes_id_seq OWNER TO postgres;

--
-- Name: routes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.routes_id_seq OWNED BY public.routes.id;


--
-- Name: seats; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.seats (
    id integer NOT NULL,
    bus_id integer NOT NULL,
    seat_number character varying NOT NULL,
    deck integer NOT NULL,
    is_available boolean,
    created_at timestamp with time zone DEFAULT now(),
    "row" integer NOT NULL,
    "column" integer NOT NULL,
    is_sleeper boolean,
    is_window boolean DEFAULT false
);


ALTER TABLE public.seats OWNER TO postgres;

--
-- Name: seats_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.seats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.seats_id_seq OWNER TO postgres;

--
-- Name: seats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.seats_id_seq OWNED BY public.seats.id;


--
-- Name: trips; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.trips (
    id integer NOT NULL,
    bus_id integer NOT NULL,
    route_id integer NOT NULL,
    departure_time timestamp with time zone NOT NULL,
    arrival_time timestamp with time zone NOT NULL,
    price numeric(10,2) NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.trips OWNER TO postgres;

--
-- Name: trips_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.trips_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.trips_id_seq OWNER TO postgres;

--
-- Name: trips_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.trips_id_seq OWNED BY public.trips.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying NOT NULL,
    hashed_password character varying NOT NULL,
    full_name character varying,
    is_active boolean,
    created_at timestamp with time zone DEFAULT now(),
    name character varying,
    phone character varying,
    role character varying DEFAULT 'customer'::character varying
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: bookings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bookings ALTER COLUMN id SET DEFAULT nextval('public.bookings_id_seq'::regclass);


--
-- Name: buses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.buses ALTER COLUMN id SET DEFAULT nextval('public.buses_id_seq'::regclass);


--
-- Name: routes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.routes ALTER COLUMN id SET DEFAULT nextval('public.routes_id_seq'::regclass);


--
-- Name: seats id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seats ALTER COLUMN id SET DEFAULT nextval('public.seats_id_seq'::regclass);


--
-- Name: trips id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trips ALTER COLUMN id SET DEFAULT nextval('public.trips_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
2026_05_01_add_is_window
\.


--
-- Data for Name: booking_seats; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.booking_seats (booking_id, seat_id) FROM stdin;
20	148
21	148
22	145
23	146
24	147
25	145
26	146
27	147
28	1
29	145
30	15
31	16
32	5
33	6
34	7
35	3
36	8
37	37
38	145
39	5
40	4
41	4
42	193
43	147
44	147
45	184
46	2
47	146
48	146
49	182
50	2
51	146
52	146
53	2
54	15
\.


--
-- Data for Name: bookings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bookings (id, user_id, trip_id, seat_id, status, booking_date, total_price) FROM stdin;
20	13	1	148	CANCELLED	2026-05-06 13:43:57.860374+00	899.00
21	13	1	148	CONFIRMED	2026-05-07 05:40:26.224606+00	899.00
22	13	1	145	CANCELLED	2026-05-07 06:03:12.748225+00	899.00
23	13	1	146	CANCELLED	2026-05-07 06:03:12.748225+00	899.00
24	13	1	147	CANCELLED	2026-05-07 06:03:12.748225+00	899.00
25	13	1	145	CANCELLED	2026-05-07 06:29:20.470043+00	899.00
26	13	1	146	CANCELLED	2026-05-07 06:29:20.470043+00	899.00
27	13	1	147	CANCELLED	2026-05-07 06:29:20.470043+00	899.00
28	18	1	1	CONFIRMED	2026-05-07 06:50:01.340772+00	899.00
32	13	1	5	CONFIRMED	2026-05-07 08:44:04.73423+00	899.00
29	13	1	145	EXPIRED	2026-05-07 07:58:19.427588+00	899.00
30	13	1	15	EXPIRED	2026-05-07 08:15:19.67673+00	899.00
31	13	1	16	EXPIRED	2026-05-07 08:15:19.67673+00	899.00
33	13	1	6	EXPIRED	2000-01-01 00:00:00+00	899.00
34	13	1	7	EXPIRED	2026-05-08 08:10:52.46356+00	899.00
35	13	1	3	CANCELLED	2026-05-08 09:57:47.175082+00	899.00
36	13	1	8	CANCELLED	2026-05-09 05:00:06.061852+00	899.00
37	13	2	37	CANCELLED	2026-05-09 05:09:56.346873+00	899.00
38	13	27	145	CONFIRMED	2026-05-09 07:12:40.931532+00	1045.00
39	13	28	5	CANCELLED	2026-05-09 11:59:22.438575+00	950.00
40	13	28	4	CANCELLED	2026-05-09 11:59:22.438575+00	950.00
41	13	26	4	CANCELLED	2026-05-09 12:12:19.495846+00	900.00
42	13	1	193	CONFIRMED	2026-05-09 12:39:12.87502+00	899.00
43	13	28	147	CANCELLED	2026-05-09 14:38:58.734866+00	950.00
44	13	28	147	CANCELLED	2026-05-09 14:57:35.759562+00	950.00
45	13	28	184	CANCELLED	2026-05-09 15:07:09.090388+00	950.00
46	13	28	2	CANCELLED	2026-05-09 15:11:04.570737+00	950.00
47	13	28	146	CANCELLED	2026-05-10 05:30:11.378534+00	950.00
48	13	28	146	CANCELLED	2026-05-10 06:17:23.105587+00	950.00
49	13	28	182	CANCELLED	2026-05-10 06:25:52.383076+00	950.00
50	13	28	2	CANCELLED	2026-05-10 06:29:14.685814+00	950.00
51	13	28	146	CANCELLED	2026-05-10 06:41:32.434371+00	950.00
52	13	28	146	CONFIRMED	2026-05-10 06:54:01.027996+00	950.00
53	13	28	2	CONFIRMED	2026-05-10 07:04:26.122962+00	950.00
54	13	28	15	CONFIRMED	2026-05-10 07:16:22.066894+00	950.00
\.


--
-- Data for Name: buses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.buses (id, name, bus_type, total_seats, created_at) FROM stdin;
1	Theni Travels - AC Sleeper	AC_SLEEPER	36	2026-05-01 07:27:10.098543+00
2	Madurai Express - AC Seater	AC_SEATER	40	2026-05-01 07:27:10.098543+00
3	Chennai King - Non-AC Sleeper	NON_AC_SLEEPER	30	2026-05-01 07:27:10.098543+00
4	South India Travels - Non-AC Seater	NON_AC_SEATER	45	2026-05-01 07:27:10.098543+00
7	KPN Travels AC Sleeper	AC_SLEEPER	30	2026-05-09 06:00:30.389395+00
\.


--
-- Data for Name: routes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.routes (id, source_city, destination_city, distance_km, created_at) FROM stdin;
1	Chennai	Madurai	450.00	2026-05-01 07:27:10.098543+00
2	Madurai	Chennai	450.00	2026-05-01 07:27:10.098543+00
3	Chennai	Theni	520.00	2026-05-01 07:27:10.098543+00
4	Theni	Chennai	520.00	2026-05-01 07:27:10.098543+00
5	Madurai	Theni	75.00	2026-05-01 07:27:10.098543+00
6	Theni	Madurai	75.00	2026-05-01 07:27:10.098543+00
8	Chennai	Bangalore	250.00	2026-05-09 05:58:34.949245+00
\.


--
-- Data for Name: seats; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.seats (id, bus_id, seat_number, deck, is_available, created_at, "row", "column", is_sleeper, is_window) FROM stdin;
145	1	L1	0	f	2026-05-06 11:54:24.293208+00	1	1	t	t
82	3	3B	0	f	2026-05-01 07:27:10.098543+00	3	2	t	f
148	1	R2	0	f	2026-05-06 11:54:24.293208+00	1	5	t	t
146	1	L2	0	f	2026-05-06 11:54:24.293208+00	1	2	t	f
147	1	R1	0	t	2026-05-06 11:54:24.293208+00	1	4	t	f
48	2	3D	0	t	2026-05-01 07:27:10.098543+00	3	4	t	f
49	2	4A	0	t	2026-05-01 07:27:10.098543+00	4	1	t	f
50	2	4B	0	t	2026-05-01 07:27:10.098543+00	4	2	t	f
103	3	8C	1	t	2026-05-01 07:27:10.098543+00	8	3	t	f
104	3	8D	1	t	2026-05-01 07:27:10.098543+00	8	4	t	f
105	3	9A	1	t	2026-05-01 07:27:10.098543+00	9	1	t	f
106	3	9B	1	t	2026-05-01 07:27:10.098543+00	9	2	t	f
107	3	9C	1	t	2026-05-01 07:27:10.098543+00	9	3	t	f
54	2	5B	0	t	2026-05-01 07:27:10.098543+00	5	2	t	f
55	2	5C	0	t	2026-05-01 07:27:10.098543+00	5	3	t	f
56	2	5D	0	t	2026-05-01 07:27:10.098543+00	5	4	t	f
57	2	6A	1	t	2026-05-01 07:27:10.098543+00	6	1	t	f
58	2	6B	1	t	2026-05-01 07:27:10.098543+00	6	2	t	f
59	2	6C	1	t	2026-05-01 07:27:10.098543+00	6	3	t	f
60	2	6D	1	t	2026-05-01 07:27:10.098543+00	6	4	t	f
61	2	7A	1	t	2026-05-01 07:27:10.098543+00	7	1	t	f
62	2	7B	1	t	2026-05-01 07:27:10.098543+00	7	2	t	f
63	2	7C	1	t	2026-05-01 07:27:10.098543+00	7	3	t	f
64	2	7D	1	t	2026-05-01 07:27:10.098543+00	7	4	t	f
65	2	8A	1	t	2026-05-01 07:27:10.098543+00	8	1	t	f
66	2	8B	1	t	2026-05-01 07:27:10.098543+00	8	2	t	f
67	2	8C	1	t	2026-05-01 07:27:10.098543+00	8	3	t	f
68	2	8D	1	t	2026-05-01 07:27:10.098543+00	8	4	t	f
69	2	9A	1	t	2026-05-01 07:27:10.098543+00	9	1	t	f
70	2	9B	1	t	2026-05-01 07:27:10.098543+00	9	2	t	f
71	2	9C	1	t	2026-05-01 07:27:10.098543+00	9	3	t	f
72	2	9D	1	t	2026-05-01 07:27:10.098543+00	9	4	t	f
73	3	1A	0	t	2026-05-01 07:27:10.098543+00	1	1	t	f
74	3	1B	0	t	2026-05-01 07:27:10.098543+00	1	2	t	f
75	3	1C	0	t	2026-05-01 07:27:10.098543+00	1	3	t	f
76	3	1D	0	t	2026-05-01 07:27:10.098543+00	1	4	t	f
77	3	2A	0	t	2026-05-01 07:27:10.098543+00	2	1	t	f
78	3	2B	0	t	2026-05-01 07:27:10.098543+00	2	2	t	f
79	3	2C	0	t	2026-05-01 07:27:10.098543+00	2	3	t	f
80	3	2D	0	t	2026-05-01 07:27:10.098543+00	2	4	t	f
81	3	3A	0	t	2026-05-01 07:27:10.098543+00	3	1	t	f
83	3	3C	0	t	2026-05-01 07:27:10.098543+00	3	3	t	f
84	3	3D	0	t	2026-05-01 07:27:10.098543+00	3	4	t	f
85	3	4A	0	t	2026-05-01 07:27:10.098543+00	4	1	t	f
86	3	4B	0	t	2026-05-01 07:27:10.098543+00	4	2	t	f
87	3	4C	0	t	2026-05-01 07:27:10.098543+00	4	3	t	f
88	3	4D	0	t	2026-05-01 07:27:10.098543+00	4	4	t	f
89	3	5A	0	t	2026-05-01 07:27:10.098543+00	5	1	t	f
90	3	5B	0	t	2026-05-01 07:27:10.098543+00	5	2	t	f
91	3	5C	0	t	2026-05-01 07:27:10.098543+00	5	3	t	f
92	3	5D	0	t	2026-05-01 07:27:10.098543+00	5	4	t	f
93	3	6A	1	t	2026-05-01 07:27:10.098543+00	6	1	t	f
94	3	6B	1	t	2026-05-01 07:27:10.098543+00	6	2	t	f
95	3	6C	1	t	2026-05-01 07:27:10.098543+00	6	3	t	f
96	3	6D	1	t	2026-05-01 07:27:10.098543+00	6	4	t	f
97	3	7A	1	t	2026-05-01 07:27:10.098543+00	7	1	t	f
98	3	7B	1	t	2026-05-01 07:27:10.098543+00	7	2	t	f
99	3	7C	1	t	2026-05-01 07:27:10.098543+00	7	3	t	f
100	3	7D	1	t	2026-05-01 07:27:10.098543+00	7	4	t	f
101	3	8A	1	t	2026-05-01 07:27:10.098543+00	8	1	t	f
102	3	8B	1	t	2026-05-01 07:27:10.098543+00	8	2	t	f
149	7	L1	0	t	2026-05-09 06:00:30.389395+00	1	1	t	t
150	7	L2	0	t	2026-05-09 06:00:30.389395+00	1	2	t	t
151	7	L1	0	t	2026-05-09 06:00:30.389395+00	2	1	t	t
152	7	L2	0	t	2026-05-09 06:00:30.389395+00	2	2	t	t
153	7	L1	0	t	2026-05-09 06:00:30.389395+00	3	1	t	t
154	7	L2	0	t	2026-05-09 06:00:30.389395+00	3	2	t	t
155	7	L1	0	t	2026-05-09 06:00:30.389395+00	4	1	t	t
156	7	L2	0	t	2026-05-09 06:00:30.389395+00	4	2	t	t
157	7	L1	0	t	2026-05-09 06:00:30.389395+00	5	1	t	t
158	7	L2	0	t	2026-05-09 06:00:30.389395+00	5	2	t	t
159	7	L1	0	t	2026-05-09 06:00:30.389395+00	6	1	t	t
160	7	L2	0	t	2026-05-09 06:00:30.389395+00	6	2	t	t
161	7	L1	0	t	2026-05-09 06:00:30.389395+00	7	1	t	t
162	7	L2	0	t	2026-05-09 06:00:30.389395+00	7	2	t	t
163	7	U1	1	t	2026-05-09 06:00:30.389395+00	1	1	t	t
164	7	U2	1	t	2026-05-09 06:00:30.389395+00	1	2	t	t
108	3	9D	1	t	2026-05-01 07:27:10.098543+00	9	4	t	f
109	4	1A	0	t	2026-05-01 07:27:10.098543+00	1	1	t	f
110	4	1B	0	t	2026-05-01 07:27:10.098543+00	1	2	t	f
111	4	1C	0	t	2026-05-01 07:27:10.098543+00	1	3	t	f
112	4	1D	0	t	2026-05-01 07:27:10.098543+00	1	4	t	f
113	4	2A	0	t	2026-05-01 07:27:10.098543+00	2	1	t	f
114	4	2B	0	t	2026-05-01 07:27:10.098543+00	2	2	t	f
115	4	2C	0	t	2026-05-01 07:27:10.098543+00	2	3	t	f
116	4	2D	0	t	2026-05-01 07:27:10.098543+00	2	4	t	f
117	4	3A	0	t	2026-05-01 07:27:10.098543+00	3	1	t	f
119	4	3C	0	t	2026-05-01 07:27:10.098543+00	3	3	t	f
120	4	3D	0	t	2026-05-01 07:27:10.098543+00	3	4	t	f
121	4	4A	0	t	2026-05-01 07:27:10.098543+00	4	1	t	f
122	4	4B	0	t	2026-05-01 07:27:10.098543+00	4	2	t	f
123	4	4C	0	t	2026-05-01 07:27:10.098543+00	4	3	t	f
124	4	4D	0	t	2026-05-01 07:27:10.098543+00	4	4	t	f
125	4	5A	0	t	2026-05-01 07:27:10.098543+00	5	1	t	f
126	4	5B	0	t	2026-05-01 07:27:10.098543+00	5	2	t	f
127	4	5C	0	t	2026-05-01 07:27:10.098543+00	5	3	t	f
128	4	5D	0	t	2026-05-01 07:27:10.098543+00	5	4	t	f
129	4	6A	1	t	2026-05-01 07:27:10.098543+00	6	1	t	f
130	4	6B	1	t	2026-05-01 07:27:10.098543+00	6	2	t	f
131	4	6C	1	t	2026-05-01 07:27:10.098543+00	6	3	t	f
132	4	6D	1	t	2026-05-01 07:27:10.098543+00	6	4	t	f
133	4	7A	1	t	2026-05-01 07:27:10.098543+00	7	1	t	f
134	4	7B	1	t	2026-05-01 07:27:10.098543+00	7	2	t	f
135	4	7C	1	t	2026-05-01 07:27:10.098543+00	7	3	t	f
136	4	7D	1	t	2026-05-01 07:27:10.098543+00	7	4	t	f
137	4	8A	1	t	2026-05-01 07:27:10.098543+00	8	1	t	f
138	4	8B	1	t	2026-05-01 07:27:10.098543+00	8	2	t	f
139	4	8C	1	t	2026-05-01 07:27:10.098543+00	8	3	t	f
140	4	8D	1	t	2026-05-01 07:27:10.098543+00	8	4	t	f
141	4	9A	1	t	2026-05-01 07:27:10.098543+00	9	1	t	f
142	4	9B	1	t	2026-05-01 07:27:10.098543+00	9	2	t	f
143	4	9C	1	t	2026-05-01 07:27:10.098543+00	9	3	t	f
144	4	9D	1	t	2026-05-01 07:27:10.098543+00	9	4	t	f
9	1	3A	0	t	2026-05-01 07:27:10.098543+00	3	1	t	f
11	1	3C	0	t	2026-05-01 07:27:10.098543+00	3	3	t	f
12	1	3D	0	t	2026-05-01 07:27:10.098543+00	3	4	t	f
13	1	4A	0	t	2026-05-01 07:27:10.098543+00	4	1	t	f
14	1	4B	0	t	2026-05-01 07:27:10.098543+00	4	2	t	f
1	1	1A	0	f	2026-05-01 07:27:10.098543+00	1	1	t	f
16	1	4D	0	t	2026-05-01 07:27:10.098543+00	4	4	t	f
165	7	U1	1	t	2026-05-09 06:00:30.389395+00	2	1	t	t
166	7	U2	1	t	2026-05-09 06:00:30.389395+00	2	2	t	t
167	7	U1	1	t	2026-05-09 06:00:30.389395+00	3	1	t	t
168	7	U2	1	t	2026-05-09 06:00:30.389395+00	3	2	t	t
169	7	U1	1	t	2026-05-09 06:00:30.389395+00	4	1	t	t
170	7	U2	1	t	2026-05-09 06:00:30.389395+00	4	2	t	t
171	7	U1	1	t	2026-05-09 06:00:30.389395+00	5	1	t	t
172	7	U2	1	t	2026-05-09 06:00:30.389395+00	5	2	t	t
173	7	U1	1	t	2026-05-09 06:00:30.389395+00	6	1	t	t
174	7	U2	1	t	2026-05-09 06:00:30.389395+00	6	2	t	t
175	7	U1	1	t	2026-05-09 06:00:30.389395+00	7	1	t	t
176	7	U2	1	t	2026-05-09 06:00:30.389395+00	7	2	t	t
177	7	U1	2	t	2026-05-09 06:00:30.389395+00	1	1	t	t
178	7	U2	2	t	2026-05-09 06:00:30.389395+00	1	2	t	t
189	1	U1	1	t	2026-05-09 12:24:16.373105+00	1	1	\N	f
118	4	3B	0	f	2026-05-01 07:27:10.098543+00	3	2	t	f
2	1	1B	0	f	2026-05-01 07:27:10.098543+00	1	2	t	f
15	1	4C	0	f	2026-05-01 07:27:10.098543+00	4	3	t	f
37	2	1A	0	t	2026-05-01 07:27:10.098543+00	1	1	t	f
183	1	A2	0	t	2026-05-09 12:20:38.76304+00	2	1	\N	f
185	1	B2	1	t	2026-05-09 12:20:38.76304+00	2	1	\N	f
193	1	3B	0	f	2026-05-09 12:38:48.624166+00	3	2	\N	f
184	1	B1	1	t	2026-05-09 12:20:38.76304+00	1	1	\N	f
182	1	A1	0	t	2026-05-09 12:20:38.76304+00	1	1	\N	f
17	1	5A	0	t	2026-05-01 07:27:10.098543+00	5	1	t	f
18	1	5B	0	t	2026-05-01 07:27:10.098543+00	5	2	t	f
19	1	5C	0	t	2026-05-01 07:27:10.098543+00	5	3	t	f
20	1	5D	0	t	2026-05-01 07:27:10.098543+00	5	4	t	f
21	1	6A	1	t	2026-05-01 07:27:10.098543+00	6	1	t	f
22	1	6B	1	t	2026-05-01 07:27:10.098543+00	6	2	t	f
23	1	6C	1	t	2026-05-01 07:27:10.098543+00	6	3	t	f
24	1	6D	1	t	2026-05-01 07:27:10.098543+00	6	4	t	f
25	1	7A	1	t	2026-05-01 07:27:10.098543+00	7	1	t	f
26	1	7B	1	t	2026-05-01 07:27:10.098543+00	7	2	t	f
27	1	7C	1	t	2026-05-01 07:27:10.098543+00	7	3	t	f
28	1	7D	1	t	2026-05-01 07:27:10.098543+00	7	4	t	f
29	1	8A	1	t	2026-05-01 07:27:10.098543+00	8	1	t	f
30	1	8B	1	t	2026-05-01 07:27:10.098543+00	8	2	t	f
31	1	8C	1	t	2026-05-01 07:27:10.098543+00	8	3	t	f
32	1	8D	1	t	2026-05-01 07:27:10.098543+00	8	4	t	f
33	1	9A	1	t	2026-05-01 07:27:10.098543+00	9	1	t	f
34	1	9B	1	t	2026-05-01 07:27:10.098543+00	9	2	t	f
35	1	9C	1	t	2026-05-01 07:27:10.098543+00	9	3	t	f
36	1	9D	1	t	2026-05-01 07:27:10.098543+00	9	4	t	f
38	2	1B	0	t	2026-05-01 07:27:10.098543+00	1	2	t	f
39	2	1C	0	t	2026-05-01 07:27:10.098543+00	1	3	t	f
40	2	1D	0	t	2026-05-01 07:27:10.098543+00	1	4	t	f
6	1	2B	0	t	2026-05-01 07:27:10.098543+00	2	2	t	f
7	1	2C	0	t	2026-05-01 07:27:10.098543+00	2	3	t	f
3	1	1C	0	t	2026-05-01 07:27:10.098543+00	1	3	t	f
41	2	2A	0	t	2026-05-01 07:27:10.098543+00	2	1	t	f
42	2	2B	0	t	2026-05-01 07:27:10.098543+00	2	2	t	f
43	2	2C	0	t	2026-05-01 07:27:10.098543+00	2	3	t	f
44	2	2D	0	t	2026-05-01 07:27:10.098543+00	2	4	t	f
45	2	3A	0	t	2026-05-01 07:27:10.098543+00	3	1	t	f
47	2	3C	0	t	2026-05-01 07:27:10.098543+00	3	3	t	f
51	2	4C	0	t	2026-05-01 07:27:10.098543+00	4	3	t	f
52	2	4D	0	t	2026-05-01 07:27:10.098543+00	4	4	t	f
53	2	5A	0	t	2026-05-01 07:27:10.098543+00	5	1	t	f
8	1	2D	0	t	2026-05-01 07:27:10.098543+00	2	4	t	f
5	1	2A	0	t	2026-05-01 07:27:10.098543+00	2	1	t	f
4	1	1D	0	t	2026-05-01 07:27:10.098543+00	1	4	t	f
187	1	3C	0	t	2026-05-09 12:24:04.640893+00	3	3	\N	f
188	1	3D	0	t	2026-05-09 12:24:04.640893+00	3	5	\N	f
46	2	3B	0	f	2026-05-01 07:27:10.098543+00	3	2	t	f
\.


--
-- Data for Name: trips; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.trips (id, bus_id, route_id, departure_time, arrival_time, price, created_at) FROM stdin;
2	2	1	2026-05-01 14:00:00+00	2026-05-01 22:00:00+00	899.00	2026-05-01 07:27:10.098543+00
3	3	1	2026-05-01 21:00:00+00	2026-05-02 05:00:00+00	899.00	2026-05-01 07:27:10.098543+00
4	1	2	2026-05-01 06:00:00+00	2026-05-01 14:00:00+00	899.00	2026-05-01 07:27:10.098543+00
5	2	2	2026-05-01 14:00:00+00	2026-05-01 22:00:00+00	899.00	2026-05-01 07:27:10.098543+00
6	3	2	2026-05-01 21:00:00+00	2026-05-02 05:00:00+00	899.00	2026-05-01 07:27:10.098543+00
7	1	3	2026-05-01 06:00:00+00	2026-05-01 14:00:00+00	999.00	2026-05-01 07:27:10.098543+00
8	2	3	2026-05-01 14:00:00+00	2026-05-01 22:00:00+00	999.00	2026-05-01 07:27:10.098543+00
9	3	3	2026-05-01 21:00:00+00	2026-05-02 05:00:00+00	999.00	2026-05-01 07:27:10.098543+00
10	1	4	2026-05-01 06:00:00+00	2026-05-01 14:00:00+00	999.00	2026-05-01 07:27:10.098543+00
11	2	4	2026-05-01 14:00:00+00	2026-05-01 22:00:00+00	999.00	2026-05-01 07:27:10.098543+00
12	3	4	2026-05-01 21:00:00+00	2026-05-02 05:00:00+00	999.00	2026-05-01 07:27:10.098543+00
13	1	5	2026-05-01 06:00:00+00	2026-05-01 14:00:00+00	199.00	2026-05-01 07:27:10.098543+00
14	2	5	2026-05-01 14:00:00+00	2026-05-01 22:00:00+00	199.00	2026-05-01 07:27:10.098543+00
15	3	5	2026-05-01 21:00:00+00	2026-05-02 05:00:00+00	199.00	2026-05-01 07:27:10.098543+00
16	1	6	2026-05-01 06:00:00+00	2026-05-01 14:00:00+00	199.00	2026-05-01 07:27:10.098543+00
17	2	6	2026-05-01 14:00:00+00	2026-05-01 22:00:00+00	199.00	2026-05-01 07:27:10.098543+00
18	3	6	2026-05-01 21:00:00+00	2026-05-02 05:00:00+00	199.00	2026-05-01 07:27:10.098543+00
1	1	1	2026-05-03 08:55:17.025945+00	2026-05-01 14:00:00+00	899.00	2026-05-01 07:27:10.098543+00
20	1	1	2026-05-10 09:00:00+00	2026-05-10 17:30:00+00	900.00	2026-05-09 06:31:33.545435+00
21	1	1	2026-05-11 09:00:00+00	2026-05-11 17:30:00+00	900.00	2026-05-09 06:31:33.545435+00
22	1	1	2026-05-12 09:00:00+00	2026-05-12 17:30:00+00	900.00	2026-05-09 06:31:33.545435+00
23	1	1	2026-05-13 09:00:00+00	2026-05-13 17:30:00+00	900.00	2026-05-09 06:31:33.545435+00
24	1	1	2026-05-14 09:00:00+00	2026-05-14 17:30:00+00	900.00	2026-05-09 06:31:33.545435+00
25	1	1	2026-05-15 09:00:00+00	2026-05-15 17:30:00+00	900.00	2026-05-09 06:31:33.545435+00
26	1	1	2026-05-16 09:00:00+00	2026-05-16 17:30:00+00	900.00	2026-05-09 06:31:33.545435+00
27	1	1	2026-05-15 21:30:00+00	2026-05-16 05:00:00+00	950.00	2026-05-09 07:03:02.147917+00
28	1	1	2026-05-16 21:30:00+00	2026-05-17 05:00:00+00	950.00	2026-05-09 07:03:02.147917+00
29	1	1	2026-05-17 21:30:00+00	2026-05-18 05:00:00+00	950.00	2026-05-09 07:03:02.147917+00
30	1	1	2026-05-18 21:30:00+00	2026-05-19 05:00:00+00	950.00	2026-05-09 07:03:02.147917+00
31	1	1	2026-05-19 21:30:00+00	2026-05-20 05:00:00+00	950.00	2026-05-09 07:03:02.147917+00
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, email, hashed_password, full_name, is_active, created_at, name, phone, role) FROM stdin;
1	admin@redbus.com	hashed_password	Admin User	t	2026-05-01 07:27:10.098543+00	\N	\N	customer
2	user@example.com	hashed_password	Regular User	t	2026-05-01 07:27:10.098543+00	\N	\N	customer
8	newuser7@example.com	$2b$12$iPL/eLHw3YicQYHxKEDkXeyra8JlXnhva5civiZmEQZ5ms0p8kgC.	New User 7	t	2026-05-01 12:49:05.634993+00	\N	+91-9876543215	customer
9	architect_test@example.com	$2b$12$wJEIT71sVAejNxOeJs05AuBa4Pg6ubEgcU8P1CL7G7/Lvjx9BcD16	Architect Tester	t	2026-05-01 12:51:51.424009+00	\N	+91-9999988888	customer
10	nikhil_test_final@example.com	$2b$12$Tkvf4sXdsjmCIPnS5ZZPy./RMjbZyVKQ/K.5O2k/WC7ceDPZadKi2	Nikhil Sridhar	t	2026-05-06 11:35:27.914114+00	\N	9876543210	customer
11	testuser8@example.com	$2b$12$vhSzJJzzVFBB5fN79jTtceYdBklqisQqm914iGUrwmN71XBJ7O/Oq	Test User 8	t	2026-05-06 11:39:11.926128+00	\N	+91-9876543216	customer
12	testuser9@example.com	$2b$12$cySdydTjj0dnKV2edY8Ygue7YMgxDkGCs/hkFosa0hL41fgEEy28C	Test User 9	t	2026-05-06 11:39:25.748031+00	\N	\N	customer
13	nikhil_test_final_v2@example.com	$2b$12$xQK4Fm2hVKHCp0mwHpCjfuoXprVMWgQRp3iM0AuvrmNGGsTbzOHq6	Nikhil Sridhar	t	2026-05-06 11:41:58.849047+00	\N	9876543210	customer
14	dashboard@example.com	$2b$12$/BxTvPnfpgzES6cw0Otsr.jwpY1RXlvuv2QVCguyn.mnVcjfiXi2O	Dashboard User	t	2026-05-07 06:36:05.089586+00	\N	\N	customer
15	dashboard2@example.com	$2b$12$Djr.wrZTHySk9ntUTzjvTubwi1qQWROlo9Ygzb7sW2OU2Vd9n3AFa	Dashboard User 2	t	2026-05-07 06:45:26.497043+00	\N	\N	customer
16	dashboard3@example.com	$2b$12$q5A3D78yjBmQzQIArLPnHOoM3HnNwOpmyKaeaDm538suFJ7rTOeRK	Dashboard User 3	t	2026-05-07 06:46:10.211843+00	\N	\N	customer
17	dashboard4@example.com	$2b$12$qy6Od6TLFUmaAR9kEMFx/.uTvgq.VI.k7BKgr44yDg6shgDfgvBly	Dashboard User 4	t	2026-05-07 06:46:43.552771+00	\N	\N	customer
18	dashboard5@example.com	$2b$12$2oyzkMunBTfHxLCiUBA4gePV/VoELIWm7TduLUto8Of3UdeMBzy/m	Dashboard User 5	t	2026-05-07 06:47:32.398909+00	\N	\N	customer
\.


--
-- Name: bookings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.bookings_id_seq', 54, true);


--
-- Name: buses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.buses_id_seq', 7, true);


--
-- Name: routes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.routes_id_seq', 8, true);


--
-- Name: seats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.seats_id_seq', 193, true);


--
-- Name: trips_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.trips_id_seq', 31, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 18, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: booking_seats booking_seats_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.booking_seats
    ADD CONSTRAINT booking_seats_pkey PRIMARY KEY (booking_id, seat_id);


--
-- Name: bookings bookings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_pkey PRIMARY KEY (id);


--
-- Name: buses buses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.buses
    ADD CONSTRAINT buses_pkey PRIMARY KEY (id);


--
-- Name: routes routes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.routes
    ADD CONSTRAINT routes_pkey PRIMARY KEY (id);


--
-- Name: seats seats_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seats
    ADD CONSTRAINT seats_pkey PRIMARY KEY (id);


--
-- Name: trips trips_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT trips_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_booking_seats_booking_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_booking_seats_booking_id ON public.booking_seats USING btree (booking_id);


--
-- Name: ix_booking_seats_seat_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_booking_seats_seat_id ON public.booking_seats USING btree (seat_id);


--
-- Name: ix_bookings_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_bookings_id ON public.bookings USING btree (id);


--
-- Name: ix_buses_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_buses_id ON public.buses USING btree (id);


--
-- Name: ix_routes_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_routes_id ON public.routes USING btree (id);


--
-- Name: ix_seats_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_seats_id ON public.seats USING btree (id);


--
-- Name: ix_trips_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_trips_id ON public.trips USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: booking_seats booking_seats_booking_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.booking_seats
    ADD CONSTRAINT booking_seats_booking_id_fkey FOREIGN KEY (booking_id) REFERENCES public.bookings(id) ON DELETE CASCADE;


--
-- Name: booking_seats booking_seats_seat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.booking_seats
    ADD CONSTRAINT booking_seats_seat_id_fkey FOREIGN KEY (seat_id) REFERENCES public.seats(id) ON DELETE CASCADE;


--
-- Name: bookings bookings_seat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_seat_id_fkey FOREIGN KEY (seat_id) REFERENCES public.seats(id);


--
-- Name: bookings bookings_trip_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_trip_id_fkey FOREIGN KEY (trip_id) REFERENCES public.trips(id);


--
-- Name: bookings bookings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: seats seats_bus_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seats
    ADD CONSTRAINT seats_bus_id_fkey FOREIGN KEY (bus_id) REFERENCES public.buses(id);


--
-- Name: trips trips_bus_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT trips_bus_id_fkey FOREIGN KEY (bus_id) REFERENCES public.buses(id);


--
-- Name: trips trips_route_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT trips_route_id_fkey FOREIGN KEY (route_id) REFERENCES public.routes(id);


--
-- PostgreSQL database dump complete
--

\unrestrict nEjWGOqnWJiD5P27CA3JC1Drxee5ShNWsE78Wv0Gw412uKUfEw8hAfWXlED2h0K

