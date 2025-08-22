---------------------------------------
# 🧠 Extremely Advanced SQL Topics

This document outlines some of the most advanced SQL concepts used in enterprise-level data analytics, engineering, and optimization. These topics are ideal for senior-level professionals looking to deepen their SQL expertise.

---

## 🔁 1. Recursive Common Table Expressions (CTEs)
- Traverse hierarchical or graph-based data structures.
- Useful for org charts, category trees, and dependency resolution.

---

## 📊 2. Advanced Window Functions
- Beyond basic ranking: `LAG()`, `LEAD()`, `FIRST_VALUE()`, `LAST_VALUE()`.
- Use cases include running totals, moving averages, and time-based comparisons.

---

## ⚙️ 3. Query Optimization & Execution Plans
- Analyze performance using `EXPLAIN` or `EXPLAIN ANALYZE`.
- Understand join algorithms, indexing strategies, and cost-based optimization.

---

## 🧮 4. Materialized Views & Query Caching
- Precompute and store query results for performance.
- Learn refresh strategies: on-demand, scheduled, or incremental.

---

## 🧬 5. Dynamic SQL
- Construct and execute SQL statements at runtime.
- Common in stored procedures and metadata-driven reporting.

---

## 🔄 6. Pivoting and Unpivoting Data
- Transform rows into columns and vice versa.
- Essential for reshaping data for reporting and analysis.

---

## ⏳ 7. Temporal Tables & Time Travel
- Query historical versions of data.
- Useful for auditing, compliance, and tracking changes over time.

---

## 🔗 8. Advanced Joins
- Anti-joins (`NOT EXISTS`, `LEFT JOIN` + `IS NULL`).
- Semi-joins, self-joins, and cross joins for complex logic.

---

## 📐 9. Set-Based Logic & Relational Algebra
- Use `INTERSECT`, `EXCEPT`, and `UNION` for set operations.
- Apply relational theory to solve complex problems.

---

## 🏛️ 10. Data Warehousing Concepts in SQL
- Querying star and snowflake schemas.
- Handling Slowly Changing Dimensions (SCDs) and fact/dimension modeling.

---

## 📦 11. JSON and XML Processing
- Query and transform semi-structured data.
- Use functions like `JSON_VALUE()`, `OPENJSON()`, or `->`, `->>`.

---

## 🔧 12. User-Defined Functions (UDFs) and Stored Procedures
- Encapsulate reusable logic.
- Handle parameters, control flow, and error management.

---

## 🔐 13. Concurrency and Transaction Isolation
- Understand ACID properties and isolation levels.
- Prevent deadlocks and ensure data consistency.

---

## 🧭 14. Data Lineage and Auditing
- Track data transformations across systems.
- Implement audit trails and metadata tracking.

---

## 🛡️ 15. Advanced Security & Row-Level Security
- Implement fine-grained access control.
- Restrict data visibility based on user roles or policies.

---

> 💡 **Tip:** These topics are best learned through hands-on projects and performance tuning exercises. Consider building a mini data warehouse or analytics dashboard to apply these concepts.
=========================================================================
> Here’s your content converted into clean **Markdown format** suitable for a `README.md` file on GitHub. I’ve preserved your structure, added fenced code blocks for SQL, and formatted `<xaiArtifact>` blocks as collapsible details (so they don’t clutter the page but remain reusable).

````markdown
# Advanced SQL Interview Questions

Below is a curated list of advanced SQL interview questions, including scenario-based questions, designed to test deep knowledge of SQL concepts such as complex joins, window functions, query optimization, and database design.  

Each question includes a detailed answer with SQL code wrapped inside collapsible `<details>` blocks for readability. These questions are suitable for candidates preparing for senior data analyst, data engineer, or database developer roles.

---

## 1. Advanced: Optimizing a Slow Query with Multiple Joins
**Scenario**: You are a data engineer at a retail company. The following SQL query, which retrieves sales data with product and customer details, takes 10 seconds to run on a database with 10M sales records, 1M products, and 500K customers.

