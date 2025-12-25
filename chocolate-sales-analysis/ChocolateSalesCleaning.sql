/******************************************************************
ETL PIPELINE – Chocolate Sales Data
Description  : Cleans and prepares data for visualization
Date Created : CURRENT_DATE
******************************************************************/

-------------------------------
-- STEP 1. INSPECT RAW DATA
-------------------------------

-- Preview a few rows from the raw table
SELECT * FROM chocolate_sales LIMIT 5;

-- Check table structure and data types
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'chocolate_sales';


-------------------------------
-- STEP 2. TRANSFORM - DATA CLEANING
-------------------------------

-- 2.1 Add a new numeric column for Amount if it does not exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='chocolate_sales' AND column_name='amount_num'
    ) THEN
        ALTER TABLE chocolate_sales ADD COLUMN amount_num numeric;
    END IF;
END $$;

-- 2.2 Remove '$' and ',' characters and convert to numeric
UPDATE chocolate_sales
SET amount_num = REPLACE(REPLACE("Amount", '$', ''), ',', '')::numeric
WHERE "Amount" IS NOT NULL;

-- 2.3 Convert "Date" column from text to proper date type
ALTER TABLE chocolate_sales
ALTER COLUMN "Date" TYPE date
USING to_date("Date", 'DD-Mon-YY');


-------------------------------
-- STEP 3. DATA VALIDATION / PROFILING
-------------------------------

-- 3.1 Create a function for column-level profiling
CREATE OR REPLACE FUNCTION profile_table(_schema_name text, _table_name text)
RETURNS TABLE (
    column_name text,
    total_rows bigint,
    null_count bigint,
    null_percent numeric,
    unique_values bigint
)
LANGUAGE plpgsql AS $$
DECLARE
    sql text;
BEGIN
    SELECT string_agg(
        format(
            'SELECT %L AS column_name,
                    COUNT(*) AS total_rows,
                    SUM(CASE WHEN %I IS NULL THEN 1 ELSE 0 END) AS null_count,
                    ROUND(SUM(CASE WHEN %I IS NULL THEN 1 ELSE 0 END)*100.0/COUNT(*), 2) AS null_percent,
                    COUNT(DISTINCT %I) AS unique_values
             FROM %I.%I',
            col.column_name, col.column_name, col.column_name, col.column_name, _schema_name, _table_name
        ),
        ' UNION ALL '
    )
    INTO sql
    FROM information_schema.columns AS col
    WHERE col.table_schema = _schema_name
      AND col.table_name = _table_name;

    RETURN QUERY EXECUTE sql;
END $$;

-- Run the profiling function
SELECT * FROM profile_table('public', 'chocolate_sales');


-------------------------------
-- STEP 4. DATA QUALITY CHECKS
-------------------------------

-- 4.1 Check for duplicate records (based on all key columns)
SELECT 
    "Sales Person",
    "Country",
    "Product",
    "Date",
    amount_num,
    "Boxes Shipped",
    COUNT(*) AS duplicate_count
FROM chocolate_sales
GROUP BY 
    "Sales Person", "Country", "Product", "Date", amount_num, "Boxes Shipped"
HAVING COUNT(*) > 1;

-- 4.2 Check for invalid or unrealistic dates
SELECT *
FROM chocolate_sales
WHERE "Date" > CURRENT_DATE
   OR "Date" < DATE '2000-01-01';

-- 4.3 Check for negative numeric values
SELECT *
FROM chocolate_sales
WHERE amount_num < 0 OR "Boxes Shipped" < 0;


-------------------------------
-- STEP 5. OUTLIER DETECTION
-------------------------------
-- Identify potential outliers based on IQR method
WITH stats AS (
  SELECT 
    percentile_cont(0.25) WITHIN GROUP (ORDER BY amount_num) AS q1,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY amount_num) AS q3
  FROM chocolate_sales
)
SELECT 
  c."Sales Person",
  c."Product",
  c.amount_num,
  s.q1, s.q3,
  (s.q3 - s.q1) AS iqr
FROM chocolate_sales c
CROSS JOIN stats s
WHERE c.amount_num > (s.q3 + 1.5 * (s.q3 - s.q1))
   OR c.amount_num < (s.q1 - 1.5 * (s.q3 - s.q1));


-------------------------------
-- STEP 6. CREATE CLEAN VIEW 
-------------------------------
-- Create a clean version of the dataset for Power BI / Tableau
CREATE OR REPLACE VIEW chocolate_sales_clean AS
SELECT 
    "Sales Person" AS sales_person,
    "Country" AS country,
    "Product" AS product,
    "Date" AS date,
    amount_num AS amount,
    "Boxes Shipped" AS boxes_shipped
FROM chocolate_sales
WHERE 
    "Date" BETWEEN DATE '2000-01-01' AND CURRENT_DATE
    AND amount_num >= 0
    AND "Boxes Shipped" >= 0;

-- Verify the clean view
SELECT * FROM chocolate_sales_clean LIMIT 10;


------------------------------------------------------------------
-- PIPELINE END
------------------------------------------------------------------