CREATE TABLE IF NOT EXISTS city (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    state TEXT NOT NULL,
    population BIGINT NOT NULL CHECK (population >= 0),
    year INTEGER NOT NULL,
    source TEXT NOT NULL,
    UNIQUE (name, state, year)
);
CREATE TABLE IF NOT EXISTS employment (
    id SERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES city(id),
    industry TEXT NOT NULL,
    occupation TEXT NOT NULL,
    employment_count INTEGER NOT NULL CHECK (employment_count >= 0),
    year INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS salary (
    id SERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES city(id),
    occupation TEXT NOT NULL,
    median_salary NUMERIC(12,2) NOT NULL CHECK (median_salary >= 0),
    mean_salary NUMERIC(12,2) NOT NULL CHECK (mean_salary >= 0),
    year INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS education (
    id SERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES city(id),
    education_level TEXT NOT NULL,
    population INTEGER NOT NULL CHECK (population >= 0),
    year INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS economic_indicator (
    id SERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES city(id),
    indicator TEXT NOT NULL,
    value NUMERIC(14,4) NOT NULL,
    year INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS dataset_metadata (
    id SERIAL PRIMARY KEY,
    dataset_name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    source TEXT NOT NULL,
    update_frequency TEXT
);
CREATE TABLE IF NOT EXISTS column_metadata (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL REFERENCES dataset_metadata(id),
    column_name TEXT NOT NULL,
    business_name TEXT NOT NULL,
    description TEXT NOT NULL,
    data_type TEXT NOT NULL,
    semantic_type TEXT NOT NULL,
    UNIQUE(dataset_id, column_name)
);
INSERT INTO dataset_metadata(dataset_name,description,source,update_frequency) VALUES
('city','Annual resident population estimates for incorporated U.S. places.','U.S. Census Bureau Vintage 2025','annual'),
('employment','Employment by occupation and industry.','U.S. Bureau of Labor Statistics OEWS','annual'),
('salary','Occupation wage statistics.','U.S. Bureau of Labor Statistics OEWS','annual'),
('education','Education attainment indicators.','U.S. Census Bureau ACS','annual'),
('economic_indicator','Selected economic indicators.','U.S. Census Bureau / BLS','annual')
ON CONFLICT(dataset_name) DO UPDATE SET source=EXCLUDED.source;
