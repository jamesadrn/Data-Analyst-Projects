# Power Query Transformation Steps

This document details all transformations applied to the Lending Club loan dataset using Power Query in Excel.

---

## Overview
- Source Dataset: `loan.csv` (145 columns, ~1m rows)
- Final Output: 15 columns, ~860K rows (2014-2016 data only)
- Tool Used: Microsoft Excel Power Query Editor

---

## Transformation Steps

### 1. Load Source Data
```m
Source = Csv.Document(File.Contents("...\loan.csv"), 
    [Delimiter=",", Columns=145, Encoding=1252, QuoteStyle=QuoteStyle.None])
```
- Loaded raw CSV file with 145 columns

---

### 2. Promote Headers
```m
#"First Row as Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true])
```
- Converted first row to column headers

---

### 3. Change Data Types
```m
#"Changed Type" = Table.TransformColumnTypes(...)
```
- Applied appropriate data types to all 145 columns:
  - Text: IDs, categorical variables (grade, purpose, state)
  - Integer (Int64): Loan amounts, account counts
  - Decimal (Number): Interest rates, ratios, percentages
  - Date: Issue dates, payment dates, credit line dates

---

### 4. Select Relevant Columns
```m
#"Removed Unused Columns" = Table.SelectColumns(#"Changed Type", {
    "loan_amnt", "funded_amnt", "term", "int_rate", "grade", 
    "sub_grade", "home_ownership", "annual_inc", "issue_d", 
    "loan_status", "purpose", "addr_state", "dti"
})
```
- Reduced from 145 columns → 13 columns
- Selected only variables relevant for credit risk analysis

---

### 5. Filter Issue Date (2014-2016)
```m
#"Filter Issue Date to 2014-2016" = Table.SelectRows(
    #"Removed Unused Columns", 
    each [issue_d] >= #date(2014, 1, 1) and [issue_d] <= #date(2016, 12, 31)
)
```
- Filtered loans issued between January 1, 2014 - December 31, 2016

---

### 6. Filter Loan Status
```m
#"Filter Loan Stats" = Table.SelectRows(
    #"Filter Issue Date to 2014-2016", 
    each ([loan_status] = "Charged Off" or 
          [loan_status] = "Default" or 
          [loan_status] = "Fully Paid")
)
```
- Kept only completed loans with final status:
  - ✅ Fully Paid (non-default)
  - ❌ Charged Off (default)
  - ❌ Default (default)
- Excluded: Current, Late, In Grace Period, etc.

---

### 7. Rename Columns
```m
#"Renamed Columns" = Table.RenameColumns(#"Filter Loan Stats", {
    {"term", "term (months)"},
    {"int_rate", "interest_rate"},
    {"loan_amnt", "loan_amount"},
    {"funded_amnt", "funded_amount"},
    {"annual_inc", "annual_income"},
    {"issue_d", "issue_date"},
    {"addr_state", "state"},
    {"dti", "dti_ratio"}
})
```
- Applied descriptive, standardized column names

---

### 8. Clean Term Column
```m
#"Trimmed term(months) column" = Table.TransformColumns(..., Text.Trim)
#"Extracted Text Before Delimiter" = Table.TransformColumns(..., Text.BeforeDelimiter(_, " "))
#"Changed term(months) Dtype" = Table.TransformColumnTypes(..., Int64.Type)
```
Steps:
1. Trimmed whitespace from term values (e.g., `" 36 months "`)
2. Extracted numeric part before space (e.g., `"36 months"` → `"36"`)
3. Converted to integer type

Result: `36 months` → `36`, `60 months` → `60`

---

### 9. Convert Interest Rate to Decimal
```m
#"Interest Rate to Decimal" = Table.TransformColumns(
    ..., 
    {{"interest_rate", each _ / 100, type number}}
)
```
- Converted percentage to decimal format
- Example: `10.5%` → `0.105`

---

### 10. Reorder Columns
```m
#"Reordered Columns" = Table.ReorderColumns(..., {
    "issue_date", "loan_amount", "funded_amount", "term (months)", 
    "interest_rate", "grade", "sub_grade", "home_ownership", 
    "annual_income", "loan_status", "purpose", "state", "dti_ratio"
})
```
- Organized columns in logical order (date → loan details → borrower info → status)

