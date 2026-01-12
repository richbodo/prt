# E2E Test: Complex Query with Filtering

Test complex query capabilities with filtering conditions.

## User Story

As a user  
I want to query data using natural language with complex filtering conditions  
So that I can retrieve specific subsets of data without needing to write SQL

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. Clear the query input
4. Enter: "Show users older than 30 who live in cities starting with 'S'"
5. Take a screenshot of the query input
6. Click Query button
7. **Verify** results appear with filtered data
8. **Verify** the generated SQL contains WHERE clause
9. Take a screenshot of the SQL translation
10. Count the number of results returned
11. Take a screenshot of the filtered results
12. Click "Hide" button to close results
13. Take a screenshot of the final state

## Success Criteria
- Complex natural language is correctly interpreted
- SQL contains appropriate WHERE conditions
- Results are properly filtered
- No errors occur during execution
- Hide button works
- 5 screenshots are taken