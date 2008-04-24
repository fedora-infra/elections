--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS 'Standard public schema';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: candidates; Type: TABLE; Schema: public; Owner: njones; Tablespace: 
--

CREATE TABLE candidates (
    id integer NOT NULL,
    election_id integer NOT NULL,
    name text NOT NULL,
    url text NOT NULL
);


ALTER TABLE public.candidates OWNER TO njones;

--
-- Name: candidates_id_seq; Type: SEQUENCE; Schema: public; Owner: njones
--

CREATE SEQUENCE candidates_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.candidates_id_seq OWNER TO njones;

--
-- Name: candidates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: njones
--

ALTER SEQUENCE candidates_id_seq OWNED BY candidates.id;


--
-- Name: candidates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: njones
--

SELECT pg_catalog.setval('candidates_id_seq', 5, true);


--
-- Name: elections; Type: TABLE; Schema: public; Owner: njones; Tablespace: 
--

CREATE TABLE elections (
    id integer NOT NULL,
    name text NOT NULL,
    info text NOT NULL,
    url text NOT NULL,
    start_date timestamp without time zone NOT NULL,
    end_date timestamp without time zone NOT NULL,
    max_seats integer NOT NULL,
    votes_per_user integer NOT NULL,
    public_results integer NOT NULL
);


ALTER TABLE public.elections OWNER TO njones;

--
-- Name: elections_id_seq; Type: SEQUENCE; Schema: public; Owner: njones
--

CREATE SEQUENCE elections_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.elections_id_seq OWNER TO njones;

--
-- Name: elections_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: njones
--

ALTER SEQUENCE elections_id_seq OWNED BY elections.id;


--
-- Name: elections_id_seq; Type: SEQUENCE SET; Schema: public; Owner: njones
--

SELECT pg_catalog.setval('elections_id_seq', 2, true);


--
-- Name: legalvoters; Type: TABLE; Schema: public; Owner: njones; Tablespace: 
--

CREATE TABLE legalvoters (
    election_id integer NOT NULL,
    group_name text NOT NULL
);


ALTER TABLE public.legalvoters OWNER TO njones;

--
-- Name: votes; Type: TABLE; Schema: public; Owner: njones; Tablespace: 
--

CREATE TABLE votes (
    voter text NOT NULL,
    candidate_id integer NOT NULL
);


ALTER TABLE public.votes OWNER TO njones;

--
-- Name: id; Type: DEFAULT; Schema: public; Owner: njones
--

ALTER TABLE candidates ALTER COLUMN id SET DEFAULT nextval('candidates_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: njones
--

ALTER TABLE elections ALTER COLUMN id SET DEFAULT nextval('elections_id_seq'::regclass);


--
-- Data for Name: candidates; Type: TABLE DATA; Schema: public; Owner: njones
--

COPY candidates (id, election_id, name, url) FROM stdin;
1	1	Nigel	http://nigelj.com
2	1	Pooh Bear	about:blank
3	2	Zod	http://fedoraproject.org
4	2	Moonshine	http://yahoo.com
5	2	Warewolf	http://google.com
\.


--
-- Data for Name: elections; Type: TABLE DATA; Schema: public; Owner: njones
--

COPY elections (id, name, info, url, start_date, end_date, max_seats, votes_per_user, public_results) FROM stdin;
1	Nigel for President	The free world needs you!	foobar	2008-04-23 04:00:00	2008-04-25 04:00:00	1	1	0
2	Fedora Release Name	Choose a name or else!	foobar	2008-04-24 00:00:00	2008-04-30 00:00:00	1	1	0
\.


--
-- Data for Name: legalvoters; Type: TABLE DATA; Schema: public; Owner: njones
--

COPY legalvoters (election_id, group_name) FROM stdin;
1	anyone
2	cvsextras
\.


--
-- Data for Name: votes; Type: TABLE DATA; Schema: public; Owner: njones
--

COPY votes (voter, candidate_id) FROM stdin;
me	2
\.


--
-- Name: candidates_id_key; Type: CONSTRAINT; Schema: public; Owner: njones; Tablespace: 
--

ALTER TABLE ONLY candidates
    ADD CONSTRAINT candidates_id_key UNIQUE (id);


--
-- Name: candidates_pkey; Type: CONSTRAINT; Schema: public; Owner: njones; Tablespace: 
--

ALTER TABLE ONLY candidates
    ADD CONSTRAINT candidates_pkey PRIMARY KEY (id, election_id);


--
-- Name: elections_pkey; Type: CONSTRAINT; Schema: public; Owner: njones; Tablespace: 
--

ALTER TABLE ONLY elections
    ADD CONSTRAINT elections_pkey PRIMARY KEY (id);


--
-- Name: legalvoters_pkey; Type: CONSTRAINT; Schema: public; Owner: njones; Tablespace: 
--

ALTER TABLE ONLY legalvoters
    ADD CONSTRAINT legalvoters_pkey PRIMARY KEY (election_id);


--
-- Name: votes_pkey; Type: CONSTRAINT; Schema: public; Owner: njones; Tablespace: 
--

ALTER TABLE ONLY votes
    ADD CONSTRAINT votes_pkey PRIMARY KEY (candidate_id);


--
-- Name: candidates_election_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: njones
--

ALTER TABLE ONLY candidates
    ADD CONSTRAINT candidates_election_id_fkey FOREIGN KEY (election_id) REFERENCES elections(id);


--
-- Name: legalvoters_election_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: njones
--

ALTER TABLE ONLY legalvoters
    ADD CONSTRAINT legalvoters_election_id_fkey FOREIGN KEY (election_id) REFERENCES elections(id);


--
-- Name: votes_candidate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: njones
--

ALTER TABLE ONLY votes
    ADD CONSTRAINT votes_candidate_id_fkey FOREIGN KEY (candidate_id) REFERENCES candidates(id);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