---

### 11. Trim All Text Columns
```m
#"Trimmed All Columns" = Table.TransformColumns(..., Text.Trim)
```
- Removed leading/trailing whitespace from all columns
- Ensured data consistency

---

### 12. Remove Null DTI Values
```m
#"Filtered Rows" = Table.SelectRows(
    #"Trimmed All Columns", 
    each [dti_ratio] <> null and [dti_ratio] <> ""
)
```
- Removed rows where DTI ratio is missing or empty
- DTI is critical for credit risk analysis

---

### 13. Remove All Missing Values
```m
#"Removed Missing Values Rows" = Table.SelectRows(
    #"Filtered Rows", 
    each not List.Contains(Record.FieldValues(_), null)
)
```
- Removed any remaining rows with null values in any column
- Ensured complete records only

---

### 14. Remove Duplicates
```m
#"Removed Duplicates" = Table.Distinct(#"Removed Missing Values Rows")
```
- Removed duplicate loan records

---

### 15. Final Data Type Conversion
```m
#"Changed Type - Final" = Table.TransformColumnTypes(..., {
    {"loan_amount", Int64.Type},
    {"funded_amount", Int64.Type},
    {"term (months)", Int64.Type},
    {"annual_income", Int64.Type},
    {"dti_ratio", type number},
    {"interest_rate", Percentage.Type},
    {"issue_date", type date}
})
```
- Applied final, correct data types after all transformations

---

### 16. Feature Engineering: Default Flag
```m
#"Feature Engineering 'default_flag'" = Table.AddColumn(
    #"Changed Type - Final", 
    "default_flag", 
    each if [loan_status] = "Fully Paid" then 0 else 1
)
```
Created binary target variable:
- `1` = Charged Off, Default (Default)
- `0` = Fully Paid (Non-default)

---

### 17. Feature Engineering: DTI Bucket
```m
#"Feature Engineering 'dti_bucket'" = Table.AddColumn(
    #"Feature Engineering 'default_flag'", 
    "dti_bucket", 
    each if [dti_ratio] < 10 then "Very Low (<10)" 
         else if [dti_ratio] < 20 then "Low (<20)" 
         else if [dti_ratio] < 30 then "Medium (<30)" 
         else "High (>=30)"
)
```
Created categorical DTI buckets:
- Very Low: DTI < 10%
- Low: 10% ≤ DTI < 20%
- Medium: 20% ≤ DTI < 30%
- High: DTI ≥ 30%

---

## Final Dataset Schema

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `issue_date` | Date | Date when loan was issued |
| `loan_amount` | Integer | Original loan amount requested |
| `funded_amount` | Integer | Amount actually funded |
| `term (months)` | Integer | Loan term (36 or 60 months) |
| `interest_rate` | Percentage | Interest rate (decimal format) |
| `grade` | Text | Lending Club assigned loan grade (A-G) |
| `sub_grade` | Text | Lending Club assigned sub-grade (A1-G5) |
| `home_ownership` | Text | Borrower's home ownership status |
| `annual_income` | Integer | Borrower's annual income |
| `loan_status` | Text | Final loan status (Fully Paid / Charged Off) |
| `purpose` | Text | Purpose of the loan |
| `state` | Text | US state of borrower |
| `dti_ratio` | Decimal | Debt-to-income ratio |
| `default_flag` | Integer | Binary flag: 1=Default, 0=Paid |
| `dti_bucket` | Text | DTI category (Very Low / Low / Medium / High) |

---

## Data Quality Summary

### Before Transformation:
- Rows: ~1m
- Columns: 145
- Issues: Missing values, inconsistent formats, irrelevant columns

### After Transformation:
- Rows: ~860,000 (filtered to 2014-2016)
- Columns: 15 (relevant variables only)
- Quality: No missing values, standardized formats, ready for analysis

---

## Notes
- All transformations are reproducible through Power Query
- Data types are optimized for Excel dashboard performance
- Feature engineering enables categorical analysis of risk factors
- Dataset is clean and analysis-ready

---

## Power Query M Code
The complete M code for these transformations is available in the query editor and can be exported from Excel.

---

Last Updated: January 2026  
Created by: James