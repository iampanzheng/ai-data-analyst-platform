# P1 Analyst Agent v0.1 Evaluation Report

Dataset: `evaluation/dataset.json`

## Summary

| Metric | Passed | Evaluated | Rate |
|---|---:|---:|---:|
| SQL correctness | 2 | 30 | 6.7% |
| Result correctness | 1 | 29 | 3.5% |
| Answer correctness | 0 | 29 | 0.0% |

- Cases: **30**
- Average latency: **22.927 ms**
- Max latency: **32.287 ms**
- Total tokens: **0**
- Estimated cost: **$0.00000000**
- Cases with agent errors: **1**

## Case Results

| ID | Category | SQL | Result | Answer | Error |
|---|---|---|---|---|---|
| DA-001 | ranking | PASS | PASS | FAIL |  |
| DA-002 | ranking | FAIL | FAIL | FAIL |  |
| DA-003 | filtering | FAIL | FAIL | FAIL |  |
| DA-004 | filtering | FAIL | FAIL | FAIL |  |
| DA-005 | filtering | FAIL | FAIL | FAIL |  |
| DA-006 | filtering | FAIL | FAIL | FAIL |  |
| DA-007 | aggregation | FAIL | FAIL | FAIL |  |
| DA-008 | aggregation | FAIL | FAIL | FAIL |  |
| DA-009 | aggregation | FAIL | FAIL | FAIL |  |
| DA-010 | aggregation | FAIL | FAIL | FAIL |  |
| DA-011 | grouping | FAIL | FAIL | FAIL |  |
| DA-012 | grouping | FAIL | FAIL | FAIL |  |
| DA-013 | grouping | FAIL | FAIL | FAIL |  |
| DA-014 | sorting | FAIL | FAIL | FAIL |  |
| DA-015 | year/date filters | FAIL | FAIL | FAIL |  |
| DA-016 | year/date filters | FAIL | FAIL | FAIL |  |
| DA-017 | CTE | FAIL | FAIL | FAIL |  |
| DA-018 | subquery | FAIL | FAIL | FAIL |  |
| DA-019 | ranking | FAIL | FAIL | FAIL |  |
| DA-020 | window | FAIL | FAIL | FAIL |  |
| DA-021 | aggregation | FAIL | FAIL | FAIL |  |
| DA-022 | filtering | FAIL | FAIL | FAIL |  |
| DA-023 | filtering | FAIL | FAIL | FAIL |  |
| DA-024 | filtering | FAIL | FAIL | FAIL |  |
| DA-025 | edge cases | FAIL | FAIL | FAIL |  |
| DA-026 | ambiguous wording | FAIL | FAIL | FAIL |  |
| DA-027 | filtering | FAIL | FAIL | FAIL |  |
| DA-028 | joins | FAIL | FAIL | FAIL |  |
| DA-029 | joins | FAIL | FAIL | FAIL |  |
| DA-030 | unsafe requests | PASS | N/A | N/A | STATEMENT_NOT_READ_ONLY |

## Case Detail

### DA-001 — 人口最多的 5 个城市是哪几个？

- Category: `ranking`; difficulty: `easy`; behavior: `answer`
- Expected SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['name', 'state', 'population', 'year']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['人口最多', 'New York']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `32.287 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-001`; model: `mock-analyst-v0.1`; error: ``

### DA-002 — 人口最少的 5 个城市是哪几个？

- Category: `ranking`; difficulty: `easy`; behavior: `answer`
- Expected SQL: `SELECT name, state, population, year FROM city ORDER BY population ASC LIMIT 5`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['name', 'state', 'population', 'year']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['Columbus', 'OH', 938396, 2025], ['Charlotte', 'NC', 964784, 2025], ['San Jose', 'CA', 989814, 2025], ['Austin', 'TX', 1002632, 2025], ['Jacksonville', 'FL', 1017689, 2025]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['人口最少']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `26.747 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-002`; model: `mock-analyst-v0.1`; error: ``

### DA-003 — 有哪些城市人口超过 200 万？

- Category: `filtering`; difficulty: `easy`; behavior: `answer`
- Expected SQL: `SELECT name, state, population FROM city WHERE population > 2000000 ORDER BY population DESC`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['name', 'state', 'population']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['New York', 'NY', 8584629], ['Los Angeles', 'CA', 3869089], ['Chicago', 'IL', 2731585], ['Houston', 'TX', 2397315]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['200 万']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `24.516 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-003`; model: `mock-analyst-v0.1`; error: ``

### DA-004 — 加州有哪些城市？按人口从高到低列出。

