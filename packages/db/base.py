from sqlmodel import SQLModel


class BaseModel(SQLModel):
    """
    Base model for all SafeFlow tables and DTOs.
    Extend this in your table models, e.g.:

        class Transaction(BaseModel, table=True):
            ...
    """
    pass
