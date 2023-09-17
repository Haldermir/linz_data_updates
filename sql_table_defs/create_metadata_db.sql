-- Generate Metadata Database
-- Author: Gareth Palmer
-- 
-- Description:
--  Creates the database and associated tables needed for processing updates to LINZ
--  data tables using python and postgres database.

create DATABASE metadata;
alter DATABASE metadata owner to postgres;

use metadata;

CREATE TABLE public.api_keys (
    api_id integer NOT NULL,
    source_id integer,
    api_key character varying(32),
    key_desc character varying(350)
);


ALTER TABLE public.api_keys OWNER TO postgres;


CREATE SEQUENCE public.api_keys_api_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.api_keys_api_id_seq OWNER TO postgres;


ALTER SEQUENCE public.api_keys_api_id_seq OWNED BY public.api_keys.api_id;


--
-- TOC entry 213 (class 1259 OID 3746040)
-- Name: calc_lines; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.calc_lines (
    id integer NOT NULL,
    dataset_id integer,
    feature_count integer,
    append_count integer,
    update_count integer,
    delete_count integer,
    feature_length double precision,
    append_length double precision,
    update_length double precision,
    delete_length double precision,
    process_id integer
);


ALTER TABLE public.calc_lines OWNER TO postgres;


CREATE SEQUENCE public.calc_lines_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.calc_lines_id_seq OWNER TO postgres;


ALTER SEQUENCE public.calc_lines_id_seq OWNED BY public.calc_lines.id;



CREATE TABLE public.calc_points (
    id integer NOT NULL,
    dataset_id integer,
    feature_count integer,
    append_count integer,
    update_count integer,
    delete_count integer,
    process_id integer
);


ALTER TABLE public.calc_points OWNER TO postgres;


CREATE SEQUENCE public.calc_points_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.calc_points_id_seq OWNER TO postgres;


ALTER SEQUENCE public.calc_points_id_seq OWNED BY public.calc_points.id;



CREATE TABLE public.calc_polygons (
    id integer NOT NULL,
    dataset_id integer,
    feature_count integer,
    append_count integer,
    update_count integer,
    delete_count integer,
    feature_area double precision,
    append_area double precision,
    update_area double precision,
    delete_area double precision,
    process_id integer
);


ALTER TABLE public.calc_polygons OWNER TO postgres;


CREATE TABLE public.dataset_updates (
    process_id integer NOT NULL,
    start_time timestamp without time zone,
    end_time timestamp without time zone,
    dataset_id integer,
    success boolean,
    adds integer,
    deletes integer,
    updates integer
);


ALTER TABLE public.dataset_updates OWNER TO postgres;


CREATE SEQUENCE public.dataset_updates_process_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dataset_updates_process_id_seq OWNER TO postgres;


ALTER SEQUENCE public.dataset_updates_process_id_seq OWNED BY public.dataset_updates.process_id;


CREATE TABLE public.datasets (
    dataset_id integer NOT NULL,
    source_id integer,
    relation_type character varying(5),
    item_no integer,
    source_name character varying(150),
    db_name character varying(150),
    id_field character varying(50)
);


ALTER TABLE public.datasets OWNER TO postgres;


CREATE SEQUENCE public.datasets_dataset_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.datasets_dataset_id_seq OWNER TO postgres;


ALTER SEQUENCE public.datasets_dataset_id_seq OWNED BY public.datasets.dataset_id;


CREATE SEQUENCE public.polygon_calcs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.polygon_calcs_id_seq OWNER TO postgres;


ALTER SEQUENCE public.polygon_calcs_id_seq OWNED BY public.calc_polygons.id;


CREATE TABLE public.sources (
    id integer NOT NULL,
    name character varying(100),
    url character varying(350),
    pattern character varying(50)
);


ALTER TABLE public.sources OWNER TO postgres;


CREATE SEQUENCE public.sources_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sources_id_seq OWNER TO postgres;


ALTER SEQUENCE public.sources_id_seq OWNED BY public.sources.id;


ALTER TABLE ONLY public.api_keys ALTER COLUMN api_id SET DEFAULT nextval('public.api_keys_api_id_seq'::regclass);


ALTER TABLE ONLY public.calc_lines ALTER COLUMN id SET DEFAULT nextval('public.calc_lines_id_seq'::regclass);


ALTER TABLE ONLY public.calc_points ALTER COLUMN id SET DEFAULT nextval('public.calc_points_id_seq'::regclass);


ALTER TABLE ONLY public.calc_polygons ALTER COLUMN id SET DEFAULT nextval('public.polygon_calcs_id_seq'::regclass);


ALTER TABLE ONLY public.dataset_updates ALTER COLUMN process_id SET DEFAULT nextval('public.dataset_updates_process_id_seq'::regclass);


ALTER TABLE ONLY public.datasets ALTER COLUMN dataset_id SET DEFAULT nextval('public.datasets_dataset_id_seq'::regclass);


ALTER TABLE ONLY public.sources ALTER COLUMN id SET DEFAULT nextval('public.sources_id_seq'::regclass);


SELECT pg_catalog.setval('public.api_keys_api_id_seq', 4, true);


SELECT pg_catalog.setval('public.calc_lines_id_seq', 1, false);


SELECT pg_catalog.setval('public.calc_points_id_seq', 1, false);


SELECT pg_catalog.setval('public.dataset_updates_process_id_seq', 1, false);


SELECT pg_catalog.setval('public.datasets_dataset_id_seq', 201, true);


SELECT pg_catalog.setval('public.polygon_calcs_id_seq', 1, false);


SELECT pg_catalog.setval('public.sources_id_seq', 7, true);


ALTER TABLE ONLY public.dataset_updates
    ADD CONSTRAINT dataset_updates_pkey PRIMARY KEY (process_id);


ALTER TABLE ONLY public.datasets
    ADD CONSTRAINT datasets_pkey PRIMARY KEY (dataset_id);


ALTER TABLE ONLY public.sources
    ADD CONSTRAINT sources_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_fk FOREIGN KEY (source_id) REFERENCES public.sources(id) ON UPDATE CASCADE;


ALTER TABLE ONLY public.calc_lines
    ADD CONSTRAINT calc_lines_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES public.datasets(dataset_id);


ALTER TABLE ONLY public.calc_lines
    ADD CONSTRAINT calc_lines_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.dataset_updates(process_id);


ALTER TABLE ONLY public.calc_points
    ADD CONSTRAINT calc_points_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES public.datasets(dataset_id);


ALTER TABLE ONLY public.calc_points
    ADD CONSTRAINT calc_points_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.dataset_updates(process_id);


ALTER TABLE ONLY public.dataset_updates
    ADD CONSTRAINT dataset_updates_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES public.datasets(dataset_id) NOT VALID;


ALTER TABLE ONLY public.datasets
    ADD CONSTRAINT datasets_source_id_fkey FOREIGN KEY (source_id) REFERENCES public.sources(id) NOT VALID;


ALTER TABLE ONLY public.calc_polygons
    ADD CONSTRAINT polygon_calcs_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES public.datasets(dataset_id);


ALTER TABLE ONLY public.calc_polygons
    ADD CONSTRAINT polygon_calcs_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.dataset_updates(process_id);

