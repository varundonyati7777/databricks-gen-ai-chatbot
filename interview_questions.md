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
Below is a curated list of advanced SQL interview questions, including scenario-based questions, designed to test deep knowledge of SQL concepts such as complex joins, window functions, query optimization, and database design. Each question includes a detailed answer with SQL code wrapped in `<xaiArtifact>` tags where applicable, ensuring practical and reusable solutions. These questions are suitable for candidates preparing for senior data analyst, data engineer, or database developer roles.

---

### 1. Advanced: Optimizing a Slow Query with Multiple Joins
**Scenario**: You are a data engineer at a retail company. The following SQL query, which retrieves sales data with product and customer details, takes 10 seconds to run on a database with 10M sales records, 1M products, and 500K customers. The tables have appropriate primary keys, but performance is poor due to large data volumes and frequent filtering by date and region.

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
```

**Question**: How would you optimize this query to run faster? Provide specific steps, including indexing strategies, query rewriting, and any database configuration changes.

**Answer**:
To optimize the query, consider indexing, query rewriting, and database statistics. Here’s a step-by-step approach:

1. **Analyze Execution Plan**: Use the database’s query execution plan (e.g., `EXPLAIN PLAN` in Oracle, `EXPLAIN ANALYZE` in PostgreSQL, or `SHOW PLAN` in SQL Server) to identify bottlenecks, such as full table scans or inefficient joins.
2. **Create Indexes**:
   - Create a composite index on `Sales(SaleDate, CustomerID, ProductID)` to support the `WHERE` clause and joins.
   - Create an index on `Customers(Region, CustomerID)` to optimize the region filter.
   - Ensure `Products(ProductID)` has a primary key index (typically exists by default).
3. **Rewrite the Query**: Push down filters to reduce the dataset before joining, and consider partitioning for large tables.
4. **Partitioning**: If `Sales` is frequently filtered by `SaleDate`, partition the table by year or month to reduce scanned rows.
5. **Update Statistics**: Ensure the database’s statistics are up-to-date to help the query optimizer choose the best plan.
6. **Consider Materialized Views**: For frequently accessed data, create a materialized view with pre-aggregated results.

<xaiArtifact artifact_id="589f841f-28ec-4162-8dba-8be54bc7bbe4" artifact_version_id="c8dcdc46-2ddf-43f1-ad35-958c3340cddc" title="OptimizedSalesQuery.sql" contentType="text/sql">
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
</xaiArtifact>

**Explanation**:
- **Indexes**: The composite index on `Sales` covers the `WHERE` and `JOIN` conditions, reducing lookup time. The `Customers` index speeds up the region filter.
- **Join Order**: Explicitly filter `Customers` by `Region` before joining to reduce the number of rows processed.
- **Partitioning**: If the database supports it (e.g., PostgreSQL, SQL Server), partition `Sales` by `SaleDate` (e.g., yearly partitions) to scan only relevant data.
- **Validation**: Run `EXPLAIN ANALYZE` to confirm index usage and reduced scan time. Compare execution time before and after optimization.

---

### 2. Advanced: Window Functions for Running Totals
**Scenario**: You work for a financial company analyzing daily transactions. The `Transactions` table contains columns `AccountID`, `TransactionDate`, `Amount`, and `TransactionType` (Deposit or Withdrawal). You need to calculate the running balance for each account over time, ordered by transaction date, and flag transactions where the balance goes below zero.

**Question**: Write a SQL query to compute the running balance and flag negative balances. How would you handle ties in `TransactionDate` (e.g., multiple transactions on the same day)?

**Answer**:
Use a window function with `SUM` to calculate the running balance and a `CASE` statement to flag negative balances. To handle ties in `TransactionDate`, include a unique column (e.g., `TransactionID`) in the `ORDER BY` clause of the window function.

<xaiArtifact artifact_id="aec472ab-5b25-4027-9afa-8747c97176b3" artifact_version_id="5b38eca2-beed-403c-b71f-e86039b3a3fc" title="RunningBalanceQuery.sql" contentType="text/sql">
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
</xaiArtifact>

**Explanation**:
- **Window Function**: `SUM(...) OVER (PARTITION BY AccountID ORDER BY TransactionDate, TransactionID)` calculates the running total of `Amount` (positive for Deposits, negative for Withdrawals) per account, ordered by date and `TransactionID` to break ties.
- **CASE Statement**: Converts `Amount` to positive or negative based on `TransactionType`.
- **Flagging**: The second `CASE` checks if the running balance is negative to flag overdrafts.
- **Validation**: Test with a small dataset (e.g., one account with multiple transactions on the same day) to ensure the running balance accumulates correctly and ties are resolved consistently.

---

### 3. Advanced: Recursive CTE for Organizational Hierarchy
**Scenario**: You are designing a database for an HR system with an `Employees` table containing `EmployeeID`, `Name`, `ManagerID`, and `Department`. You need to generate a report showing the full organizational hierarchy (e.g., CEO -> Managers -> Employees) with each employee’s level in the hierarchy.

**Question**: Write a SQL query using a recursive CTE to display the hierarchy, including the employee’s name, manager’s name, and hierarchy level. How would you handle cases where `ManagerID` is NULL (e.g., for the CEO)?

**Answer**:
Use a recursive CTE to traverse the hierarchy, starting with employees who have no manager (`ManagerID IS NULL`) and recursively joining to find subordinates. Include a level counter to track depth.

<xaiArtifact artifact_id="a3792f91-ccd0-4d9a-bb09-523741bd7c04" artifact_version_id="70b2b3de-7cc9-4298-a3d2-fb48b8e9d80a" title="HierarchyQuery.sql" contentType="text/sql">
WITH EmployeeHierarchy AS (
    -- Anchor: Start with top-level employees (e.g., CEO)
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
</xaiArtifact>

**Explanation**:
- **Anchor**: Selects top-level employees (`ManagerID IS NULL`) as the starting point, setting `HierarchyLevel` to 1.
- **Recursive Part**: Joins `Employees` to the CTE where `ManagerID` matches `EmployeeID`, incrementing `HierarchyLevel`.
- **ManagerName**: Joins again to `Employees` to get the manager’s name.
- **IndentedName**: Uses `REPEAT` to indent names for readability (database-specific; e.g., use `REPLICATE` in SQL Server).
- **Handling NULL**: The `WHERE ManagerID IS NULL` clause ensures the CEO or top-level employees are included.
- **Validation**: Test with a small hierarchy (e.g., CEO -> Manager -> Employee) to verify levels and manager names. Check for cycles (e.g., `ManagerID` referencing a subordinate) and add constraints if needed.

---

### 4. Advanced: Pivoting Data with Dynamic Columns
**Scenario**: You work for an e-commerce company with a `Sales` table containing `SaleID`, `SaleDate`, `Category`, and `Revenue`. The company wants a report showing revenue by category as columns, with months as rows, but the categories are dynamic (new categories may be added).

**Question**: Write a SQL query to create a dynamic pivot table showing revenue by category for each month. How would you handle the dynamic nature of categories?

**Answer**:
Use dynamic SQL to generate a pivot table, as the categories are unknown at query time. First, retrieve distinct categories, then construct a dynamic `PIVOT` query (or use conditional aggregation for databases without `PIVOT`).

<xaiArtifact artifact_id="41eec310-8b27-41d2-80d1-7c43ac674abd" artifact_version_id="a91533ed-c84c-42af-a201-3788fa7a1945" title="DynamicPivotQuery.sql" contentType="text/sql">
DECLARE @Columns NVARCHAR(MAX), @SQL NVARCHAR(MAX);

-- Get distinct categories as columns
SET @Columns = (
    SELECT STRING_AGG(QUOTENAME(Category), ', ')
    FROM (SELECT DISTINCT Category FROM Sales) AS Categories
);

-- Dynamic SQL for pivot
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

-- Execute dynamic SQL
EXEC sp_executesql @SQL;
</xaiArtifact>

**Explanation**:
- **Dynamic Columns**: `STRING_AGG(QUOTENAME(Category), ', ')` concatenates distinct categories into a comma-separated list (e.g., `[Electronics], [Clothing]`). Use `GROUP_CONCAT` in MySQL or a loop in PostgreSQL if needed.
- **PIVOT**: The `PIVOT` operator (SQL Server) rotates `Category` into columns, summing `Revenue` for each month.
- **Formatting**: `FORMAT(SaleDate, 'yyyy-MM')` groups by month.
- **Alternative for Non-PIVOT Databases**: Use conditional aggregation (e.g., `SUM(CASE WHEN Category = 'Electronics' THEN Revenue END)`).
- **Validation**: Run the query and verify that new categories appear as columns after adding to the `Sales` table. Check monthly totals against raw data.

---

### 5. Advanced: Detecting and Resolving Deadlocks
**Scenario**: You are a database administrator for a banking system. Users report intermittent errors due to deadlocks when multiple transactions update the `Accounts` and `Transactions` tables concurrently (e.g., transferring funds between accounts). The tables are indexed, but deadlocks persist.

**Question**: How would you identify the cause of the deadlocks and resolve them? Provide a sample transaction script and explain preventive measures.

**Answer**:
Deadlocks occur when two or more transactions block each other, each waiting for a resource the other holds. To identify and resolve:

1. **Identify Deadlocks**:
   - Enable deadlock logging (e.g., SQL Server: `DBCC TRACEON(1222, -1)`; PostgreSQL: `log_min_messages = debug5`).
   - Use system views (e.g., SQL Server: `sys.dm_tran_locks`, `sys.dm_exec_requests`) to capture deadlock graphs.
2. **Analyze Deadlock Graph**: Identify the tables, indexes, and statements involved (e.g., `UPDATE Accounts` vs. `INSERT Transactions`).
3. **Resolve Deadlocks**:
   - **Consistent Lock Order**: Ensure transactions access tables in the same order (e.g., always lock `Accounts` before `Transactions`).
   - **Reduce Transaction Scope**: Minimize the duration of transactions by preparing data outside the transaction.
   - **Use Optimistic Locking**: Implement row versioning or retry logic.
   - **Indexing**: Ensure indexes support `WHERE` and `JOIN` clauses to reduce lock contention.

<xaiArtifact artifact_id="c6124947-0cb6-44a8-a148-581f01614ed8" artifact_version_id="c7fec8be-bdf7-4cc3-b687-be2438cd7313" title="FundTransferTransaction.sql" contentType="text/sql">
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
    -- Log error or retry
    DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
    INSERT INTO ErrorLog (ErrorMessage, ErrorDate)
    VALUES (@ErrorMessage, GETDATE());
END CATCH;
</xaiArtifact>

**Explanation**:
- **Consistent Order**: Updates `Accounts` before inserting into `Transactions` to avoid deadlocks with other transactions.
- **Error Handling**: Uses `TRY-CATCH` to rollback on deadlock errors and log them.
- **Preventive Measures**: Add retry logic (e.g., loop with `TRY-CATCH` in SQL Server) or use `WITH (UPDLOCK, HOLDLOCK)` to acquire locks early.
- **Validation**: Simulate concurrent transfers using multiple sessions and monitor deadlock logs to ensure resolution.

---

### Notes:
- **Testing**: Test queries in a development database with sample data. For optimization questions, use execution plans. For deadlocks, simulate concurrent transactions.
- **Database-Specific**: The solutions assume SQL Server syntax (e.g., `PIVOT`, `STRING_AGG`). For MySQL, PostgreSQL, or Oracle, adjustments may be needed (e.g., `GROUP_CONCAT` in MySQL, `LATERAL` joins in PostgreSQL).
- **Scalability**: Solutions are designed for large datasets, with indexing and partitioning recommendations.
- **Visualizations**: If you want a chart (e.g., revenue by category from the pivot query), provide sample data and a chart type, and I can generate a Chart.js visualization.

