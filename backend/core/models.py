from pydantic import BaseModel, Field
from typing import List

class Property(BaseModel):
    property: str = Field(..., description="Unique property identifier")
    cost: int
    landValue: int
    renovation: int
    loanClosingCOst: int
    ownerCount: int
    purchaseDate: str
    propMgmgtComp: str

class CompanyRecord(BaseModel):
    companyname: str = Field(..., description="Unique company name")
    rentPercentage: int

class BankAccountRecord(BaseModel):
    bankaccountname: str = Field(..., description="Unique bank account name")
    bankname: str

class GroupRecord(BaseModel):
    groupname: str = Field(..., description="Unique group name")
    propertylist: List[str]

class OwnerRecord(BaseModel):
    name: str = Field(..., description="Owner name")
    bankaccounts: List[str] = []
    properties: List[str] = []
    companies: List[str] = []

class TaxCategoryRecord(BaseModel):
    category: str = Field(..., description="Tax category name")

class TransactionTypeRecord(BaseModel):
    transactiontype: str = Field(..., description="Transaction type name")
