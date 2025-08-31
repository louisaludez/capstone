### Utility: role_required

Source: `globals/decorator.py`

Signature:
`role_required(required_role: str) -> callable`

Behavior:
- Enforces that the current user is authenticated and has `request.user.role == required_role`.
- Raises `PermissionDenied` if the role check fails.

Example:
```python
from globals import decorator

@decorator.role_required('personnel')
def dashboard(request):
    ...
```