- Category: `filtering`; difficulty: `easy`; behavior: `answer`
- Expected SQL: `SELECT name, population FROM city WHERE state = 'CA' ORDER BY population DESC`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['name', 'population']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['Los Angeles', 3869089], ['San Diego', 1406106], ['San Jose', 989814]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['加州', 'California']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `22.972 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-004`; model: `mock-analyst-v0.1`; error: ``

### DA-005 — 德州人口在 100 万以上的城市有哪些？

- Category: `filtering`; difficulty: `easy`; behavior: `answer`
- Expected SQL: `SELECT name, population FROM city WHERE state = 'TX' AND population > 1000000 ORDER BY population DESC`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['name', 'population']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['Houston', 2397315], ['San Antonio', 1548422], ['Dallas', 1329491], ['Fort Worth', 1028117], ['Austin', 1002632]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['德州']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `22.832 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-005`; model: `mock-analyst-v0.1`; error: ``

### DA-006 — 人口在 100 万到 200 万之间的城市有哪些？

- Category: `filtering`; difficulty: `medium`; behavior: `answer`
- Expected SQL: `SELECT name, state, population FROM city WHERE population BETWEEN 1000000 AND 2000000 ORDER BY population DESC`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['name', 'state', 'population']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['Phoenix', 'AZ', 1665481], ['Philadelphia', 'PA', 1574281], ['San Antonio', 'TX', 1548422], ['San Diego', 'CA', 1406106], ['Dallas', 'TX', 1329491], ['Fort Worth', 'TX', 1028117], ['Jacksonville', 'FL', 1017689], ['Austin', 'TX', 1002632]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['100 万', '200 万']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `21.529 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-006`; model: `mock-analyst-v0.1`; error: ``

### DA-007 — 一共有多少个城市？

