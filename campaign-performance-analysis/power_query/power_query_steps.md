# Power Query Sales Data Processing Pipeline

## Overview
This Power Query M script processes raw sales/advertising data from an Excel table, implementing comprehensive data validation, cleaning, and feature engineering to prepare analytics-ready data for marketing performance analysis.

## Pipeline Architecture

```
Raw Data (Excel) 
    ↓
Data Import & Type Conversion
    ↓
Column Management & Cleanup
    ↓
Data Validation (Funnel Logic)
    ↓
Feature Engineering
    ↓
Performance Classification
    ↓
Clean Output Dataset
```

---

## Processing Steps

### 1. Data Import
**Step:** `Source`
- Imports data from Excel table named "Sales"
- Source: `Excel.CurrentWorkbook()`

### 2. Data Type Conversion
**Step:** `Changed Type`

Enforces strict typing for all columns:

| Column | Type | Description |
|--------|------|-------------|
| Ad_ID | Text | Unique advertisement identifier |
| Campaign_Name | Text | Marketing campaign name |
| Clicks | Integer | Number of ad clicks |
| Impressions | Integer | Number of ad impressions |
| Cost | Number | Advertising spend |
| Leads | Integer | Generated leads count |
| Conversions | Integer | Completed conversions |
| Conversion Rate | Number | Raw conversion rate |
| Sale_Amount | Integer | Revenue generated |
| Ad_Date | Any | Date (to be cleaned) |
| Location | Text | Geographic location |
| Device | Text | User device type |
| Keyword | Text | Search keyword |

### 3. Column Management
**Steps:** `Reordered Columns` → `Removed Location Column`

- Reorders columns in logical funnel sequence: ID → Date → Campaign → Cost → Impressions → Clicks → Leads → Conversions → Revenue
- Removes `Location` column (not needed for analysis)

### 4. Column Renaming
**Step:** `Renamed Columns`

Standardizes all column names to **snake_case** convention:

```
Ad_ID           → ad_id
Ad_Date         → ad_date_raw
Cost            → cost
Impressions     → impressions
Clicks          → clicks
Leads           → leads
Conversions     → conversions
Conversion Rate → cvr_raw
Sale_Amount     → sale_amount
Device          → device
Campaign_Name   → campaign_name
Keyword         → keywords
```

### 5. Text Cleaning & Standardization
**Steps:** `Lowercased Device` → `Capitalized Device` → `Trimmed Keywords`

- **Device column:** Normalized to Title Case (e.g., "mobile" → "Mobile")
- **Keywords column:** Trimmed whitespace from both ends

### 6. Data Validation - Funnel Logic
**Step:** `Add Valid Data Flag`

Implements comprehensive validation with `valid_data_flag` (boolean):

#### Required Fields (Must-Have)
- ✅ `impressions` > 0 and not null
- ✅ `cost` > 0 and not null (ensures paid ads only)
- ✅ `device` is not empty
- ✅ `ad_date_raw` is not null

#### Funnel Metrics (Should-Have)
- ✅ `clicks`, `leads`, `conversions` are not null (can be 0)
- ⚠️ `sale_amount` can be null (treated as 0 later)

#### Funnel Logic Validation
Ensures parent-child relationship integrity:
```
Impressions ≥ Clicks ≥ Leads ≥ Conversions
```

**Validation Rules:**
- `clicks ≤ impressions`
- `leads ≤ clicks`
- `conversions ≤ leads`

### 7. Filter Valid Data
**Step:** `Filtered Valid Data Only`

- Removes all rows where `valid_data_flag = false`
- Ensures only high-quality, paid advertising data proceeds

### 8. Date Cleaning
**Step:** `Add Cleaned Date`

Creates `ad_date` column with robust date parsing:
1. Attempts standard `Date.From()` conversion
2. Falls back to locale-specific parsing (`id-ID` format)

### 9. Campaign Naming Validation
**Steps:** `Add Campaign Naming Flag` → `Removed campaign_name`

- Creates `campaign_naming_issue_flag`:
  - `0` = Campaign name contains "DataAnalyticsCourse" ✅
  - `1` = Campaign name missing standard naming convention ⚠️
- Removes original `campaign_name` column after validation

### 10. NULL Handling for Revenue
**Step:** `Replaced Null Revenue`

- Replaces `null` values in `sale_amount` with `0`
- Enables ROAS calculation without errors
- Distinguishes between "no conversion" (0) and "missing data" (filtered earlier)

