Below is a curated list of medium to advanced Power BI questions, each with detailed answers and, where applicable, artifacts such as DAX code or Power Query snippets. These questions cover key areas like DAX, data modeling, Power Query, and report optimization, designed to challenge intermediate to advanced Power BI users. Each question includes a solution wrapped in an `<xaiArtifact>` tag where appropriate, ensuring the content is practical and reusable.

---

### 1. Medium: Creating a Dynamic Rolling Average Measure
**Question**: How would you create a DAX measure to calculate a 7-day rolling average of sales, ensuring it dynamically adjusts based on a date slicer selection? The measure should handle missing dates and exclude future dates.

**Answer**:
To calculate a 7-day rolling average, you need a DAX measure that aggregates sales over a 7-day window relative to each date in the report. The measure must respect slicer filters, handle missing dates (e.g., no sales on a day), and exclude future dates to avoid skewing the average. You can use `DATESINPERIOD` to define the rolling window and `AVERAGEX` to compute the average.

<xaiArtifact artifact_id="ee20a79e-b0d0-453c-a36a-a957a984ed87" artifact_version_id="ff7d241c-263e-48dd-8ff2-82300eb4325f" title="RollingAverageDAX.txt" contentType="text/plain">
Rolling7DayAvgSales = 
VAR MaxDate = MAX('Date'[Date]) -- Get the latest date in the current context
VAR RollingPeriod = 
    DATESINPERIOD(
        'Date'[Date],
        MaxDate,
        -7,
        DAY
    )
VAR SalesInPeriod = 
    CALCULATE(
        SUM('Sales'[Amount]),
        RollingPeriod,
        'Date'[Date] <= TODAY() -- Exclude future dates
    )
VAR DaysWithSales = 
    COUNTROWS(
        FILTER(
            RollingPeriod,
            CALCULATE(SUM('Sales'[Amount])) > 0
        )
    )
RETURN
    IF(
        DaysWithSales > 0,
        DIVIDE(SalesInPeriod, DaysWithSales, 0),
        BLANK()
    )
</xaiArtifact>

**Explanation**:
- `DATESINPERIOD` creates a 7-day window ending at the maximum date in the filter context.
- `CALCULATE(SUM('Sales'[Amount]), ...)` sums sales within this period, excluding future dates using `TODAY()`.
- `DaysWithSales` counts days with actual sales to avoid dividing by 7 if some days have no data.
- `DIVIDE` computes the average, returning `BLANK()` for invalid cases to avoid cluttering visuals.
- **Validation**: Test the measure in a line chart with a date slicer. Ensure the average updates correctly when selecting different date ranges and that future dates show no values.

---

### 2. Medium: Optimizing Power Query for Large Datasets
**Question**: You have a Power Query that merges a 5M-row sales table with a 1M-row customer table, followed by transformations like grouping and unpivoting. The refresh takes 20 minutes. How would you optimize the query?

**Answer**:
To optimize the Power Query, focus on query folding, reducing data early, and leveraging buffering. Here’s a step-by-step approach with a sample query:

1. **Enable Query Folding**: Ensure transformations (e.g., filters, joins) are pushed back to the source database (e.g., SQL Server) by applying filters before merges.
2. **Filter Early**: Remove unnecessary rows (e.g., filter by date range) before merging to reduce memory usage.
3. **Use Table.Buffer**: For non-foldable operations (e.g., unpivoting), buffer the smaller table to avoid repeated evaluations.
4. **Remove Unnecessary Columns**: Drop unused columns before heavy transformations.
5. **Validate Folding**: Use SQL Server Profiler or Power BI’s “View Native Query” to confirm query folding.

