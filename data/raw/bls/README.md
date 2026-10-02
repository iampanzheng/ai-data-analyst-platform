# BLS OEWS May 2023 curated metro fixture

This directory contains a small source-backed Stage 3.2 fixture for Software Developers (SOC 15-1252) in five metropolitan areas anchored to demo cities. The statistical grain is **metropolitan area**, not city.

Official area pages:
- New York-Newark-Jersey City, NY-NJ-PA: https://www.bls.gov/oes/2023/May/oes_35620.htm
- Los Angeles-Long Beach-Anaheim, CA: https://www.bls.gov/oes/2023/May/oes_31080.htm
- Chicago-Naperville-Elgin, IL-IN-WI: https://www.bls.gov/oes/2023/May/oes_16980.htm
- Houston-The Woodlands-Sugar Land, TX: https://www.bls.gov/oes/2023/May/oes_26420.htm
- Phoenix-Mesa-Scottsdale, AZ: https://www.bls.gov/oes/2023/May/oes_38060.htm

`employment_count` and `mean_salary` are directly published OEWS estimates. `median_salary` in the database is a **derived annualized median** computed as published median hourly wage × 2,080 hours/year. It must not be described as a directly published BLS annual-median field.

The 2023 static area pages are used for this curated fixture because every value can be audited line-by-line from stable official pages. The schema/ETL design allows a later refresh to newer OEWS releases without changing the application architecture.
