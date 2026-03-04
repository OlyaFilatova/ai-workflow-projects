-- PostgreSQL database dump
CREATE TABLE public.events (
    id integer,
    payload text,
    active boolean,
    created_at timestamp without time zone
);

COPY public.events (id, payload, active, created_at) FROM stdin;
1	alpha	true	2024-01-01 00:00:00
2	beta	false	2024-01-02 00:00:00
3	\\N	true	2024-01-03 00:00:00
\.

CREATE VIEW public.v_events AS SELECT id FROM public.events;
