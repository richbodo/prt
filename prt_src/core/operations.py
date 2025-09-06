"""Main operations orchestrator for PRT core business logic."""

from typing import Any
from typing import Dict
from typing import List

from .contacts import ContactOperations
from .database import DatabaseOperations
from .relationships import RelationshipOperations
from .search import SearchOperations


class Operations:
    """Central orchestrator for all business operations.

    This class provides a unified interface to all core operations,
    making it easy for any UI layer (CLI, Textual, Flet) to access
    business logic without dealing with implementation details.
    """

    def __init__(self, api):
        """Initialize with API instance and create sub-operations.

        Args:
            api: PRTAPI instance for database access
        """
        self.api = api

        # Initialize sub-operation handlers
        self.contacts = ContactOperations(api)
        self.relationships = RelationshipOperations(api)
        self.search = SearchOperations(api)
        self.database = DatabaseOperations(api)

    def validate_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validates parameters before operations.

        Args:
            operation: Name of the operation to validate
            params: Parameters to validate

        Returns:
            Dict with validation results
        """
        errors = []
        warnings = []

        # Contact operations validation
        if operation == "create_relationship":
            if not params.get("from_id"):
                errors.append("from_id is required")
            if not params.get("to_id"):
                errors.append("to_id is required")
            if not params.get("type_key"):
                errors.append("type_key is required")
            if params.get("from_id") == params.get("to_id"):
                errors.append("Cannot create relationship with same contact")

        elif operation == "search":
            if not params.get("query"):
                warnings.append("Empty search query will return no results")
            elif len(params.get("query", "")) < 2:
                warnings.append("Short search queries may return many results")

        elif operation == "restore_backup":
            if not params.get("backup_id"):
                errors.append("backup_id is required")

        elif operation == "list_contacts":
            page = params.get("page", 0)
            if page < 0:
                errors.append("Page number must be non-negative")
            page_size = params.get("page_size", 20)
            if page_size < 1:
                errors.append("Page size must be at least 1")
            elif page_size > 100:
                warnings.append("Large page sizes may impact performance")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def execute_batch(self, operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Executes multiple operations in sequence.

        Args:
            operations: List of operation dictionaries with 'type' and 'params'

        Returns:
            List of results for each operation
        """
        results = []

        for op in operations:
            op_type = op.get("type")
            params = op.get("params", {})

            try:
                # Validate first
                validation = self.validate_operation(op_type, params)
                if not validation["valid"]:
                    results.append(
                        {"success": False, "operation": op_type, "errors": validation["errors"]}
                    )
                    continue

                # Execute operation based on type
                result = self._execute_single_operation(op_type, params)
                results.append(result)

            except Exception as e:
                results.append({"success": False, "operation": op_type, "error": str(e)})

        return results

    def _execute_single_operation(self, op_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single operation.

        Args:
            op_type: Type of operation
            params: Operation parameters

        Returns:
            Operation result
        """
        # Contact operations
        if op_type == "list_contacts":
            return self.contacts.list_contacts(**params)
        elif op_type == "search_contacts":
            results = self.contacts.search_contacts(**params)
            return {"success": True, "results": results}
        elif op_type == "get_contact_details":
            result = self.contacts.get_contact_details(**params)
            return {"success": result is not None, "data": result}

        # Relationship operations
        elif op_type == "create_relationship":
            return self.relationships.create_relationship(**params)
        elif op_type == "delete_relationship":
            return self.relationships.delete_relationship(**params)
        elif op_type == "list_relationship_types":
            types = self.relationships.list_relationship_types()
            return {"success": True, "types": types}

        # Search operations
        elif op_type == "unified_search":
            return self.search.unified_search(**params)
        elif op_type == "search_by_tag":
            results = self.search.search_by_tag(**params)
            return {"success": True, "results": results}

        # Database operations
        elif op_type == "create_backup":
            return self.database.create_backup(**params)
        elif op_type == "restore_backup":
            return self.database.restore_backup(**params)
        elif op_type == "database_status":
            status = self.database.get_database_status()
            return {"success": True, "status": status}

        else:
            return {"success": False, "error": f"Unknown operation type: {op_type}"}

    def get_operation_metadata(self, op_type: str) -> Dict[str, Any]:
        """Get metadata about an operation.

        Args:
            op_type: Type of operation

        Returns:
            Dict with operation metadata
        """
        metadata = {
            "list_contacts": {
                "description": "List contacts with pagination",
                "params": {
                    "page": {"type": "int", "default": 0, "required": False},
                    "page_size": {"type": "int", "default": 20, "required": False},
                },
                "returns": "Paginated contact list",
            },
            "create_relationship": {
                "description": "Create a relationship between two contacts",
                "params": {
                    "from_id": {"type": "int", "required": True},
                    "to_id": {"type": "int", "required": True},
                    "type_key": {"type": "str", "required": True},
                    "start_date": {"type": "date", "required": False},
                },
                "returns": "Success status with relationship details",
            },
            "unified_search": {
                "description": "Search across all entity types",
                "params": {"query": {"type": "str", "required": True}},
                "returns": "Results grouped by entity type",
            },
            "create_backup": {
                "description": "Create a database backup with comment",
                "params": {"comment": {"type": "str", "default": "", "required": False}},
                "returns": "Backup information",
            },
        }

        return metadata.get(
            op_type, {"description": "Unknown operation", "params": {}, "returns": "Unknown"}
        )

    def get_available_operations(self) -> List[str]:
        """Get list of all available operations.

        Returns:
            List of operation names
        """
        return [
            # Contact operations
            "list_contacts",
            "get_contact_details",
            "search_contacts",
            "get_contacts_by_letter",
            # Relationship operations
            "list_relationship_types",
            "create_relationship",
            "delete_relationship",
            "get_contact_relationships",
            "find_relationships_between",
            # Search operations
            "unified_search",
            "search_by_tag",
            "search_by_note",
            "search_by_relationship_type",
            # Database operations
            "database_status",
            "list_backups",
            "create_backup",
            "restore_backup",
            "get_backup_details",
        ]
