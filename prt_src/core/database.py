"""Database and backup operations."""

from typing import Any
from typing import Dict
from typing import Optional


class DatabaseOperations:
    """Handles database status, backup, and restore operations."""

    def __init__(self, api):
        """Initialize with API instance.

        Args:
            api: PRTAPI instance for database access
        """
        self.api = api

    def get_database_status(self) -> Dict[str, Any]:
        """Returns health, table counts, file size.

        Combines status, test, and stats for Issue #71.

        Returns:
            Dict with comprehensive database status
        """
        try:
            # Test connection
            connection_ok = False
            try:
                self.api.db.test_connection()
                connection_ok = True
            except Exception as conn_error:
                connection_error = str(conn_error)

            # Get database file info
            db_path = self.api.db.path
            db_size = 0
            if db_path.exists():
                db_size = db_path.stat().st_size

            # Get table counts
            contact_count = self.api.db.count_contacts()
            tag_count = len(self.api.list_all_tags())
            note_count = len(self.api.list_all_notes())

            # Get relationship counts
            relationship_count = 0
            rel_type_count = len(self.api.db.list_relationship_types())

            # Calculate relationships (approximate)
            try:
                all_contacts = self.api.list_all_contacts()
                for contact in all_contacts[:10]:  # Sample first 10 for performance
                    rels = self.api.db.get_contact_relationships(contact["id"])
                    relationship_count += len(rels)
                # Extrapolate
                if all_contacts[:10]:
                    relationship_count = (relationship_count * len(all_contacts)) // min(
                        10, len(all_contacts)
                    )
            except Exception:
                pass

            # Get backup info
            backups = self.api.get_backup_history()
            last_backup = backups[0] if backups else None

            return {
                "healthy": connection_ok,
                "connection_ok": connection_ok,
                "connection_error": connection_error if not connection_ok else None,
                "database_path": str(db_path),
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "counts": {
                    "contacts": contact_count,
                    "tags": tag_count,
                    "notes": note_count,
                    "relationships": relationship_count,
                    "relationship_types": rel_type_count,
                },
                "last_backup": (
                    {
                        "date": last_backup.get("created_at") if last_backup else None,
                        "comment": last_backup.get("comment") if last_backup else None,
                        "size_mb": (
                            round(last_backup.get("size", 0) / (1024 * 1024), 2)
                            if last_backup
                            else 0
                        ),
                    }
                    if last_backup
                    else None
                ),
                "backup_count": len(backups),
                "has_data": contact_count > 0,
            }

        except Exception as e:
            return {"healthy": False, "error": str(e), "counts": {}}

    def list_backups(self, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """Returns paginated backup list with metadata.

        Game save-style listing for Issue #71.

        Args:
            limit: Number of backups per page
            offset: Starting position

        Returns:
            Dict with backups and pagination info
        """
        try:
            # Get all backups
            all_backups = self.api.get_backup_history()
            total = len(all_backups)

            # Apply pagination
            backups = all_backups[offset : offset + limit]

            # Format for game-save style display
            formatted_backups = []
            for backup in backups:
                formatted_backups.append(
                    {
                        "id": backup.get("id"),
                        "filename": backup.get("filename"),
                        "comment": backup.get("comment", "No description"),
                        "created_at": backup.get("created_at"),
                        "size_bytes": backup.get("size", 0),
                        "size_mb": round(backup.get("size", 0) / (1024 * 1024), 2),
                        "is_auto": backup.get("is_auto", False),
                        "exists": backup.get("exists", True),
                        "schema_version": backup.get("schema_version"),
                    }
                )

            return {
                "success": True,
                "backups": formatted_backups,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total,
                "page": (offset // limit) + 1 if limit > 0 else 1,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "backups": [], "total": 0}

    def create_backup(self, comment: str = "") -> Dict[str, Any]:
        """Creates backup with user comment.

        Args:
            comment: User's description of the backup

        Returns:
            Dict with backup info
        """
        try:
            # Create backup with comment
            backup_info = self.api.create_backup_with_comment(comment=comment, auto=False)

            return {
                "success": True,
                "backup": {
                    "id": backup_info.get("id"),
                    "filename": backup_info.get("filename"),
                    "path": backup_info.get("path"),
                    "comment": backup_info.get("comment"),
                    "size_bytes": backup_info.get("size", 0),
                    "size_mb": round(backup_info.get("size", 0) / (1024 * 1024), 2),
                    "created_at": backup_info.get("created_at"),
                },
                "message": f"Backup created successfully: {backup_info.get('filename')}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def restore_backup(self, backup_id: int) -> Dict[str, Any]:
        """Restores from specific backup.

        Args:
            backup_id: ID of the backup to restore

        Returns:
            Dict with success/error status
        """
        try:
            # Validate backup exists
            backups = self.api.get_backup_history()
            backup = next((b for b in backups if b.get("id") == backup_id), None)

            if not backup:
                return {"success": False, "error": f"Backup with ID {backup_id} not found"}

            if not backup.get("exists", True):
                return {"success": False, "error": "Backup file no longer exists"}

            # Perform restore
            self.api.restore_from_backup(backup_id)

            return {
                "success": True,
                "message": f"Successfully restored from backup: {backup.get('comment', 'Unknown')}",
                "backup": backup,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_backup_details(self, backup_id: int) -> Optional[Dict[str, Any]]:
        """Returns full backup metadata.

        Args:
            backup_id: ID of the backup

        Returns:
            Dict with backup details or None
        """
        try:
            backups = self.api.get_backup_history()
            backup = next((b for b in backups if b.get("id") == backup_id), None)

            if not backup:
                return None

            # Add additional details
            return {
                "id": backup.get("id"),
                "filename": backup.get("filename"),
                "path": backup.get("path"),
                "comment": backup.get("comment", "No description"),
                "created_at": backup.get("created_at"),
                "size_bytes": backup.get("size", 0),
                "size_mb": round(backup.get("size", 0) / (1024 * 1024), 2),
                "is_auto": backup.get("is_auto", False),
                "exists": backup.get("exists", True),
                "schema_version": backup.get("schema_version"),
                "can_restore": backup.get("exists", True),
            }

        except Exception as e:
            return {"error": str(e)}

    def cleanup_auto_backups(self, keep_count: int = 5) -> Dict[str, Any]:
        """Clean up old automatic backups.

        Args:
            keep_count: Number of auto backups to keep

        Returns:
            Dict with cleanup results
        """
        try:
            # Use API's cleanup method
            self.api.cleanup_auto_backups(keep_count=keep_count)

            # Get current backup count
            backups = self.api.get_backup_history()
            auto_count = sum(1 for b in backups if b.get("is_auto", False))
            manual_count = len(backups) - auto_count

            return {
                "success": True,
                "message": f"Cleanup complete. Kept {keep_count} auto backups.",
                "current_counts": {
                    "auto": auto_count,
                    "manual": manual_count,
                    "total": len(backups),
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_database_info(self) -> Dict[str, Any]:
        """Get detailed database information.

        Returns:
            Dict with database details
        """
        try:
            from prt_src.schema_manager import SchemaManager

            schema_mgr = SchemaManager(self.api.db)
            current_version = schema_mgr.get_schema_version()

            return {
                "path": str(self.api.db.path),
                "exists": self.api.db.path.exists(),
                "schema_version": current_version,
                "current_schema": SchemaManager.CURRENT_VERSION,
                "needs_migration": current_version < SchemaManager.CURRENT_VERSION,
                "encrypted": False,  # Will be updated when encryption is implemented
            }
        except Exception as e:
            return {"error": str(e)}