```sql
SELECT 
    s.SaleID, 
    p.ProductName, 
    c.CustomerName, 
    s.SaleDate, 
    s.Amount
FROM Sales s
JOIN Products p ON s.ProductID = p.ProductID
JOIN Customers c ON s.CustomerID = c.CustomerID
WHERE s.SaleDate >= '2024-01-01' 
AND c.Region = 'North America';
````

**Question**: How would you optimize this query to run faster? Provide specific steps, including indexing strategies, query rewriting, and any database configuration changes.

**Answer**:

* Analyze execution plan
* Add composite and selective indexes
* Rewrite joins to push filters down
* Partition large tables by `SaleDate`
* Keep statistics updated
* Consider materialized views

<details>
<summary>📄 Optimized Query (click to expand)</summary>

```sql
-- Create indexes
CREATE INDEX idx_sales_date_customer_product 
ON Sales (SaleDate, CustomerID, ProductID);

CREATE INDEX idx_customers_region 
ON Customers (Region, CustomerID);

-- Optimized query
SELECT 
    s.SaleID, 
    p.ProductName, 
    c.CustomerName, 
    s.SaleDate, 
    s.Amount
FROM Sales s
INNER JOIN Customers c 
    ON s.CustomerID = c.CustomerID
    AND c.Region = 'North America'
INNER JOIN Products p 
    ON s.ProductID = p.ProductID
WHERE s.SaleDate >= '2024-01-01';
```

</details>

---

## 2. Advanced: Window Functions for Running Totals

**Scenario**: You work for a financial company analyzing daily transactions.

**Question**: Write a SQL query to compute the running balance and flag negative balances.

**Answer**:
Use a `SUM()` window function with ordering by `TransactionDate` and `TransactionID`.

<details>
<summary>📄 Running Balance Query</summary>

```sql
SELECT 
    AccountID,
    TransactionDate,
    Amount,
    TransactionType,
    SUM(
        CASE 
            WHEN TransactionType = 'Deposit' THEN Amount 
            WHEN TransactionType = 'Withdrawal' THEN -Amount 
            ELSE 0 
        END
    ) OVER (
        PARTITION BY AccountID 
        ORDER BY TransactionDate, TransactionID
    ) AS RunningBalance,
    CASE 
        WHEN SUM(
            CASE 
                WHEN TransactionType = 'Deposit' THEN Amount 
                WHEN TransactionType = 'Withdrawal' THEN -Amount 
                ELSE 0 
            END
        ) OVER (
            PARTITION BY AccountID 
            ORDER BY TransactionDate, TransactionID
        ) < 0 THEN 'Negative'
        ELSE 'Positive'
    END AS BalanceStatus
FROM Transactions
ORDER BY AccountID, TransactionDate, TransactionID;
```

</details>

---

## 3. Advanced: Recursive CTE for Organizational Hierarchy

**Scenario**: You need to generate a report showing the full organizational hierarchy (CEO → Managers → Employees).

**Answer**:
Use a recursive CTE starting from top-level employees (`ManagerID IS NULL`).

<details>
<summary>📄 Hierarchy Query</summary>

```sql
WITH EmployeeHierarchy AS (
    -- Anchor: Start with top-level employees
    SELECT 
        EmployeeID,
        Name,
        ManagerID,
        CAST(NULL AS VARCHAR(50)) AS ManagerName,
        1 AS HierarchyLevel
    FROM Employees
    WHERE ManagerID IS NULL

    UNION ALL

    -- Recursive: Join to find subordinates
    SELECT 
        e.EmployeeID,
        e.Name,
        e.ManagerID,
        m.Name AS ManagerName,
        eh.HierarchyLevel + 1 AS HierarchyLevel
    FROM Employees e
    INNER JOIN EmployeeHierarchy eh 
        ON e.ManagerID = eh.EmployeeID
    INNER JOIN Employees m 
        ON e.ManagerID = m.EmployeeID
)
SELECT 
    EmployeeID,
    Name,
    ManagerName,
    HierarchyLevel,
    REPEAT('  ', HierarchyLevel - 1) + Name AS IndentedName
FROM EmployeeHierarchy
ORDER BY HierarchyLevel, Name;
```

</details>

---

## 4. Advanced: Pivoting Data with Dynamic Columns

**Scenario**: Generate a pivot table of monthly revenue per category (dynamic columns).

**Answer**:
Use dynamic SQL with `STRING_AGG` to construct the pivot.

<details>
<summary>📄 Dynamic Pivot Query</summary>

```sql
DECLARE @Columns NVARCHAR(MAX), @SQL NVARCHAR(MAX);

