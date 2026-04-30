"""SQL модели для создания таблиц"""

CREATE_COMPANIES_TABLE = """
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    website_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_SOURCES_TABLE = """
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER,
    source_type TEXT CHECK(source_type IN ('html', 'rss', 'career', 'news', 'official')),
    url TEXT NOT NULL,
    name TEXT,
    is_active BOOLEAN DEFAULT 1,
    last_checked TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
)
"""

CREATE_RAW_DOCS_TABLE = """
CREATE TABLE IF NOT EXISTS raw_docs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    raw_content TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    http_status INTEGER,
    error_message TEXT,
    FOREIGN KEY (source_id) REFERENCES sources(id)
)
"""

CREATE_CLEAN_DOCS_TABLE = """
CREATE TABLE IF NOT EXISTS clean_docs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_doc_id INTEGER UNIQUE,
    clean_content TEXT NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_hash TEXT,
    FOREIGN KEY (raw_doc_id) REFERENCES raw_docs(id)
)
"""

CREATE_FACTS_TABLE = """
CREATE TABLE IF NOT EXISTS facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clean_doc_id INTEGER,
    fact_type TEXT CHECK(fact_type IN ('vacancy', 'price', 'release')),
    fact_json TEXT,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (clean_doc_id) REFERENCES clean_docs(id)
)
"""

CREATE_ALERTS_TABLE = """
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    alert_type TEXT CHECK(alert_type IN ('connection_error', 'parse_error', 'timeout', 'http_error', 'duplicate')),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_resolved BOOLEAN DEFAULT 0,
    FOREIGN KEY (source_id) REFERENCES sources(id)
)
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_raw_docs_fetched ON raw_docs(fetched_at)",
    "CREATE INDEX IF NOT EXISTS idx_raw_docs_source ON raw_docs(source_id)",
    "CREATE INDEX IF NOT EXISTS idx_clean_docs_hash ON clean_docs(content_hash)",
    "CREATE INDEX IF NOT EXISTS idx_facts_type ON facts(fact_type)",
    "CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_sources_type ON sources(source_type)",
    "CREATE INDEX IF NOT EXISTS idx_sources_active ON sources(is_active)"
]