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

