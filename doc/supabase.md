-- Enable the pgvector extension to work with embedding vectors
create extension vector;

-- Create a table to store your documents
create table documents (
  id text primary key,
  content text UNIQUE, -- corresponds to Document.pageContent
  metadata jsonb, -- corresponds to Document.metadata
  embedding vector(768) -- 1536 works for OpenAI embeddings, change if needed
);

-- Create a function to do queries
CREATE FUNCTION match_documents(query_embedding vector(768), match_count int)
    RETURNS TABLE(
        id text,
        content text,
        metadata jsonb,
        -- we return matched vectors to enable maximal marginal relevance searches
        embedding vector(768),
        similarity float)
    LANGUAGE plpgsql
    AS $$
    # variable_conflict use_column
BEGIN
    RETURN query
    SELECT
        id,
        content,
        metadata,
        embedding,
        1 -(documents.embedding <=> query_embedding) AS similarity
    FROM
        documents
    ORDER BY
        documents.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