<xaiArtifact artifact_id="3b712718-6a8c-4086-bb27-d6debb6a0223" artifact_version_id="df7bf1c9-4085-405a-a8ee-924b58833c03" title="OptimizedSalesQuery.m" contentType="text/plain">
let
    SourceSales = Sql.Database("Server", "Database", [Query="SELECT SaleID, CustomerID, SaleDate, Amount FROM Sales WHERE SaleDate >= '2024-01-01'"]),
    SourceCustomers = Sql.Database("Server", "Database", [Query="SELECT CustomerID, Region FROM Customers"]),
    FilteredSales = Table.SelectRows(SourceSales, each [SaleDate] <= DateTime.LocalNow()),
    BufferedCustomers = Table.Buffer(SourceCustomers),
    MergedData = Table.Join(FilteredSales, "CustomerID", BufferedCustomers, "CustomerID", JoinKind.Inner),
    RemovedColumns = Table.SelectColumns(MergedData, {"SaleID", "SaleDate", "Amount", "Region"}),
    GroupedData = Table.Group(RemovedColumns, {"Region", "SaleDate"}, {{"TotalAmount", each List.Sum([Amount]), type number}})
in
    GroupedData
</xaiArtifact>

**Explanation**:
- The query filters sales by date in the SQL query to leverage query folding.
- `Table.Buffer` caches the smaller `Customers` table to optimize the merge.
- Columns are removed before grouping to reduce memory usage.
- **Validation**: Check “View Native Query” in Power Query Editor to ensure filters are applied at the source. Use Performance Analyzer to measure refresh time improvements.

---

### 3. Advanced: Dynamic Ranking with Tiebreakers
**Question**: Create a DAX measure to rank products by sales amount, with ties broken by profit margin. The ranking should respect slicers for region and date range.

**Answer**:
To rank products with tiebreakers, use `RANKX` with a calculated table that combines sales and profit margin. The measure must handle dynamic filter contexts from slicers.

<xaiArtifact artifact_id="2ee18029-5d66-4277-a100-fd771210ac05" artifact_version_id="c82f0016-8bc1-4b6d-ac9c-17a7d5370d3f" title="ProductRankingDAX.txt" contentType="text/plain">
ProductRank = 
VAR CurrentProduct = SELECTEDVALUE('Products'[ProductID])
VAR RankingTable = 
    CALCULATETABLE(
        ADDCOLUMNS(
            SUMMARIZE(
                'Sales',
                'Products'[ProductID],
                "TotalSales", SUM('Sales'[Amount]),
                "ProfitMargin", AVERAGE('Sales'[ProfitMargin])
            ),
            "RankScore", [TotalSales] + [ProfitMargin] / 1000000 -- Small weight for tiebreaker
        ),
        ALLSELECTED('Products'), -- Respect slicer filters
        ALLSELECTED('Date')
    )
RETURN
    RANKX(
        RankingTable,
        [RankScore],
        CALCULATE(
            SUM('Sales'[Amount]) + AVERAGE('Sales'[ProfitMargin]) / 1000000,
            'Products'[ProductID] = CurrentProduct
        ),
        DESC,
        Dense
    )
</xaiArtifact>

**Explanation**:
- `SUMMARIZE` creates a table with products, their total sales, and average profit margin.
- `ADDCOLUMNS` adds a composite score for ranking, using a small weight for profit margin to break ties.
- `RANKX` ranks products based on the composite score, respecting slicer filters via `ALLSELECTED`.
- The `Dense` option ensures consecutive ranks for ties.
- **Validation**: Test in a table visual with region and date slicers. Verify that products with equal sales are ranked by profit margin.

---

### 4. Advanced: Implementing Row-Level Security (RLS) with Dynamic Hierarchy
**Question**: Implement RLS in a Power BI model where users see sales data only for their subordinates in a dynamic organizational hierarchy (Employee -> Manager -> Director). The hierarchy is stored in a table updated daily.

**Answer**:
RLS requires a hierarchy table (e.g., `EmployeeHierarchy`) with columns like `EmployeeID`, `ManagerID`, and `Level`. Use DAX to filter data based on the logged-in user’s email and their subordinates.

