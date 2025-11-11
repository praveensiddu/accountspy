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
    statement_location: str = ''
    abbreviation: str = ''

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


class InheritRuleRecord(BaseModel):
    bankaccountname: str = Field(..., description="Bank account name")
    tax_category: str = Field('', description="Tax category")
    property: str = Field('', description="Property id")
    group: str = Field('', description="Optional group name")
    otherentity: str = Field('', description="Other entity (e.g., vendor/payee)")


class ClassifyRuleRecord(BaseModel):
    bankaccountname: str = Field(..., description="Bank account name")
    transaction_type: str = Field(..., description="Transaction type")
    pattern_match_logic: str = Field(..., description="Pattern matching expression")
    tax_category: str = Field(..., description="Tax category")
    property: str = Field(..., description="Property id")
    group: str = Field('', description="Optional group name")
    company: str = Field('', description="Optional company name")
    otherentity: str = Field(..., description="Other entity (e.g., vendor/payee)")
    order: int = Field(0, description="Order/priority for rule evaluation")

    class Config:
        extra = 'forbid'


class ClassifyRuleRecordOut(ClassifyRuleRecord):
    usedcount: int = Field(0, description="Number of times this rule matched in the latest classification run")
