from typing import Annotated
from fastapi import Depends
from app.core.security import get_current_user, verify_read_key, verify_write_key

# Aliases de dependencias para mayor legibilidad
CurrentUser = Annotated[dict, Depends(get_current_user)]
ReadKey = Annotated[str, Depends(verify_read_key)]
WriteKey = Annotated[str, Depends(verify_write_key)]
