# Experiment Delete Endpoint Permission Fix

## Issue Summary

The experiment delete endpoint had a critical design conflict in its permission validation mechanism. This caused validation errors when attempting to delete draft experiments, even when the user had proper permissions.

### Root Cause

The conflict stemmed from these contradictory requirements:

1. The `delete_experiment` endpoint used the `can_delete_experiment` dependency to check permissions
2. The `can_delete_experiment` dependency in turn used `get_experiment_access`, which relied on `get_experiment_by_key`
3. `get_experiment_by_key` enforced a validation that experiments must be in **ACTIVE** status, returning a 400 error for other statuses
4. However, the `delete_experiment` endpoint logic enforced a business rule that only experiments in **DRAFT** status can be deleted

This created an impossible situation where:
- To delete an experiment, it had to be in DRAFT status (endpoint requirement)
- But the permission check required it to be in ACTIVE status (dependency requirement)
- This resulted in "Inactive experiment" 400 errors when trying to delete draft experiments

## Implementation Fix

The solution eliminated the dependency chain conflict by:

1. **Removing** the `can_delete_experiment` dependency from the delete endpoint
2. **Adding** a required `experiment_key` query parameter
3. **Implementing** inline permission checks directly within the endpoint:
   - Retrieving the experiment directly from the database
   - Verifying `experiment_key` matches the `experiment_id` path parameter
   - Checking permissions (user must have DELETE permission)
   - Checking ownership (non-superusers must own the experiment)
   - Verifying experiment status (must be DRAFT)

### Code Changes

```python
@router.delete(
    "/{experiment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    # other parameters...
)
async def delete_experiment(
    experiment_id: UUID = Path(..., description="The ID of the experiment to delete"),
    experiment_key: str = Query(..., description="Key or ID of the experiment to delete (must match experiment_id)"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    cache_control: Dict[str, Any] = Depends(deps.get_cache_control),
) -> None:
    """Delete an experiment."""
    # Get experiment by ID
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )

    # Verify experiment_key matches experiment_id
    if str(experiment.id) != experiment_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="experiment_key does not match experiment_id"
        )

    # Check permission to delete experiment
    if not current_user.is_superuser:
        # User must be the owner
        if str(experiment.owner_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be the owner to delete this experiment",
            )

        # Check if user has permission to delete experiments
        if not check_permission(current_user, ResourceType.EXPERIMENT, Action.DELETE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=get_permission_error_message(ResourceType.EXPERIMENT, Action.DELETE),
            )

    # Additional check for experiment status for non-draft experiments
    if experiment.status != ExperimentStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete experiments that are not in DRAFT status",
        )

    # Delete experiment and handle cache...
```

### Documentation Updates

In addition to the implementation fix, documentation was updated in two places:

1. A warning was added to the `can_delete_experiment` dependency function:
```python
def can_delete_experiment(...):
    """
    Check if user can delete an experiment.

    WARNING: Do not use this dependency in the delete_experiment endpoint!
    There is a design conflict where this dependency chain requires ACTIVE experiments
    (via get_experiment_access → get_experiment_by_key) but the delete_experiment
    endpoint requires experiments to be in DRAFT status. Use inline permission checks
    in the delete_experiment endpoint instead.
    """
```

2. The project instructions were updated with clear guidelines about this special case.

## Testing Considerations

The test file `backend/tests/unit/api/v1/endpoints/test_experiment_permissions.py` was also updated to correctly expect:

- Status code 204 (No Content) for deleting DRAFT experiments (success case)
- Status code 403 (Forbidden) for attempting to delete non-DRAFT experiments
- Status code 403 (Forbidden) for users without proper permissions

## Lessons Learned

This fix highlights the importance of:

1. Being aware of dependency chains and how they can create conflicting validation requirements
2. Designing validation dependencies with flexibility for different usage contexts
3. Documenting special cases and exceptions to prevent reintroduction of the issue
4. Using inline permission checks when necessary, while still maintaining proper security validation
