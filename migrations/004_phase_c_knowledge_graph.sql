-- Phase C: Knowledge Graph with Graph Neural Network
-- Implements entity extraction, relationship modeling, and graph-based reasoning

-- Knowledge Graph Entities: Core nodes in the knowledge graph
CREATE TABLE IF NOT EXISTS kg_entities (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Entity identification
    entity_type text NOT NULL, -- 'person', 'organization', 'concept', 'tool', 'agent', 'task', 'document'
    name text NOT NULL,
    canonical_name text, -- Normalized form for deduplication

    -- Entity properties
    properties jsonb DEFAULT '{}'::jsonb,
    aliases text[] DEFAULT '{}',

    -- Source tracking
    source_memories uuid[], -- References to memory_episodic or memory_semantic
    source_sessions uuid[], -- Sessions where this entity was mentioned
    extraction_confidence numeric(5,2) DEFAULT 0.7,

    -- Graph metrics
    centrality_score numeric(10,6) DEFAULT 0.0, -- PageRank-style importance
    degree_in integer DEFAULT 0, -- Incoming edges
    degree_out integer DEFAULT 0, -- Outgoing edges
    clustering_coefficient numeric(5,4) DEFAULT 0.0,

    -- Temporal tracking
    first_seen timestamptz NOT NULL DEFAULT now(),
    last_seen timestamptz NOT NULL DEFAULT now(),
    access_count integer DEFAULT 0,

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kg_entities_type ON kg_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_kg_entities_name ON kg_entities(name);
CREATE INDEX IF NOT EXISTS idx_kg_entities_canonical ON kg_entities(canonical_name);
CREATE INDEX IF NOT EXISTS idx_kg_entities_centrality ON kg_entities(centrality_score DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_kg_entities_unique ON kg_entities(entity_type, canonical_name);

-- Knowledge Graph Relationships: Edges connecting entities
CREATE TABLE IF NOT EXISTS kg_relationships (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relationship endpoints
    source_entity_id uuid NOT NULL REFERENCES kg_entities(id) ON DELETE CASCADE,
    target_entity_id uuid NOT NULL REFERENCES kg_entities(id) ON DELETE CASCADE,

    -- Relationship type and properties
    relationship_type text NOT NULL, -- 'uses', 'manages', 'created_by', 'related_to', 'depends_on', etc.
    properties jsonb DEFAULT '{}'::jsonb,

    -- Evidence tracking
    evidence_memories uuid[], -- Supporting evidence from memory system
    confidence_score numeric(5,2) DEFAULT 0.7,
    strength numeric(5,2) DEFAULT 0.5, -- Relationship strength (0.0 to 1.0)

    -- Temporal information
    first_observed timestamptz NOT NULL DEFAULT now(),
    last_observed timestamptz NOT NULL DEFAULT now(),
    observation_count integer DEFAULT 1,

    -- Graph properties
    bidirectional boolean DEFAULT false,
    transitive boolean DEFAULT false,

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kg_rel_source ON kg_relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_kg_rel_target ON kg_relationships(target_entity_id);
CREATE INDEX IF NOT EXISTS idx_kg_rel_type ON kg_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_kg_rel_strength ON kg_relationships(strength DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_kg_rel_unique ON kg_relationships(source_entity_id, target_entity_id, relationship_type);

-- GNN Node Features: Neural network features for each entity
CREATE TABLE IF NOT EXISTS kg_gnn_node_features (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id uuid NOT NULL REFERENCES kg_entities(id) ON DELETE CASCADE,

    -- Feature vectors
    structural_features vector(128), -- Graph structure features (degree, centrality, etc.)
    semantic_features vector(768), -- Semantic embeddings from LLM
    temporal_features vector(32), -- Temporal patterns (access frequency, recency, etc.)
    combined_features vector(928), -- Concatenated feature vector

    -- Feature metadata
    features_version integer DEFAULT 1,
    last_computed timestamptz NOT NULL DEFAULT now(),

    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_gnn_features_entity ON kg_gnn_node_features(entity_id);
CREATE INDEX IF NOT EXISTS idx_gnn_features_combined ON kg_gnn_node_features
    USING ivfflat (combined_features vector_cosine_ops) WITH (lists = 100);

-- GNN Edge Features: Neural network features for relationships
CREATE TABLE IF NOT EXISTS kg_gnn_edge_features (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    relationship_id uuid NOT NULL REFERENCES kg_relationships(id) ON DELETE CASCADE,

    -- Feature vectors
    relationship_embedding vector(256), -- Learned edge representation
    context_features vector(128), -- Contextual features from surrounding nodes

    -- Feature metadata
    features_version integer DEFAULT 1,
    last_computed timestamptz NOT NULL DEFAULT now(),

    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_gnn_edge_features_rel ON kg_gnn_edge_features(relationship_id);

-- Graph Queries: Stores complex graph query patterns and results
CREATE TABLE IF NOT EXISTS kg_queries (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Query details
    query_type text NOT NULL, -- 'path_finding', 'community_detection', 'link_prediction', 'subgraph_matching'
    query_pattern jsonb NOT NULL, -- Query structure/parameters
    query_cypher text, -- Cypher-like query (for documentation)

    -- Execution tracking
    session_id uuid REFERENCES sessions(id) ON DELETE SET NULL,
    agent_id text REFERENCES agents(agent_id) ON DELETE SET NULL,

    -- Results
    result_entities uuid[], -- Entity IDs in result
    result_relationships uuid[], -- Relationship IDs in result
    result_graph jsonb, -- Full graph structure
    confidence_score numeric(5,2),

    -- Performance metrics
    execution_time_ms numeric(10,2),
    nodes_traversed integer,
    edges_traversed integer,

    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kg_queries_type ON kg_queries(query_type);
CREATE INDEX IF NOT EXISTS idx_kg_queries_session ON kg_queries(session_id);

-- Graph Communities: Detected clusters/communities in the knowledge graph
CREATE TABLE IF NOT EXISTS kg_communities (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Community identification
    community_id text NOT NULL,
    algorithm text NOT NULL, -- 'louvain', 'label_propagation', 'girvan_newman'

    -- Community members
    member_entities uuid[], -- Entity IDs in this community
    member_count integer,

    -- Community properties
    modularity numeric(5,4), -- Quality metric for community detection
    density numeric(5,4), -- Edge density within community
    cohesion_score numeric(5,2),

    -- Semantic characterization
    topic text, -- Auto-detected topic/theme
    keywords text[],
    representative_entities uuid[], -- Most central entities

    -- Temporal tracking
    detection_date timestamptz NOT NULL DEFAULT now(),
    stability_score numeric(5,2) DEFAULT 0.5, -- How stable over time

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kg_communities_id ON kg_communities(community_id);
CREATE INDEX IF NOT EXISTS idx_kg_communities_modularity ON kg_communities(modularity DESC);

-- Graph Evolution Log: Tracks changes to the knowledge graph over time
CREATE TABLE IF NOT EXISTS kg_evolution_log (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Change details
    change_type text NOT NULL, -- 'entity_added', 'entity_updated', 'entity_merged', 'relationship_added', etc.
    entity_id uuid REFERENCES kg_entities(id) ON DELETE SET NULL,
    relationship_id uuid REFERENCES kg_relationships(id) ON DELETE SET NULL,

    -- Change metadata
    change_data jsonb,
    reason text,
    triggered_by text, -- 'user', 'agent', 'consolidation', 'inference'

    -- Source tracking
    session_id uuid REFERENCES sessions(id) ON DELETE SET NULL,
    agent_id text REFERENCES agents(agent_id) ON DELETE SET NULL,

    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kg_evolution_type ON kg_evolution_log(change_type);
CREATE INDEX IF NOT EXISTS idx_kg_evolution_time ON kg_evolution_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_kg_evolution_entity ON kg_evolution_log(entity_id);

-- Link Prediction Tasks: GNN-based predictions for missing relationships
CREATE TABLE IF NOT EXISTS kg_link_predictions (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Prediction endpoints
    source_entity_id uuid NOT NULL REFERENCES kg_entities(id) ON DELETE CASCADE,
    target_entity_id uuid NOT NULL REFERENCES kg_entities(id) ON DELETE CASCADE,

    -- Prediction
    predicted_relationship_type text NOT NULL,
    prediction_confidence numeric(5,2),
    prediction_score numeric(10,6), -- Raw GNN output score

    -- Model information
    model_version text,
    features_used jsonb,

    -- Validation
    validated boolean DEFAULT false,
    validation_result text, -- 'correct', 'incorrect', 'uncertain'
    actual_relationship_id uuid REFERENCES kg_relationships(id) ON DELETE SET NULL,

    created_at timestamptz NOT NULL DEFAULT now(),
    validated_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_kg_predictions_source ON kg_link_predictions(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_kg_predictions_confidence ON kg_link_predictions(prediction_confidence DESC);
CREATE INDEX IF NOT EXISTS idx_kg_predictions_unvalidated ON kg_link_predictions(validated) WHERE NOT validated;

-- Entity Embeddings: Semantic vector representations for similarity search
CREATE TABLE IF NOT EXISTS kg_entity_embeddings (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id uuid NOT NULL REFERENCES kg_entities(id) ON DELETE CASCADE,

    -- Embedding vectors
    name_embedding vector(1536), -- Embedding of entity name
    context_embedding vector(1536), -- Embedding of entity context/properties
    graph_embedding vector(256), -- Graph structure-based embedding (Node2Vec, GraphSAGE)

    -- Metadata
    embedding_model text,
    last_updated timestamptz NOT NULL DEFAULT now(),

    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kg_embeddings_entity ON kg_entity_embeddings(entity_id);
CREATE INDEX IF NOT EXISTS idx_kg_embeddings_context ON kg_entity_embeddings
    USING ivfflat (context_embedding vector_cosine_ops) WITH (lists = 100);

-- Create materialized view for graph statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS kg_graph_stats AS
SELECT
    (SELECT COUNT(*) FROM kg_entities) as total_entities,
    (SELECT COUNT(*) FROM kg_relationships) as total_relationships,
    (SELECT COUNT(DISTINCT entity_type) FROM kg_entities) as entity_types_count,
    (SELECT COUNT(DISTINCT relationship_type) FROM kg_relationships) as relationship_types_count,
    (SELECT AVG(degree_in + degree_out) FROM kg_entities) as avg_degree,
    (SELECT MAX(centrality_score) FROM kg_entities) as max_centrality,
    (SELECT COUNT(*) FROM kg_communities) as communities_count,
    now() as last_updated;

CREATE UNIQUE INDEX IF NOT EXISTS idx_kg_stats_singleton ON kg_graph_stats((1));

COMMENT ON TABLE kg_entities IS 'Knowledge graph entities: core nodes representing concepts, agents, tasks, etc.';
COMMENT ON TABLE kg_relationships IS 'Knowledge graph edges: typed relationships between entities';
COMMENT ON TABLE kg_gnn_node_features IS 'GNN node feature vectors for graph neural network reasoning';
COMMENT ON TABLE kg_gnn_edge_features IS 'GNN edge feature vectors for relationship modeling';
COMMENT ON TABLE kg_communities IS 'Detected communities/clusters in the knowledge graph';
COMMENT ON TABLE kg_link_predictions IS 'GNN-based predictions for missing or future relationships';
