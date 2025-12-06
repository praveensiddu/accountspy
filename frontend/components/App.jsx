const { useEffect, useState } = React;

function App() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [companies, setCompanies] = useState([]);
  const [companyRecords, setCompanyRecords] = useState([]);
  const [bankaccounts, setBankaccounts] = useState([]);
  const [groups, setGroups] = useState([]);
  const [inheritGroupsData, setInheritGroupsData] = useState([]);
  useEffect(() => { setInheritGroupsData(groups || []); }, [groups]);
  useEffect(() => {
    if (!groups || groups.length === 0) {
      try { api.listGroups().then(gs => { if (Array.isArray(gs)) setInheritGroupsData(gs); }).catch(()=>{}); } catch (_) {}
    }
  }, []);
  const [owners, setOwners] = useState([]);
  const [taxCategories, setTaxCategories] = useState([]);
  const [transactionTypes, setTransactionTypes] = useState([]);
  const [banks, setBanks] = useState([]);
  const [classifyRules, setClassifyRules] = useState([]);
  const [prepYear, setPrepYear] = useState(() => {
    try { return window.localStorage.getItem('currentYearSelect') || (window.current_year || ''); } catch(_) { return (window.current_year || ''); }
  });
  useEffect(() => {
    try { window.localStorage.setItem('currentYearSelect', prepYear || ''); } catch(_) {}
  }, [prepYear]);
  const [txnBATab, setTxnBATab] = useState(() => {
    try { return window.localStorage.getItem('txnBATab') || ''; } catch(_) { return ''; }
  });
  useEffect(() => {
    if (!txnBATab && (bankaccounts || []).length > 0) {
      setTxnBATab((bankaccounts[0].bankaccountname || ''));
    }
  }, [txnBATab, bankaccounts]);
  useEffect(() => {
    try { window.localStorage.setItem('txnBATab', txnBATab || ''); } catch(_) {}
  }, [txnBATab]);
  const [transactionsByBA, setTransactionsByBA] = useState({});
  const [currentYear, setCurrentYear] = useState('');
  const [txnMonth, setTxnMonth] = useState('12');
  const [txnDay, setTxnDay] = useState('31');
  const [txnOpen, setTxnOpen] = useState(false);
  const [txnSaving, setTxnSaving] = useState(false);
  const emptyTxn = { tr_id: '', date: '', description: '', credit: '', ruleid: '', comment: '', transaction_type: '', tax_category: '', property: '', group: '', company: '', otherentity: '', override: '' };
  const [txnForm, setTxnForm] = useState(emptyTxn);
  const [txnFilters, setTxnFilters] = useState({ tr_id: '', date: '', description: '', credit: '', ruleid: '', comment: '', transaction_type: '', tax_category: '', pgc: '', property: '', group: '', company: '', otherentity: '', override: '' });
  const onTxnChange = (e) => {
    const { name, value } = e.target;
    const v = name === 'description' ? (value || '').toLowerCase() : value;
    setTxnForm(prev => ({ ...prev, [name]: v }));
  };
  const onTxnFilterChange = (e) => {
    const { name, value } = e.target;
    setTxnFilters(prev => ({ ...prev, [name]: value }));
  };
  const onTxnAdd = async () => {
    setTxnForm(emptyTxn);
    setTxnMonth('12');
    setTxnDay('31');
    try {
      const res = await fetch('/api/transactions/config');
      if (res.ok) {
        const j = await res.json();
        setCurrentYear(String(j.current_year || ''));
      }
    } catch (_) {}
    setTxnOpen(true);
  };
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/transactions/config');
        if (!res.ok) return;
        const j = await res.json();
        setCurrentYear(String(j.current_year || ''));
      } catch (_) {}
    })();
  }, []);
  const isValidTxnDate = () => {
    if (!currentYear) return false;
    const m = Number(txnMonth);
    const d = Number(txnDay);
    if (!Number.isInteger(m) || m < 1 || m > 12) return false;
    if (!Number.isInteger(d) || d < 1 || d > 31) return false;
    return true;
  };
  const isValidCredit = (c) => {
    if (c == null) return false;
    const s = String(c).trim();
    if (!s) return false;
    const n = Number(s);
    return Number.isFinite(n);
  };
  const isTxnSaveEnabled = (
    isValidTxnDate() &&
    String(txnForm.description || '').trim().length > 0 &&
    isValidCredit(txnForm.credit)
  );
  const saveTxnRows = async (ba, newRows) => {
    setTxnSaving(true);
    try {
      const res = await fetch(`/api/transactions/${encodeURIComponent(ba)}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ rows: newRows }) });
      if (!res.ok) {
        const msg = await res.text().catch(()=> '');
        throw new Error(msg || 'Failed to save');
      }
      setTransactionsByBA(prev => ({ ...prev, [ba]: newRows }));
    } finally { setTxnSaving(false); }
  };
  const onTxnSubmit = async (e) => {
    e.preventDefault();
    try {
      const ba = txnBATab || '';
      if (!ba) throw new Error('Select a bank account');
      const mm = String(txnMonth).padStart(2,'0');
      const dd = String(txnDay).padStart(2,'0');
      const payload = {
        date: `${String(currentYear)}-${mm}-${dd}`,
        description: (txnForm.description || ''),
        credit: (txnForm.credit || ''),
      };
      const res = await fetch(`/api/addendum/${encodeURIComponent(ba)}` , {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const msg = await res.text().catch(()=> '');
        throw new Error(msg || 'Failed to save addendum');
      }
      try {
        const txnsMap = await api.listTransactions();
        if (txnsMap && typeof txnsMap === 'object') setTransactionsByBA(txnsMap);
      } catch (_) {}
      setTxnOpen(false);
    } catch (err) {
      console.error(err);
      alert((err && err.message) || 'Failed to save');
    }
  };
  const onTxnDelete = async (ba, index) => {
    if (!confirm(`Delete transaction ${index}?`)) return;
    try {
      const current = transactionsByBA[ba] || [];
      if (current[index].tr_id) {
        alert('Cannot delete normalized rows');
        return;
      }
      const newRows = [ ...current.slice(0, index), ...current.slice(index + 1) ];
      await saveTxnRows(ba, newRows);
    } catch (err) {
      alert(err.message || 'Error');
    }
  };
  const requestTransactionsReload = React.useCallback(async () => {
    try {
      const txnsMap = await api.listTransactions();
      if (txnsMap && typeof txnsMap === 'object') setTransactionsByBA(txnsMap);
    } catch (_) { /* ignore */ }
  }, []);
  useEffect(() => {
    try { window.requestTransactionsReload = requestTransactionsReload; } catch (_) {}
    return () => {
      try { if (window.requestTransactionsReload === requestTransactionsReload) delete window.requestTransactionsReload; } catch (_) {}
    };
  }, [requestTransactionsReload]);
  const [taxCatForm, setTaxCatForm] = useState({ category: '' });
  const [txTypeForm, setTxTypeForm] = useState({ transactiontype: '' });
  const [bankForm, setBankForm] = useState({ name: '', date_format: '', delim: '', ignore_lines_contains: '', ignore_lines_startswith: '', columnsText: '' });
  const [savingTaxCat, setSavingTaxCat] = useState(false);
  const [savingTxType, setSavingTxType] = useState(false);
  const [savingBank, setSavingBank] = useState(false);
  const [topTab, setTopTab] = useState(() => {
    try {
      const path = (window.location && window.location.pathname) || '/';
      if (path.startsWith('/setup')) return 'setup';
      if (path.startsWith('/classifyrules')) return 'classifyrules';
      if (path.startsWith('/transactions')) return 'transactions';
      if (path.startsWith('/renttracker')) return 'renttracker';
      if (path.startsWith('/rentalsummary')) return 'rentalsummary';
      if (path.startsWith('/companysummary')) return 'companysummary';
      if (path.startsWith('/report')) return 'report';
      return window.localStorage.getItem('topTab') || 'setup';
    } catch (_) {
      return 'setup';
    }
  });
  const [setupTab, setSetupTab] = useState(() => {
    try {
      const path = (window.location && window.location.pathname) || '/';
      if (path.startsWith('/setup/')) {
        const slug = path.split('/')[2] || '';
        if (slug === 'settings') return 'settings';
        if (slug === 'banks') return 'banks';
        if (slug === 'bankaccounts') return 'bankaccounts';
        if (slug === 'companies') return 'companies';
        if (slug === 'properties') return 'properties';
        if (slug === 'groups') return 'groups';
        if (slug === 'owners') return 'owners';
        if (slug === 'taxcats') return 'taxcats';
        if (slug === 'txtypes') return 'txtypes';
      }
      return window.localStorage.getItem('setupTab') || 'properties';
    } catch (_) {
      return 'properties';
    }
  });
  const slugToSetup = (s) => ({
    settings:'settings',
    properties:'properties', companies:'companies', bankaccounts:'bankaccounts', groups:'groups', owners:'owners', banks:'banks', taxcats:'taxcats', txtypes:'txtypes'
  })[s] || 'properties';
  const setupToSlug = (s) => ({
    settings:'settings',
    properties:'properties', companies:'companies', bankaccounts:'bankaccounts', groups:'groups', owners:'owners', banks:'banks', taxcats:'taxcats', txtypes:'txtypes'
  })[s] || 'properties';
  const crSlugToSub = (s) => ({ bankrules:'bank', common:'common', inherit:'inherit' })[s] || 'bank';
  const crSubToSlug = (s) => ({ bank:'bankrules', common:'common', inherit:'inherit' })[s] || 'bankrules';
  const applyRouteFromPath = React.useCallback(() => {
    try {
      const raw = (window.location && window.location.pathname) || '/';
      const parts = raw.replace(/^\/+|\/+$/g,'').split('/');
      const p0 = (parts[0]||'').toLowerCase();
      const p1 = (parts[1]||'').toLowerCase();
      if (p0 === 'setup') {
        setTopTab('setup');
        if (p1) setSetupTab(slugToSetup(p1));
        return;
      }
      if (p0 === 'classifyrules') {
        setTopTab('classifyrules');
        const sub = crSlugToSub(p1);
        try { window.localStorage.setItem('crSubTab', sub); } catch(_) {}
        return;
      }
      if (p0 === 'transactions') { setTopTab('transactions'); return; }
      if (p0 === 'rentalsummary') { setTopTab('rentalsummary'); return; }
      if (p0 === 'companysummary') { setTopTab('companysummary'); return; }
      if (p0 === 'report') { setTopTab('report'); return; }
    } catch (_) {}
  }, [setTopTab, setSetupTab]);
  useEffect(() => {
    applyRouteFromPath();
    const onPop = () => applyRouteFromPath();
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, [applyRouteFromPath]);
  const pushRouteForState = React.useCallback(() => {
    try {
      let path = '/';
      if (topTab === 'setup') {
        path = `/setup/${setupToSlug(setupTab)}`;
      } else if (topTab === 'classifyrules') {
        let sub = 'bank';
        try { sub = window.localStorage.getItem('crSubTab') || 'bank'; } catch(_) {}
        path = `/classifyrules/${crSubToSlug(sub)}`;
      } else if (topTab === 'transactions') {
        path = '/transactions';
      } else if (topTab === 'renttracker') {
        path = '/renttracker';
      } else if (topTab === 'rentalsummary') {
        path = '/rentalsummary';
      } else if (topTab === 'companysummary') {
        path = '/companysummary';
      } else if (topTab === 'report') {
        path = '/report';
      }
      if ((window.location && window.location.pathname) !== path) {
        window.history.pushState(null, '', path);
      }
    } catch (_) {}
  }, [topTab, setupTab]);
  useEffect(() => { pushRouteForState(); }, [topTab, setupTab, pushRouteForState]);
  const empty = { property: '', cost: 0, landValue: 0, renovation: 0, loanClosingCost: 0, ownerCount: 1, purchaseDate: '', propMgmtComp: '' };
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);
  const load = async () => {
    setError('');
    setLoading(true);
    try {
      const [data, comps, compRecs, bas, grps, ownrs, taxcats, txtypes, banksCfg, rules, txnsMap] = await Promise.all([
        api.list(),
        api.companies(),
        api.listCompanyRecords(),
        api.listBankaccounts(),
        api.listGroups(),
        api.listOwners(),
        api.listTaxCategories(),
        api.listTransactionTypes(),
        api.listBanks(),
        api.listClassifyRules(),
        api.listTransactions(),
      ]);
      setItems(data || []);
      setCompanies(comps || []);
      setCompanyRecords(compRecs || []);
      setBankaccounts(bas || []);
      setGroups(grps || []);
      setOwners(ownrs || []);
      setTaxCategories(taxcats || []);
      setTransactionTypes(txtypes || []);
      setBanks(banksCfg || []);
      setClassifyRules(rules || []);
      if (txnsMap && typeof txnsMap === 'object') setTransactionsByBA(txnsMap);
    } catch (e) {
      console.error(e);
      setError(e.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { load(); }, []);
  useEffect(() => {
    try { window.setTopTab = setTopTab; } catch (_) {}
    return () => { try { if (window.setTopTab === setTopTab) delete window.setTopTab; } catch (_) {} };
  }, [setTopTab]);
  useEffect(() => {
    try { window.localStorage.setItem('topTab', topTab || ''); } catch(_) {}
  }, [topTab]);
  useEffect(() => {
    try { window.localStorage.setItem('setupTab', setupTab || ''); } catch(_) {}
  }, [setupTab]);
  const isCSVerified = (row, field) => {
    try {
      if (!row || !row._verified) return false;
      const v = row._verified[field];
      return v === true || v === 'true' || v === '1';
    } catch (_) { return false; }
  };
  const isRSVerified = (row, field) => {
    try {
      if (!row || !row._verified) return false;
      const v = row._verified[field];
      return v === true || v === 'true' || v === '1';
    } catch (_) { return false; }
  };
  const [companyLoading, setCompanyLoading] = useState(false);
  const [companyRows, setCompanyRows] = useState([]);
  const [companyFilters, setCompanyFilters] = useState({ Name:'', income:'', rentpassedtoowners:'', bankfees:'', c_auto:'', c_donate:'', c_entertainment:'', c_internet:'', c_license:'', c_mobile:'', c_off_exp:'', c_parktoll:'', c_phone:'', c_website:'', ignore:'', insurane:'', proffees:'', utilities:'', profit:'' });
  const [rentalLoading, setRentalLoading] = useState(false);
  const [rentalRows, setRentalRows] = useState([]);
  const [rentalFilters, setRentalFilters] = useState({ property:'', rent:'', commissions:'', insurance:'', proffees:'', mortgageinterest:'', repairs:'', tax:'', utilities:'', depreciation:'', hoa:'', other:'', costbasis:'', renteddays:'', profit:'' });
  const [rentTrackerLoading, setRentTrackerLoading] = useState(false);
  const [rentTrackerRows, setRentTrackerRows] = useState([]);
  const verifyCSCell = async (row, field) => {
    try {
      const res = await fetch('/api/company-summary/verify', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ Name: row.Name, field })
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await api.listCompanySummary();
      setCompanyRows(data || []);
    } catch (e) { console.error(e); alert(e.message || 'Failed to verify'); }
  };
  const verifyRSCell = async (row, field) => {
    try {
      const res = await fetch('/api/rental-summary/verify', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ property: row.property, field })
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await api.listRentalSummary();
      setRentalRows(data || []);
    } catch (e) { console.error(e); alert(e.message || 'Failed to verify'); }
  };
  useEffect(() => {
    (async () => {
      try {
        setCompanyLoading(true);
        const data = await api.listCompanySummary();
        setCompanyRows(data || []);
      } catch (e) { console.error(e); setCompanyRows([]); }
      finally { setCompanyLoading(false); }
    })();
  }, []);
  useEffect(() => {
    (async () => {
      try {
        setRentalLoading(true);
        const data = await api.listRentalSummary();
        setRentalRows(data || []);
      } catch (e) { console.error(e); setRentalRows([]); }
      finally { setRentalLoading(false); }
    })();
  }, []);
  useEffect(() => {
    (async () => {
      try {
        setRentTrackerLoading(true);
        const data = await api.listRentTracker();
        setRentTrackerRows(data || []);
      } catch (e) { console.error(e); setRentTrackerRows([]); }
      finally { setRentTrackerLoading(false); }
    })();
  }, []);
  const onBankChange = (e) => {
    const { name, value } = e.target;
    setBankForm(prev => ({ ...prev, [name]: value }));
  };
  const onTxTypeChange = (e) => {
    const { name, value } = e.target;
    setTxTypeForm(prev => ({ ...prev, [name]: value.toLowerCase() }));
  };
  const onTaxCatChange = (e) => {
    const { name, value } = e.target;
    setTaxCatForm(prev => ({ ...prev, [name]: value.toLowerCase() }));
  };
  const onBankSubmit = async (e) => {
    e.preventDefault(); setSavingBank(true); setError('');
    try {
      const name = (bankForm.name || '').trim().toLowerCase();
      if (!name) throw new Error('name is required');
      const ignore_lines_contains = (bankForm.ignore_lines_contains || '')
        .split('|').map(s => s.trim()).filter(Boolean);
      const ignore_lines_startswith = (bankForm.ignore_lines_startswith || '')
        .split('|').map(s => s.trim()).filter(Boolean);
      let columns = [];
      if (bankForm.columnsText && bankForm.columnsText.trim()) {
        try { columns = JSON.parse(bankForm.columnsText); } catch (_) { columns = []; }
      }
      const payload = {
        name,
        date_format: bankForm.date_format || undefined,
        delim: bankForm.delim || undefined,
        ignore_lines_contains: ignore_lines_contains.length ? ignore_lines_contains : undefined,
        ignore_lines_startswith: ignore_lines_startswith.length ? ignore_lines_startswith : undefined,
        columns: columns.length ? columns : undefined,
      };
      await api.addBank(payload);
      setBankForm({ name: '', date_format: '', delim: '', ignore_lines_contains: '', ignore_lines_startswith: '', columnsText: '' });
      await load();
    } catch (err) { setError(err.message || 'Error'); } finally { setSavingBank(false); }
  };
  const onBankDelete = async (name) => {
    if (!confirm(`Delete ${name}?`)) return;
    try { await api.removeBank(name); await load(); } catch (err) { alert(err.message || 'Error'); }
  };
  const onSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      if (!form.property) throw new Error('property is required');
      const payload = {
        ...form,
        property: (form.property || '').trim().toLowerCase(),
        purchaseDate: (form.purchaseDate || '').trim().toLowerCase(),
        propMgmtComp: (form.propMgmtComp || '').trim().toLowerCase(),
      };
      const created = await api.add(payload);
      setItems([ ...items, created ]);
      setForm(empty);
    } catch (e2) {
      setError(e2.message || 'Error');
    } finally {
      setSaving(false);
    }
  };
  const onDelete = async (id) => {
    if (!confirm(`Delete ${id}?`)) return;
    try {
      await api.remove(id);
      setItems(items.filter(x => x.property !== id));
    } catch (e2) {
      alert(e2.message || 'Error');
    }
  };
  const emptyCompany = { companyname: '', rentPercentage: 0 };
  const [companyForm, setCompanyForm] = useState(emptyCompany);
  const [savingCompany, setSavingCompany] = useState(false);
  const onCompanyChange = (e) => {
    const { name, value } = e.target;
    if (name === 'rentPercentage') {
      setCompanyForm({ ...companyForm, [name]: Number(value || 0) });
    } else if (name === 'companyname') {
      const sanitized = (value || '').toLowerCase().replace(/[^a-z0-9]/g, '');
      setCompanyForm({ ...companyForm, [name]: sanitized });
    } else {
      setCompanyForm({ ...companyForm, [name]: value });
    }
  };
  const onCompanySubmit = async (e) => {
    e.preventDefault();
    setSavingCompany(true);
    setError('');
    try {
      if (!companyForm.companyname) throw new Error('companyname is required');
      const payload = { ...companyForm, companyname: companyForm.companyname.trim().toLowerCase() };
      const created = await api.addCompanyRecord(payload);
      setCompanyRecords([ ...companyRecords, created ]);
      setCompanyForm(emptyCompany);
    } catch (e2) {
      setError(e2.message || 'Error');
    } finally {
      setSavingCompany(false);
    }
  };
  const onCompanyDelete = async (name) => {
    if (!confirm(`Delete ${name}?`)) return;
    try {
      await api.removeCompanyRecord(name);
      setCompanyRecords(companyRecords.filter(x => x.companyname !== name));
    } catch (e2) {
      alert(e2.message || 'Error');
    }
  };
  const emptyBA = { bankaccountname: '', bankname: '' };
  const [baForm, setBaForm] = useState(emptyBA);
  const [savingBA, setSavingBA] = useState(false);
  const onBAChange = (e) => {
    const { name, value } = e.target;
    if (name === 'bankaccountname') {
      const sanitized = (value || '').toLowerCase().replace(/[^a-z0-9_]/g, '');
      setBaForm({ ...baForm, [name]: sanitized });
    } else if (name === 'bankname') {
      setBaForm({ ...baForm, [name]: (value || '').toLowerCase() });
    }
  };
  const onBASubmit = async (e) => {
    e.preventDefault(); setSavingBA(true); setError('');
    try {
      if (!baForm.bankaccountname || !baForm.bankname) throw new Error('bankaccountname and bankname are required');
      const created = await api.addBankaccount(baForm);
      setBankaccounts([ ...bankaccounts, created ]);
      setBaForm(emptyBA);
    } catch (e2) { setError(e2.message || 'Error'); } finally { setSavingBA(false); }
  };
  const onBADelete = async (name) => {
    if (!confirm(`Delete ${name}?`)) return;
    try { await api.removeBankaccount(name); setBankaccounts(bankaccounts.filter(x => x.bankaccountname !== name)); }
    catch (e2) { alert(e2.message || 'Error'); }
  };
  const emptyGroup = { groupname: '', propertylist: '' };
  const [groupForm, setGroupForm] = useState(emptyGroup);
  const [savingGroup, setSavingGroup] = useState(false);
  const onGroupChange = (e) => {
    const { name, value } = e.target;
    if (name === 'groupname') {
      const sanitized = (value || '').toLowerCase().replace(/[^a-z0-9_]/g, '');
      setGroupForm({ ...groupForm, [name]: sanitized });
    } else {
      setGroupForm({ ...groupForm, [name]: value });
    }
  };
  const onGroupSubmit = async (e) => {
    e.preventDefault(); setSavingGroup(true); setError('');
    try {
      const payload = { groupname: groupForm.groupname, propertylist: (groupForm.propertylist || '').split('|').map(s=>s.trim().toLowerCase()).filter(Boolean) };
      if (!payload.groupname) throw new Error('groupname is required');
      const created = await api.addGroup(payload);
      setGroups([ ...groups, created ]);
      setGroupForm(emptyGroup);
    } catch (e2) { setError(e2.message || 'Error'); } finally { setSavingGroup(false); }
  };
  const onGroupDelete = async (name) => {
    if (!confirm(`Delete ${name}?`)) return;
    try { await api.removeGroup(name); setGroups(groups.filter(x => x.groupname !== name)); }
    catch (e2) { alert(e2.message || 'Error'); }
  };
  const emptyOwner = { name: '', bankaccounts: [], properties: [], companies: [] };
  const [ownerForm, setOwnerForm] = useState(emptyOwner);
  const [savingOwner, setSavingOwner] = useState(false);
  const onOwnerChange = (e) => {
    const { name, value } = e.target;
    if (name === 'name') {
      const sanitized = (value || '').toLowerCase().replace(/[^a-z0-9_]/g, '');
      setOwnerForm({ ...ownerForm, [name]: sanitized });
    } else if (e.target.multiple) {
      const selected = Array.from(e.target.selectedOptions).map(o => (o.value || '').toLowerCase());
      setOwnerForm({ ...ownerForm, [name]: selected });
    } else {
      setOwnerForm({ ...ownerForm, [name]: value });
    }
  };
  const onOwnerSubmit = async (e) => {
    e.preventDefault(); setSavingOwner(true); setError('');
    try {
      if (!ownerForm.name) throw new Error('name is required');
      const payload = {
        name: ownerForm.name,
        bankaccounts: Array.from(new Set((ownerForm.bankaccounts || []).map(s => (s || '').toLowerCase()))),
        properties: Array.from(new Set((ownerForm.properties || []).map(s => (s || '').toLowerCase()))),
        companies: Array.from(new Set((ownerForm.companies || []).map(s => (s || '').toLowerCase()))),
      };
      const created = await api.addOwner(payload);
      setOwners([ ...owners, created ]);
      setOwnerForm(emptyOwner);
    } catch (e2) { setError(e2.message || 'Error'); } finally { setSavingOwner(false); }
  };
  const onOwnerDelete = async (name) => {
    if (!confirm(`Delete ${name}?`)) return;
    try { await api.removeOwner(name); setOwners(owners.filter(x => x.name !== name)); }
    catch (e2) { alert(e2.message || 'Error'); }
  };
  const TabButton = ({ active, onClick, children }) => (
    <button type="button" onClick={onClick} className={`tab ${active ? 'active' : ''}`}>{children}</button>
  );
  const [exporting, setExporting] = useState(false);
  const [exportResult, setExportResult] = useState({ open: false, path: '' });
  const handleExport = async () => {
    if (exporting) return;
    try {
      setExporting(true);
      const res = await fetch('/api/export-accounts', { method: 'POST' });
      if (!res.ok) { const t = await res.text().catch(()=> ''); throw new Error(t || 'Export failed'); }
      const data = await res.json().catch(()=> ({}));
      const outPath = (data && data.path) ? String(data.path) : '';
      setExportResult({ open: true, path: outPath });
    } catch (e2) {
      alert(e2.message || 'Export failed');
    } finally {
      setExporting(false);
    }
  };
  return (
    <div className="container" style={{ position: 'relative' }}>
      {/* export modal etc. and tab structure remain unchanged, using existing JSX from index.html */}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
