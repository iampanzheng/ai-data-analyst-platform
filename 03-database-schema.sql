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
ON CONFLICT(dataset_name) DO UPDATE SET
    description=EXCLUDED.description,
    source=EXCLUDED.source,
    update_frequency=EXCLUDED.update_frequency;

WITH metadata(dataset_name, column_name, business_name, description, data_type, semantic_type) AS (
    VALUES
    ('city','id','City ID','Stable internal identifier for a city record.','integer','identifier'),
    ('city','name','City Name','Name of the incorporated place.','text','geography_name'),
    ('city','state','State','Two-letter U.S. state abbreviation.','text','geography_code'),
    ('city','population','Population','Estimated resident population.','bigint','measure'),
    ('city','year','Year','Reference year for the population estimate.','integer','time'),
    ('city','source','Source','Source label for the population dataset.','text','provenance'),
    ('employment','id','Employment Record ID','Stable internal identifier for an employment record.','integer','identifier'),
    ('employment','city_id','City ID','Foreign key to city.','integer','foreign_key'),
    ('employment','industry','Industry','Industry classification.','text','category'),
    ('employment','occupation','Occupation','Occupation classification.','text','category'),
    ('employment','employment_count','Employment Count','Number of employed workers represented by the record.','integer','measure'),
    ('employment','year','Year','Reference year for employment.','integer','time'),
    ('salary','id','Salary Record ID','Stable internal identifier for a salary record.','integer','identifier'),
    ('salary','city_id','City ID','Foreign key to city.','integer','foreign_key'),
    ('salary','occupation','Occupation','Occupation classification for wage statistics.','text','category'),
    ('salary','median_salary','Median Salary','Median annual salary for the occupation.','numeric','measure'),
    ('salary','mean_salary','Mean Salary','Mean annual salary for the occupation.','numeric','measure'),
    ('salary','year','Year','Reference year for wage statistics.','integer','time'),
    ('education','id','Education Record ID','Stable internal identifier for an education record.','integer','identifier'),
    ('education','city_id','City ID','Foreign key to city.','integer','foreign_key'),
    ('education','education_level','Education Level','Education attainment category.','text','category'),
    ('education','population','Population','Population represented by the education attainment record.','integer','measure'),
    ('education','year','Year','Reference year for the education measure.','integer','time'),
    ('economic_indicator','id','Economic Indicator ID','Stable internal identifier for an economic indicator record.','integer','identifier'),
    ('economic_indicator','city_id','City ID','Foreign key to city.','integer','foreign_key'),
    ('economic_indicator','indicator','Indicator','Name of the economic indicator.','text','category'),
    ('economic_indicator','value','Value','Numeric value of the economic indicator.','numeric','measure'),
    ('economic_indicator','year','Year','Reference year for the indicator.','integer','time')
)
INSERT INTO column_metadata(dataset_id,column_name,business_name,description,data_type,semantic_type)
SELECT d.id, m.column_name, m.business_name, m.description, m.data_type, m.semantic_type
FROM metadata AS m
JOIN dataset_metadata AS d ON d.dataset_name = m.dataset_name
ON CONFLICT(dataset_id,column_name) DO UPDATE SET
    business_name=EXCLUDED.business_name,
    description=EXCLUDED.description,
    data_type=EXCLUDED.data_type,
    semantic_type=EXCLUDED.semantic_type;
