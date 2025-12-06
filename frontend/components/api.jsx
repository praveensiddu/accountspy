const api = {
  async list() {
    const res = await fetch('/api/properties');
    if (!res.ok) throw new Error('Failed to fetch properties');
    return res.json();
  },
  async add(item) {
    const res = await fetch('/api/properties', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item),
    });
    if (!res.ok) {
      const msg = await res.text();
      throw new Error(msg || 'Failed to add property');
    }
    return res.json();
  },
  async remove(id) {
    const res = await fetch(`/api/properties/${encodeURIComponent(id)}`, { method: 'DELETE' });
    if (!res.ok && res.status !== 204) throw new Error('Failed to delete');
  },
  async companies() {
    const res = await fetch('/api/companies');
    if (!res.ok) throw new Error('Failed to fetch companies');
    return res.json();
  },
  async listCompanyRecords() {
    const res = await fetch('/api/company-records');
    if (!res.ok) throw new Error('Failed to fetch company records');
    return res.json();
  },
  async addCompanyRecord(item) {
    const res = await fetch('/api/company-records', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item),
    });
    if (!res.ok) {
      const msg = await res.text();
      throw new Error(msg || 'Failed to add company record');
    }
    return res.json();
  },
  async removeCompanyRecord(name) {
    const res = await fetch(`/api/company-records/${encodeURIComponent(name)}`, { method: 'DELETE' });
    if (!res.ok && res.status !== 204) throw new Error('Failed to delete company record');
  },
  async listBankaccounts() {
    const res = await fetch('/api/bankaccounts');
    if (!res.ok) throw new Error('Failed to fetch bank accounts');
    return res.json();
  },
  async addBankaccount(item) {
    const res = await fetch('/api/bankaccounts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async updateBankaccount(name, item) {
    const res = await fetch(`/api/bankaccounts/${encodeURIComponent(name)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async removeBankaccount(name) {
    const res = await fetch(`/api/bankaccounts/${encodeURIComponent(name)}`, { method: 'DELETE' });
    if (!res.ok && res.status !== 204) throw new Error('Failed to delete bank account');
  },
  async listGroups() {
    const res = await fetch('/api/groups');
    if (!res.ok) throw new Error('Failed to fetch groups');
    return res.json();
  },
  async addGroup(item) {
    const res = await fetch('/api/groups', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async removeGroup(name) {
    const res = await fetch(`/api/groups/${encodeURIComponent(name)}`, { method: 'DELETE' });
    if (!res.ok && res.status !== 204) throw new Error('Failed to delete group');
  },
  async listOwners() {
    const res = await fetch('/api/owners');
    if (!res.ok) throw new Error('Failed to fetch owners');
    return res.json();
  },
  async addOwner(item) {
    const res = await fetch('/api/owners', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async removeOwner(name) {
    const res = await fetch(`/api/owners/${encodeURIComponent(name)}`, { method: 'DELETE' });
    if (!res.ok && res.status !== 204) throw new Error('Failed to delete owner');
  },
  async listTaxCategories() {
    const res = await fetch('/api/tax-categories');
    if (!res.ok) throw new Error('Failed to fetch tax categories');
    return res.json();
  },
  async addTaxCategory(item) {
    const res = await fetch('/api/tax-categories', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(item),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async removeTaxCategory(category) {
    const res = await fetch(`/api/tax-categories/${encodeURIComponent(category)}`, { method: 'DELETE' });
    if (!res.ok && res.status !== 204) throw new Error('Failed to delete tax category');
  },
  async listTransactionTypes() {
    const res = await fetch('/api/transaction-types');
    if (!res.ok) throw new Error('Failed to fetch transaction types');
    return res.json();
  },
  async addTransactionType(item) {
    const res = await fetch('/api/transaction-types', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(item),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async removeTransactionType(tt) {
    const res = await fetch(`/api/transaction-types/${encodeURIComponent(tt)}`, { method: 'DELETE' });
    if (!res.ok && res.status !== 204) throw new Error('Failed to delete transaction type');
  },
  async listRentalSummary() {
    const res = await fetch('/api/rental-summary');
    if (!res.ok) throw new Error('Failed to fetch rental summary');
    return res.json();
  },
  async listRentTracker() {
    const res = await fetch('/api/rent-tracker');
    if (!res.ok) throw new Error('Failed to fetch rent tracker');
    return res.json();
  },
  async listCompanySummary() {
    const res = await fetch('/api/company-summary');
    if (!res.ok) throw new Error('Failed to fetch company summary');
    return res.json();
  },
  async listTransactions() {
    const res = await fetch('/api/transactions');
    if (!res.ok) throw new Error('Failed to fetch transactions');
    return res.json();
  },
  async saveTransactions(bankaccountname, rows) {
    const res = await fetch(`/api/transactions/${encodeURIComponent(bankaccountname)}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ rows }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async listClassifyRules() {
    const res = await fetch('/api/classify-rules');
    if (res.status === 404) return [];
    if (!res.ok) throw new Error('Failed to fetch classify rules');
    return res.json();
  },
  async addClassifyRule(item) {
    const res = await fetch('/api/classify-rules', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(item),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async removeClassifyRule(key) {
    const obj = (typeof key === 'object' && key !== null) ? key : { bankaccountname: key };
    const bankVal = obj.bankaccountname != null ? obj.bankaccountname : '';
    const qp = new URLSearchParams({
      bankaccountname: String(bankVal),
      transaction_type: obj.transaction_type || '',
      property: obj.property || '',
    }).toString();
    const res = await fetch(`/api/classify-rules?${qp}`, { method: 'DELETE' });
    if (!res.ok && res.status !== 204) throw new Error('Failed to delete classify rule');
  },
  async listBanks() {
    const res = await fetch('/api/banks');
    if (!res.ok) throw new Error('Failed to fetch banks config');
    return res.json();
  },
  async addBank(cfg) {
    const res = await fetch('/api/banks', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cfg),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async removeBank(name) {
    const res = await fetch(`/api/banks/${encodeURIComponent(name)}`, { method: 'DELETE' });
    if (!res.ok && res.status !== 204) throw new Error('Failed to delete bank config');
  },
};

window.api = api;
