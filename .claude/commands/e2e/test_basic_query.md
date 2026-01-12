# E2E Test: Basic Query Execution

Test basic query functionality in the Natural Language SQL Interface application.

## User Story

As a user  
I want to query my data using natural language  
So that I can access information without writing SQL

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. **Verify** the page title is "Natural Language SQL Interface"
4. **Verify** core UI elements are present:
   - Query input textbox
   - Query button
   - Upload Data button
   - Available Tables section

5. Enter the query: "Show me all users from the users table"
6. Take a screenshot of the query input
7. Click the Query button
8. **Verify** the query results appear
9. **Verify** the SQL translation is displayed (should contain "SELECT * FROM users")
10. Take a screenshot of the SQL translation
11. **Verify** the results table contains data
12. Take a screenshot of the results
13. Click "Hide" button to close results

## Success Criteria
- Query input accepts text
- Query button triggers execution
- Results display correctly
- SQL translation is shown
- Hide button works
- 3 screenshots are taken
