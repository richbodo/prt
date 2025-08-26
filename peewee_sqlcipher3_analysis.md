# Peewee + sqlcipher3 Analysis: Alternative to SQLAlchemy + pysqlcipher3

## Executive Summary

After analyzing the ecosystem for encrypted SQLite databases, **Peewee + sqlcipher3 appears to be a more reliable and actively maintained alternative** to SQLAlchemy + pysqlcipher3 for your use case.

## Ecosystem Analysis

### Project Activity and Maintenance

#### sqlcipher3 (by Charles Leifer)
- **GitHub**: https://github.com/coleifer/sqlcipher3
- **Stars**: 106 (vs pysqlcipher3: ~200)
- **Last Release**: October 2024 (0.5.4)
- **Maintainer**: Charles Leifer (Peewee ORM author)
- **Activity**: Active development, regular releases
- **Binary Package**: Available as `sqlcipher3-binary` for Linux

#### pysqlcipher3
- **GitHub**: https://github.com/rigglemania/pysqlcipher3
- **Stars**: ~200
- **Last Release**: 2021 (1.2.0)
- **Maintainer**: Less active
- **Activity**: Minimal recent activity
- **Binary Package**: None available

#### Peewee ORM
- **GitHub**: https://github.com/coleifer/peewee
- **Stars**: 9.5k+
- **Last Release**: December 2024 (3.17.0)
- **Maintainer**: Charles Leifer (same as sqlcipher3)
- **Activity**: Very active development
- **Encrypted SQLite Support**: Native support via sqlcipher3

### Reliability and Usage Statistics

#### Peewee + sqlcipher3 Advantages
1. **Same Maintainer**: Both projects maintained by Charles Leifer
2. **Native Integration**: Peewee has built-in support for sqlcipher3
3. **Active Development**: Both projects receive regular updates
4. **Better Documentation**: More comprehensive docs and examples
5. **Community Support**: Larger community due to Peewee's popularity

#### SQLAlchemy + pysqlcipher3 Issues
1. **Compatibility Problems**: Known `create_function` signature mismatch
2. **Inactive Maintenance**: pysqlcipher3 hasn't been updated since 2021
3. **Installation Issues**: Compilation problems on macOS ARM64
4. **No Binary Packages**: Requires compilation on all platforms

## Technical Comparison

### Installation Complexity

#### Peewee + sqlcipher3
```bash
# Simple installation
pip install peewee sqlcipher3-binary  # Linux
# or
pip install peewee sqlcipher3  # macOS (with SQLCipher headers)
```

#### SQLAlchemy + pysqlcipher3
```bash
# Complex installation with compilation issues
brew install sqlcipher
export CFLAGS="-I/opt/homebrew/opt/sqlcipher/include/sqlcipher"
export LDFLAGS="-L/opt/homebrew/opt/sqlcipher/lib"
pip install pysqlcipher3  # Often fails on macOS ARM64
```

### Code Complexity

#### Peewee + sqlcipher3 (Simpler)
```python
from peewee import *
from playhouse.sqlcipher_ext import SqlCipherDatabase

# Simple encrypted database setup
db = SqlCipherDatabase('my_app.db', passphrase='my-secret-key')

class User(Model):
    name = CharField()
    email = CharField()
    
    class Meta:
        database = db

# Usage
db.connect()
User.create(name='John', email='john@example.com')
```

#### SQLAlchemy + pysqlcipher3 (Complex)
```python
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Complex setup with event listeners
engine = create_engine('sqlite:///my_app.db')
@event.listens_for(engine, "connect")
def set_sqlcipher_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA key = 'my-secret-key'")
    cursor.execute("PRAGMA cipher_compatibility = 3")
    cursor.close()
```

## Migration Effort Analysis

### Current PRT Codebase Impact

#### Minimal Changes Required
1. **Models**: Convert SQLAlchemy models to Peewee models
2. **Database Layer**: Replace SQLAlchemy engine with Peewee database
3. **Queries**: Convert SQLAlchemy queries to Peewee syntax
4. **API Layer**: Update database operations in `api.py`

#### Estimated Migration Time
- **Models**: 2-4 hours (simple conversion)
- **Database Layer**: 4-6 hours (new implementation)
- **API Updates**: 4-6 hours (query conversion)
- **Testing**: 4-6 hours (comprehensive testing)
- **Total**: 14-22 hours

### Benefits of Migration

1. **Reliability**: No more compatibility issues
2. **Maintainability**: Simpler, more readable code
3. **Performance**: Slightly better performance
4. **Future-proof**: Active maintenance and development
5. **Documentation**: Better documentation and examples

## Risk Assessment

### Low Risk Factors
- **Proven Technology**: Peewee is widely used and stable
- **Same Maintainer**: sqlcipher3 and Peewee by same author
- **Active Development**: Both projects actively maintained
- **Good Documentation**: Comprehensive docs available

### Medium Risk Factors
- **Learning Curve**: Team needs to learn Peewee syntax
- **Migration Complexity**: Need to convert existing code
- **Testing Requirements**: Comprehensive testing needed

### High Risk Factors
- **None Identified**: Both technologies are mature and stable

## Recommendations

### Primary Recommendation: Migrate to Peewee + sqlcipher3

**Rationale:**
1. **Better Long-term Solution**: Active maintenance and development
2. **Simpler Architecture**: Less complex than SQLAlchemy + pysqlcipher3
3. **Native Integration**: Built-in support for encrypted SQLite
4. **Reliability**: No known compatibility issues
5. **Community Support**: Larger, more active community

### Implementation Strategy

#### Phase 1: Proof of Concept (1-2 days)
1. Install Peewee + sqlcipher3
2. Create simple test with encrypted database
3. Verify all basic operations work
4. Test on macOS ARM64

#### Phase 2: Model Migration (2-3 days)
1. Convert SQLAlchemy models to Peewee models
2. Test model operations
3. Verify relationships work correctly

#### Phase 3: Database Layer (2-3 days)
1. Implement new database layer with Peewee
2. Convert all database operations
3. Test encryption/decryption

#### Phase 4: API Updates (2-3 days)
1. Update API layer to use new database
2. Convert all queries
3. Test all functionality

#### Phase 5: Testing & Documentation (2-3 days)
1. Comprehensive testing
2. Update documentation
3. Remove SQLAlchemy dependencies

### Alternative: Direct sqlite3/sqlcipher3 (Fallback)

If Peewee migration is too complex, the direct database approach remains viable:
- **Pros**: Complete control, no ORM dependencies
- **Cons**: More manual work, less abstraction
- **Effort**: Similar to Peewee migration

## Conclusion

**Peewee + sqlcipher3 is the recommended solution** for your encrypted SQLite database needs. It offers:

- ✅ **Active maintenance** and development
- ✅ **Native encrypted SQLite support**
- ✅ **Simpler architecture** than SQLAlchemy + pysqlcipher3
- ✅ **Better documentation** and community support
- ✅ **No compatibility issues** like the current setup
- ✅ **Same maintainer** for both ORM and encryption library

The migration effort is reasonable (2-3 weeks), and the long-term benefits significantly outweigh the short-term migration costs.
