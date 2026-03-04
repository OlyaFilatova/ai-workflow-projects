CREATE TABLE public.logs (
  id integer,
  payload text,
  note text
);

COPY public.logs (id, payload, note) FROM stdin;
1	line\\t1	first\\nrow
2	\\N	second
\.
