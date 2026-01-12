# E2E Test: SQL Injection Protection

Test the application's protection against SQL injection attacks.

## User Story

As a user  
I want to be protected from SQL injection attacks when using the query interface  
So that my data remains secure and the database integrity is maintained

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. Clear the query input
4. Enter: "DROP TABLE users;"
5. Take a screenshot of the malicious query input
6. Click Query button
7. **Verify** an error message appears containing "Security error" or similar
8. Take a screenshot of the security error
9. **Verify** the users table still exists in Available Tables section
10. Take a screenshot showing the tables are intact

## Success Criteria
- SQL injection attempt is blocked
- Appropriate security error message is displayed
- No damage to the database
- Tables remain intact
- Query input accepts the malicious text
- 4 screenshots are taken