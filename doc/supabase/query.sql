-- Query the number of vectors
select count(*) from documents;

-- Query number of vectors by day
-- TODO: add sundays
select
    count(*) as counted_vector,
    metadata->>'fecha_publicacion' as date
from documents
group by date
order by date

-- Query max(day)
select max(metadata->>'fecha_publicacion') as date from documents;

-- Query min(day)
select min(metadata->>'fecha_publicacion') as date from documents;

-- Query metadata by identificador
SELECT count(*) FROM documents WHERE metadata @> '{"identificador": "BOE-A-2023-38"}';

-- Query metadata by fecha_publicacion
SELECT count(*) FROM documents WHERE metadata @> '{"fecha_publicacion": "2023-01-01"}';

-- TODO: Query to detect the duplicated (text/embeddings)


-- metadata: https://medium.com/hackernoon/how-to-query-jsonb-beginner-sheet-cheat-4da3aa5082a3