-- Get distinct categories
SET @Columns = (
    SELECT STRING_AGG(QUOTENAME(Category), ', ')
    FROM (SELECT DISTINCT Category FROM Sales) AS Categories
);

-- Build dynamic pivot
SET @SQL = N'
SELECT *
FROM (
    SELECT 
        FORMAT(SaleDate, ''yyyy-MM'') AS SaleMonth,
        Category,
        Revenue
    FROM Sales
) AS SourceTable
PIVOT (
    SUM(Revenue)
    FOR Category IN (' + @Columns + ')
) AS PivotTable
ORDER BY SaleMonth;
';

EXEC sp_executesql @SQL;
```

</details>

---

## 5. Advanced: Detecting and Resolving Deadlocks

**Scenario**: Banking system deadlocks occur when updating `Accounts` and `Transactions`.

**Answer**:

* Enable deadlock logging
* Use consistent locking order
* Reduce transaction scope
* Add retry logic

<details>
<summary>📄 Transaction Example</summary>

```sql
BEGIN TRY
    BEGIN TRANSACTION;
    
    -- Lock Accounts table first
    UPDATE Accounts
    SET Balance = Balance - 100
    WHERE AccountID = 1;
    
    UPDATE Accounts
    SET Balance = Balance + 100
    WHERE AccountID = 2;
    
    -- Insert transaction log
    INSERT INTO Transactions (AccountID, Amount, TransactionType, TransactionDate)
    VALUES (1, -100, 'Withdrawal', GETDATE()),
           (2, 100, 'Deposit', GETDATE());
    
    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
    INSERT INTO ErrorLog (ErrorMessage, ErrorDate)
    VALUES (@ErrorMessage, GETDATE());
END CATCH;
```

</details>

---

## Notes

* **Testing**: Always verify execution plans and simulate concurrency where needed.
* **Database-specific**: Syntax may differ slightly across SQL Server, PostgreSQL, MySQL, and Oracle.
* **Scalability**: Solutions are designed with indexing, partitioning, and concurrency in mind.

---

```

👉 This version is GitHub-friendly, collapses long SQL blocks for readability, and keeps explanations clean.  

Do you also want me to **add a Table of Contents at the top** (auto-links to each question), so recruiters/interviewers can jump directly to specific topics?
```
Here’s the **Markdown-formatted version** of the **Power BI interview questions** you can use in your `README.md` file on GitHub:

```markdown
# 📊 Power BI Interview Questions – Medium to Hard Level

This document contains scenario-based Power BI interview questions designed for Senior Data Analyst roles. These questions assess real-world problem-solving, dashboarding, and data storytelling skills.

---

## 🔍 Data Analysis & Problem Solving

### 1. Case Study
**Question:**  
You’re given a dataset with customer transactions. How would you identify high-value customers and suggest strategies to retain them?

**Expected Answer:**  
- Use RFM (Recency, Frequency, Monetary) analysis.
- Segment customers based on purchase behavior.
- Visualize segments using clustering or slicers.
- Recommend loyalty programs or targeted campaigns.

---

### 2. Scenario
**Question:**  
You notice a sudden drop in sales in one region. How would you investigate the cause using Power BI?

**Expected Answer:**  
- Use filters and slicers to isolate the region.
- Compare KPIs over time using line charts.
- Drill down into product categories and sales reps.
- Check for anomalies or missing data.

---

### 3. A/B Testing
**Question:**  
Explain how you would design an A/B test to evaluate the impact of a new feature on user engagement.

**Expected Answer:**  
- Define control and test groups.
- Use DAX to calculate engagement metrics.
- Visualize differences using bar/line charts.
- Apply statistical significance testing if needed.

---

## 📈 BI Tools & Visualization

### 4. Visualization Strategy
**Question:**  
How do you decide which visualization type to use for different kinds of data insights?

**Expected Answer:**  
- Bar charts for comparisons.
- Line charts for trends.
- Pie/donut charts for proportions (limited use).
- Scatter plots for correlations.
- KPI cards for metrics.

---

