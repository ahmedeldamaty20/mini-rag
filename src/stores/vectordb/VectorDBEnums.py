from enum import Enum

class VectorDBEnums(Enum):
    QDRANT = "QDRANT"
    PGVECTOR = "PGVECTOR"

class DistanceMetodEnums(Enum):
    COSINE = "Cosine"
    DOT = "Dot"
    EUCLIDEAN = "Euclidean"

class PgVectorTableSchemaEnums(Enum):
    ID = "id"
    TEXT = "text"
    VECTOR = "vector"
    CHUNK_ID = "chunk_id"
    METADATA = "metadata"
    _PREFIX = "pgvector_"

class PgVectorDistanceMethodEnums(Enum):
    COSINE = "vector_cosine_ops"
    DOT = "vector_ip_ops"
    EUCLIDEAN = "vector_l2_ops"

class PgVectorQueryOperatorEnums(Enum):
    COSINE = "<=>"
    DOT = "<#>"
    EUCLIDEAN = "<->"

class PgVectorIndexTypeEnums(Enum):
    HNSW = "hnsw"
    IVFFLAT = "ivfflat"