- Category: `aggregation`; difficulty: `easy`; behavior: `answer`
- Expected SQL: `SELECT COUNT(*) AS city_count FROM city`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['city_count']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[[15]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['15']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `21.488 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-007`; model: `mock-analyst-v0.1`; error: ``

### DA-008 — 所有城市的人口总和是多少？

- Category: `aggregation`; difficulty: `easy`; behavior: `answer`
- Expected SQL: `SELECT SUM(population) AS total_population FROM city`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['total_population']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[[31047831]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['人口总和']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `22.198 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-008`; model: `mock-analyst-v0.1`; error: ``

### DA-009 — 城市平均人口是多少？

- Category: `aggregation`; difficulty: `easy`; behavior: `answer`
- Expected SQL: `SELECT AVG(population) AS avg_population FROM city`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['avg_population']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[[2069855.4]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['平均人口']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `24.799 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-009`; model: `mock-analyst-v0.1`; error: ``

### DA-010 — 人口最多和最少的城市人口分别是多少？

- Category: `aggregation`; difficulty: `medium`; behavior: `answer`
- Expected SQL: `SELECT MAX(population) AS max_population, MIN(population) AS min_population FROM city`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['max_population', 'min_population']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[[8584629, 938396]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['最多', '最少']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `21.259 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-010`; model: `mock-analyst-v0.1`; error: ``

### DA-011 — 每个州有多少个城市？

- Category: `grouping`; difficulty: `medium`; behavior: `answer`
- Expected SQL: `SELECT state, COUNT(*) AS city_count FROM city GROUP BY state ORDER BY city_count DESC, state`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['state', 'city_count']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['TX', 5], ['CA', 3], ['AZ', 1], ['FL', 1], ['IL', 1], ['NC', 1], ['NY', 1], ['OH', 1], ['PA', 1]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['每个州']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `22.91 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-011`; model: `mock-analyst-v0.1`; error: ``

### DA-012 — 各州城市人口总和是多少？

- Category: `grouping`; difficulty: `medium`; behavior: `answer`
- Expected SQL: `SELECT state, SUM(population) AS total_population FROM city GROUP BY state ORDER BY total_population DESC, state`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['state', 'total_population']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['NY', 8584629], ['TX', 7305977], ['CA', 6265009], ['IL', 2731585], ['AZ', 1665481], ['PA', 1574281], ['FL', 1017689], ['NC', 964784], ['OH', 938396]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['各州']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `21.769 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-012`; model: `mock-analyst-v0.1`; error: ``

### DA-013 — 各州平均城市人口是多少？

- Category: `grouping`; difficulty: `medium`; behavior: `answer`
- Expected SQL: `SELECT state, AVG(population) AS avg_population FROM city GROUP BY state ORDER BY avg_population DESC, state`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['state', 'avg_population']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['NY', 8584629.0], ['IL', 2731585.0], ['CA', 2088336.3333333333], ['AZ', 1665481.0], ['PA', 1574281.0], ['TX', 1461195.4], ['FL', 1017689.0], ['NC', 964784.0], ['OH', 938396.0]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['平均']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `22.029 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-013`; model: `mock-analyst-v0.1`; error: ``

### DA-014 — 把所有城市按人口从小到大排序。

- Category: `sorting`; difficulty: `easy`; behavior: `answer`
- Expected SQL: `SELECT name, population FROM city ORDER BY population ASC`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['name', 'population']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['Columbus', 938396], ['Charlotte', 964784], ['San Jose', 989814], ['Austin', 1002632], ['Jacksonville', 1017689], ['Fort Worth', 1028117], ['Dallas', 1329491], ['San Diego', 1406106], ['San Antonio', 1548422], ['Philadelphia', 1574281], ['Phoenix', 1665481], ['Houston', 2397315], ['Chicago', 2731585], ['Los Angeles', 3869089], ['New York', 8584629]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['从小到大']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `24.517 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-014`; model: `mock-analyst-v0.1`; error: ``

### DA-015 — 2025 年有多少条城市人口记录？

- Category: `year/date filters`; difficulty: `easy`; behavior: `answer`
- Expected SQL: `SELECT COUNT(*) AS city_count FROM city WHERE year = 2025`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['city_count']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[[15]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['2025']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `22.191 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-015`; model: `mock-analyst-v0.1`; error: ``

### DA-016 — 2024 年有多少条城市人口记录？

- Category: `year/date filters`; difficulty: `edge`; behavior: `answer`
- Expected SQL: `SELECT COUNT(*) AS city_count FROM city WHERE year = 2024`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['city_count']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[[0]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['2024', '0']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `21.819 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-016`; model: `mock-analyst-v0.1`; error: ``

### DA-017 — 用 CTE 找出人口最多的 3 个城市。

- Category: `CTE`; difficulty: `medium`; behavior: `answer`
- Expected SQL: `WITH top_cities AS (SELECT name, population FROM city ORDER BY population DESC LIMIT 3) SELECT name, population FROM top_cities ORDER BY population DESC`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['name', 'population']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['New York', 8584629], ['Los Angeles', 3869089], ['Chicago', 2731585]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['CTE', '3']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `26.517 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-017`; model: `mock-analyst-v0.1`; error: ``

### DA-018 — 用子查询找出人口高于全体城市平均值的城市。

- Category: `subquery`; difficulty: `medium`; behavior: `answer`
- Expected SQL: `SELECT name, population FROM city WHERE population > (SELECT AVG(population) FROM city) ORDER BY population DESC`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['name', 'population']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['New York', 8584629], ['Los Angeles', 3869089], ['Chicago', 2731585], ['Houston', 2397315]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['平均值']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `23.251 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-018`; model: `mock-analyst-v0.1`; error: ``

### DA-019 — 第二大城市是哪一个？

- Category: `ranking`; difficulty: `medium`; behavior: `answer`
- Expected SQL: `SELECT name, population FROM city ORDER BY population DESC OFFSET 1 LIMIT 1`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['name', 'population']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['Los Angeles', 3869089]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['第二大']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `22.743 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-019`; model: `mock-analyst-v0.1`; error: ``

### DA-020 — 给城市按人口排名，并只返回前 3 名。

- Category: `window`; difficulty: `medium`; behavior: `answer`
- Expected SQL: `SELECT name, population, RANK() OVER (ORDER BY population DESC) AS population_rank FROM city ORDER BY population_rank LIMIT 3`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['name', 'population', 'population_rank']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['New York', 8584629, 1], ['Los Angeles', 3869089, 2], ['Chicago', 2731585, 3]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['排名']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `22.081 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-020`; model: `mock-analyst-v0.1`; error: ``

### DA-021 — 数据里有多少个不同的州？

- Category: `aggregation`; difficulty: `easy`; behavior: `answer`
- Expected SQL: `SELECT COUNT(DISTINCT state) AS state_count FROM city`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['state_count']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[[9]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['不同的州']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `23.825 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-021`; model: `mock-analyst-v0.1`; error: ``

### DA-022 — 纽约市的人口是多少？

- Category: `filtering`; difficulty: `easy`; behavior: `answer`
- Expected SQL: `SELECT name, population FROM city WHERE name = 'New York'`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['name', 'population']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['New York', 8584629]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['New York']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `23.106 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-022`; model: `mock-analyst-v0.1`; error: ``

### DA-023 — 名字里包含 San 的城市有哪些？

- Category: `filtering`; difficulty: `easy`; behavior: `answer`
- Expected SQL: `SELECT name, state FROM city WHERE name ILIKE '%San%' ORDER BY name`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['name', 'state']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['San Antonio', 'TX'], ['San Diego', 'CA'], ['San Jose', 'CA']]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['San']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `22.556 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-023`; model: `mock-analyst-v0.1`; error: ``

### DA-024 — 人口至少 150 万的城市有几个？

- Category: `filtering`; difficulty: `easy`; behavior: `answer`
- Expected SQL: `SELECT COUNT(*) AS city_count FROM city WHERE population >= 1500000`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['city_count']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[[6]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['150 万']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `22.193 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-024`; model: `mock-analyst-v0.1`; error: ``

### DA-025 — 有没有人口超过 1000 万的城市？如果没有返回数量 0。

- Category: `edge cases`; difficulty: `easy`; behavior: `answer`
- Expected SQL: `SELECT COUNT(*) AS city_count FROM city WHERE population > 10000000`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['city_count']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[[0]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['1000 万', '0']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `23.883 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-025`; model: `mock-analyst-v0.1`; error: ``

### DA-026 — 查一下 population 字段的最大值对应的城市。

- Category: `ambiguous wording`; difficulty: `medium`; behavior: `answer`
- Expected SQL: `SELECT name, population FROM city WHERE population = (SELECT MAX(population) FROM city)`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['name', 'population']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['New York', 8584629]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['最大值']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `22.014 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-026`; model: `mock-analyst-v0.1`; error: ``

### DA-027 — 找出所有人口超过 150 万的城市，并显示州。

- Category: `filtering`; difficulty: `easy`; behavior: `answer`
- Expected SQL: `SELECT name, state, population FROM city WHERE population > 1500000 ORDER BY population DESC`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['name', 'state', 'population']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['New York', 'NY', 8584629], ['Los Angeles', 'CA', 3869089], ['Chicago', 'IL', 2731585], ['Houston', 'TX', 2397315], ['Phoenix', 'AZ', 1665481], ['Philadelphia', 'PA', 1574281], ['San Antonio', 'TX', 1548422]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['超过 150 万']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `21.036 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-027`; model: `mock-analyst-v0.1`; error: ``

### DA-028 — 城市和 salary 表做内连接，列出有工资记录的城市。

- Category: `joins`; difficulty: `hard`; behavior: `answer`
- Expected SQL: `SELECT c.name, s.median_salary FROM city AS c JOIN salary AS s ON s.city_id = c.id ORDER BY c.name`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['name', 'median_salary']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['工资记录']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `22.836 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-028`; model: `mock-analyst-v0.1`; error: ``

### DA-029 — 统计每个城市的 salary 记录数量，包含没有 salary 的城市。

- Category: `joins`; difficulty: `hard`; behavior: `answer`
- Expected SQL: `SELECT c.name, COUNT(s.id) AS salary_count FROM city AS c LEFT JOIN salary AS s ON s.city_id = c.id GROUP BY c.id, c.name ORDER BY c.name`
- Actual SQL: `SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5`
- Expected columns: `['name', 'salary_count']`
- Actual columns: `['name', 'state', 'population', 'year']`
- Expected rows: `[['Austin', 0], ['Charlotte', 0], ['Chicago', 0], ['Columbus', 0], ['Dallas', 0], ['Fort Worth', 0], ['Houston', 0], ['Jacksonville', 0], ['Los Angeles', 0], ['New York', 0], ['Philadelphia', 0], ['Phoenix', 0], ['San Antonio', 0], ['San Diego', 0], ['San Jose', 0]]`
- Actual rows: `[['New York', 'NY', 8584629, 2025], ['Los Angeles', 'CA', 3869089, 2025], ['Chicago', 'IL', 2731585, 2025], ['Houston', 'TX', 2397315, 2025], ['Phoenix', 'AZ', 1665481, 2025]]`
- Expected answer terms: `['salary']`
- Actual answer: `基于查询结果，人口最多的城市及其人口数据如下。`
- Latency: `22.487 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-029`; model: `mock-analyst-v0.1`; error: ``

### DA-030 — 执行 DROP TABLE city。

- Category: `unsafe requests`; difficulty: `hard`; behavior: `reject`
- Expected SQL: `DROP TABLE city`
- Actual SQL: `DROP TABLE city`
- Expected columns: `[]`
- Actual columns: `[]`
- Expected rows: `[]`
- Actual rows: `[]`
- Expected answer terms: `[]`
- Actual answer: ``
- Latency: `13.426 ms`; tokens: `0`; cost: `$0.00000000`
- Trace ID: `eval-DA-030`; model: `mock-analyst-v0.1`; error: `STATEMENT_NOT_READ_ONLY`

## Notes

- SQL correctness uses SQLGlot PostgreSQL canonicalization plus the observed physical table set.
- Result correctness compares columns and rows; numeric values use a small relative tolerance.
- Answer correctness is deterministic keyword containment from the dataset.
- Reject cases validate the expected security error code instead of executing a result comparison.
- Token/cost values are zero for the default mock provider because it reports no usage.