### 5. Dashboard Design
**Question:**  
Describe a complex dashboard you built in Power BI. What challenges did you face and how did you overcome them?

**Expected Answer:**  
- Discuss data sources, relationships, and DAX measures.
- Mention performance tuning (e.g., reducing visuals, optimizing queries).
- Explain user feedback and iteration cycles.

---

### 6. Performance Optimization
**Question:**  
How do you ensure your dashboards are both performant and user-friendly?

**Expected Answer:**  
- Limit visuals per page.
- Use aggregations and pre-processed data.
- Avoid complex DAX in visuals.
- Use bookmarks and tooltips for better UX.

---

## 🧠 Advanced DAX & Modeling

### 7. DAX Challenge
**Question:**  
Write a DAX formula to calculate Year-over-Year growth for revenue.

**Expected Answer:**
```DAX
YoY Growth = 
VAR CurrentYear = CALCULATE(SUM(Sales[Revenue]), YEAR(Sales[Date]) = YEAR(TODAY()))
VAR LastYear = CALCULATE(SUM(Sales[Revenue]), YEAR(Sales[Date]) = YEAR(TODAY()) - 1)
RETURN
DIVIDE(CurrentYear - LastYear, LastYear)
```

---

### 8. Data Modeling
**Question:**  
How do you handle many-to-many relationships in Power BI?

**Expected Answer:**  
- Use bridge tables.
- Apply bi-directional filtering cautiously.
- Normalize data if possible.

---

### 9. Row-Level Security
**Question:**  
How would you implement row-level security in Power BI?

**Expected Answer:**  
- Define roles in Power BI Desktop.
- Use DAX filters on tables.
- Publish and test roles in Power BI Service.

---

## ☁️ Integration & Automation

### 10. Cloud Integration
**Question:**  
Describe your experience connecting Power BI to cloud platforms like Azure or AWS.

**Expected Answer:**  
- Use Azure SQL, Blob Storage, or Data Lake as sources.
- Configure gateways for on-prem/cloud hybrid setups.
- Automate refreshes using Power BI Service.

---

### 11. Power BI Service
**Question:**  
How do you manage workspace access and deployment pipelines?

**Expected Answer:**  
- Use deployment pipelines for dev/test/prod.
- Assign roles: viewer, contributor, admin.
- Monitor usage and performance via audit logs.

---

> 💡 **Tip:** These questions are ideal for assessing candidates' ability to work with complex datasets, build scalable dashboards, and communicate insights effectively.

```
Here’s a **Markdown-formatted example** of a **Recursive CTE** using source and destination data, ideal for your `README.md` file on GitHub:

```markdown
# 🔁 Recursive CTE Example: Source to Destination Path Traversal

This example demonstrates how to use a **Recursive Common Table Expression (CTE)** to find all possible paths from a source to a destination in a directed graph-like structure.

---

## 📋 Sample Data

We have a table called `routes` representing connections between cities:

| source | destination |
|--------|-------------|
| A      | B           |
| B      | C           |
| C      | D           |
| A      | E           |
| E      | F           |
| F      | D           |

---

## 🎯 Goal

Find all paths from city `A` to city `D`.

---

## 🧠 Recursive CTE Query

```sql
WITH RECURSIVE path_cte AS (
    -- Anchor member: start from source 'A'
    SELECT 
        source,
        destination,
        source || ' -> ' || destination AS path
    FROM 
        routes
    WHERE 
        source = 'A'

    UNION ALL

    -- Recursive member: join with next leg of the route
    SELECT 
        r.source,
        r.destination,
        pc.path || ' -> ' || r.destination AS path
    FROM 
        routes r
    INNER JOIN 
        path_cte pc ON r.source = pc.destination
)
SELECT 
    path
FROM 
    path_cte
WHERE 
    destination = 'D';
```

---

## ✅ Output

| path                     |
|--------------------------|
| A -> B -> C -> D         |
| A -> E -> F -> D         |

---

## 🧩 Explanation

- The **anchor query** starts with all routes from `A`.
- The **recursive part** joins the current destination to the next source.
- The recursion continues until all paths to `D` are found.
- The final `SELECT` filters only those paths ending at `D`.

---

> 💡 Recursive CTEs are powerful for traversing hierarchical or graph-like data such as org charts, network paths, or dependency trees.

```