### 11. Keyword Intent Classification
**Steps:** `Add Keyword Intent` → `Removed Keywords`

Classifies search intent based on keyword analysis:

| Intent Category | Trigger Keywords | Description |
|----------------|------------------|-------------|
| Course Seeking | "course" | Direct course purchase intent |
| Training Seeking | "training" | Professional training interest |
| Learning Exploration | "learn" | Educational research phase |
| General Search | (default) | Broad/unclassified searches |

- Case-insensitive matching
- Removes original `keywords` column after classification

### 12. ROAS Calculation
**Step:** `Add ROAS`

Calculates Return on Ad Spend:

```
ROAS = sale_amount / cost
```

- Returns `null` if `cost` is 0 or null
- `sale_amount` already null-handled (0 for no conversion)

### 13. Performance Tier Classification
**Step:** `Add Performance Tier`

Categorizes ad performance into tiers based on ROAS:

| Tier | ROAS Range | Description |
|------|-----------|-------------|
| Loss (≤0%) | ROAS ≤ 0 | No revenue or negative returns |
| Low (≤300%) | 0 < ROAS ≤ 3.0 | Underperforming campaigns |
| Good (301-600%) | 3.0 < ROAS ≤ 6.0 | Healthy performance |
| Excellent (>600%) | ROAS > 6.0 | Top-performing campaigns |

### 14. Final Cleanup
**Steps:** `Removed Obsolete Columns` → `Changed Final Types`

- Removes temporary columns: `ad_date_raw`, `cvr_raw`, `valid_data_flag`
- Converts `ad_date` to proper `date` type
- Ensures `campaign_naming_issue_flag` is integer

### 15. Final Column Reordering
**Step:** `Reordered Final`

Final schema in logical order:

```
1. ad_id
2. ad_date
3. device
4. keyword_intent
5. campaign_naming_issue_flag
6. impressions
7. clicks
8. leads
9. conversions
10. cost
11. sale_amount
12. roas
13. performance_tier
```

---

## Output Schema

| Column Name | Type | Description | Example |
|-------------|------|-------------|---------|
| `ad_id` | Text | Unique ad identifier | "AD-12345" |
| `ad_date` | Date | Advertisement date | 2024-01-15 |
| `device` | Text | Device type (Title Case) | "Mobile" |
| `keyword_intent` | Text | Search intent category | "Course Seeking" |
| `campaign_naming_issue_flag` | Integer | Naming compliance (0=OK, 1=Issue) | 0 |
| `impressions` | Integer | Ad impressions count | 10000 |
| `clicks` | Integer | Click count | 250 |
| `leads` | Integer | Leads generated | 45 |
| `conversions` | Integer | Conversions completed | 12 |
| `cost` | Number | Ad spend (USD) | 150.00 |
| `sale_amount` | Integer | Revenue generated (USD) | 900 |
| `roas` | Number | Return on ad spend | 6.0 |
| `performance_tier` | Text | Performance category | "Excellent (>600%)" |

---

## Key Features

### ✅ Data Quality Assurance
- Funnel logic validation ensures data integrity
- Filters invalid/incomplete records
- Handles null values appropriately

### 📊 Feature Engineering
- Keyword intent classification
- ROAS calculation
- Performance tier segmentation
- Campaign naming compliance tracking

### 🔄 Robust Error Handling
- Multiple date parsing strategies
- Safe division (ROAS calculation)
- Null value replacement for revenue

### 📝 Best Practices
- Snake_case naming convention
- Comprehensive inline comments
- Logical column ordering
- Clean separation of concerns

---

## Use Cases

This cleaned dataset enables:
1. **Marketing Performance Analysis** - Track ROAS by device, intent, date
2. **Funnel Optimization** - Analyze drop-offs at each stage
3. **Budget Allocation** - Identify high-performing segments
4. **Campaign Auditing** - Flag naming convention violations
5. **Keyword Strategy** - Optimize by intent category

---

## Notes

- **Paid Ads Only:** Pipeline filters for `cost > 0` to exclude organic traffic
- **Locale Support:** Date parsing supports Indonesian locale (`id-ID`)
- **ROAS Focus:** Performance tiers optimized for digital marketing benchmarks
- **Naming Standards:** Enforces "DataAnalyticsCourse" campaign naming convention

---

## Author
Last Updated: January 2026  
Created by: James