1. **Data Model**: Create a table `EmployeeHierarchy` with columns `EmployeeID`, `ManagerID`, `Level`, and `Email`.
2. **RLS Role**: Define an RLS role in Power BI Desktop using DAX to filter based on the user’s email (`USERPRINCIPALNAME()`).
3. **Path Calculation**: Use `PATH` and `PATHCONTAINS` to identify subordinates.

<xaiArtifact artifact_id="f707260d-6bf6-4805-b9d4-db0e983fe964" artifact_version_id="6484d1d6-8947-4722-b99f-5451813e0c5e" title="RLSRoleDAX.txt" contentType="text/plain">
[Email] = USERPRINCIPALNAME() || 
PATHCONTAINS(
    LOOKUPVALUE(
        EmployeeHierarchy[Path],
        EmployeeHierarchy[Email], USERPRINCIPALNAME()
    ),
    EmployeeHierarchy[EmployeeID]
)
</xaiArtifact>

**Explanation**:
- The `EmployeeHierarchy` table includes a `Path` column (e.g., `1|2|3` for an employee under manager 2 under director 1), created using `PATH(EmployeeID, ManagerID)`.
- The RLS filter checks if the logged-in user’s email matches the `Email` column or if their `Path` contains the current `EmployeeID`.
- **Setup**: In Power BI Desktop, create a role under “Manage Roles,” apply the DAX filter to the `EmployeeHierarchy` table, and relate it to the `Sales` table via `EmployeeID`.
- **Validation**: Test using “View As” in Power BI Desktop with different user emails. Ensure users only see data for their subordinates and that updates to the hierarchy table reflect correctly.

---

### 5. Medium: Conditional Formatting in a Matrix
**Question**: How would you apply conditional formatting to a matrix visual to highlight cells where sales exceed a dynamic threshold stored in a configuration table?

**Answer**:
Use a DAX measure to compare sales against thresholds in a configuration table (e.g., `Thresholds` with columns `Category` and `ThresholdValue`). Apply the measure in Power BI’s conditional formatting settings.

<xaiArtifact artifact_id="efb51e68-f9d3-4b40-82e3-b03eb91c9aa5" artifact_version_id="2deb792e-9147-4961-b875-528129470bd9" title="ConditionalFormattingDAX.txt" contentType="text/plain">
SalesThresholdColor = 
VAR CurrentCategory = SELECTEDVALUE('Products'[Category])
VAR CurrentSales = SUM('Sales'[Amount])
VAR Threshold = 
    LOOKUPVALUE(
        Thresholds[ThresholdValue],
        Thresholds[Category], CurrentCategory,
        0
    )
RETURN
    IF(
        CurrentSales > Threshold,
        "Green",
        "Red"
    )
</xaiArtifact>

**Explanation**:
- `LOOKUPVALUE` retrieves the threshold for the current product category.
- The measure returns “Green” if sales exceed the threshold, else “Red.”
- **Setup**: In the matrix visual, select the sales field, go to “Conditional Formatting” -> “Background Color,” and use the measure with a field value rule (Green for “Green,” Red for “Red”).
- **Validation**: Verify that cells change color based on the `Thresholds` table values. Update the table and refresh to ensure dynamic updates.

---

### Notes:
- **Testing**: Each solution can be tested in Power BI Desktop. For DAX measures, use visuals like tables or line charts. For Power Query, check refresh times in the Query Editor. For RLS, use the “View As” feature.
- **Scalability**: The solutions are designed for large datasets (e.g., millions of rows) with performance in mind (e.g., query folding, optimized DAX).

- **Environment**: These assume a standard Power BI setup with a `Date` table, `Sales` table (columns: `SaleID`, `ProductID`, `CustomerID`, `SaleDate`, `Amount`, `ProfitMargin`), `Products` table (columns: `ProductID`, `Category`), and other relevant tables as described.

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


