const { useEffect, useState } = React;

function BankRulesTabs({ bankaccounts, items, taxCategories, transactionTypes, groups }) {
  const [banks, setBanks] = useState([]);
  const [active, setActive] = useState(() => {
    try { return window.localStorage.getItem('bankrules_active') || ''; } catch(_) { return ''; }
  });
  const [rules, setRules] = useState([]);
  const [rulesReady, setRulesReady] = useState(false);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState(() => {
    try {
      const order = window.localStorage.getItem('bankrules_filter_order') || '';
      return { order, transaction_type:'', pattern_match_logic:'', tax_category:'', pgc:'', comment:'', otherentity:'', usedcount:'' };
    } catch(_) { return { order:'', transaction_type:'', pattern_match_logic:'', tax_category:'', pgc:'', comment:'', otherentity:'', usedcount:'' }; }
  });
  const [filterDraft, setFilterDraft] = useState(filter);
  useEffect(()=>{ setFilterDraft(filter); }, []);
  const filterDebTimer = React.useRef(null);
  const applyFilterDebounced = React.useCallback((next) => {
    if (filterDebTimer.current) clearTimeout(filterDebTimer.current);
    filterDebTimer.current = setTimeout(() => {
      setFilter(prev => (typeof next === 'function' ? next(prev) : next));
    }, 250);
  }, []);
  const onFilterChange = (key, value) => {
    setFilterDraft(fd => ({ ...fd, [key]: value }));
    applyFilterDebounced(f => ({ ...f, [key]: value }));
    if (key === 'order') { try { window.localStorage.setItem('bankrules_filter_order', value || ''); } catch(_) {} }
  };
  const matchesText = (val, query) => {
    const s = (val || '').toString().toLowerCase();
    const t = (query || '').toString().toLowerCase().trim();
    if (!t) return true;
    const isNeg = t.startsWith('!');
    const needle = isNeg ? t.slice(1) : t;
    if (!needle) return true; // treat '!' as no-op
    const has = s.includes(needle);
    return isNeg ? !has : has;
  };
  const [showFilterTips, setShowFilterTips] = useState(false);
  // Local groups data sourced from Groups table
  const [bankGroupsData, setBankGroupsData] = useState(groups || []);
  useEffect(() => { setBankGroupsData(groups || []); }, [groups]);
  // Companies for dropdown
  const [companiesData, setCompaniesData] = useState([]);
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/company-records');
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data)) setCompaniesData(data);
        }
      } catch (_) {}
    })();
  }, []);
  useEffect(() => {
    if (!bankGroupsData || bankGroupsData.length === 0) {
      (async () => {
        try {
          const res = await fetch('/api/groups');
          if (res.ok) {
            const data = await res.json();
            if (Array.isArray(data)) setBankGroupsData(data);
          }
        } catch (_) {}
      })();
    }
  }, []);
  const Modal = window.Modal;
  const confirmAsync = async (message) => {
    try { if (typeof window.showConfirm === 'function') return await window.showConfirm(message); } catch (_) {}
    return window.confirm(message);
  };
  const emptyForm = { bankaccountname:'', order: 10000, transaction_type:'', match:'desc_contains', description:'', credit:'', tax_category:'', property:'', group:'', company:'', otherentity:'', comment:'' };
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState('add');
  const [saving, setSaving] = useState(false);
  const [original, setOriginal] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const onChange = (e) => {
    const { name, value } = e.target; const v = (value||'').toString();
    if (name === 'order') {
      const n = Number(v);
      const clamped = (Number.isFinite(n) && n >= 1) ? n : 1;
      setForm(prev => ({ ...prev, order: clamped }));
      return;
    }
    if (name === 'match') { setForm(prev => ({ ...prev, match: v })); return; }
    if (['bankaccountname','transaction_type','tax_category','property','group','company'].includes(name)) setForm(prev => ({...prev, [name]: v.toLowerCase()}));
    else setForm(prev => ({...prev, [name]: v}));
  };

  const loadBanks = React.useCallback(async () => {
    try {
      // Base set: all bankaccounts from setup (even if they don't yet have bank_rules YAML)
      const allAccounts = (bankaccounts || []).map(b => (b.bankaccountname || '').toLowerCase()).filter(Boolean);

      // Optional: enrich with list of banks that already have rules, but do not restrict to them
      let withRules = [];
      try {
        const res = await fetch('/api/bank-rules/banks');
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data)) {
            withRules = data.map(n => (n || '').toLowerCase()).filter(Boolean);
          }
        }
      } catch (_) {
        // ignore errors; we'll fall back to allAccounts only
      }

      // Union of all known bankaccounts and those that have rules
      const union = Array.from(new Set([...(allAccounts || []), ...(withRules || [])]));
      setBanks(union);

      // Preserve current active if it's a valid bank; otherwise default to first
      if (union.length > 0) {
        setActive(prev => (prev && union.includes(prev)) ? prev : union[0]);
      }
    } catch (_) {
      setBanks([]);
    }
  }, [bankaccounts]);

  const loadRules = React.useCallback(async (bank) => {
    if (!bank) { setRules([]); return; }
    try {
      const qs = new URLSearchParams({ bankaccountname: bank });
      const res = await fetch(`/api/bank-rules?${qs}`);
      if (!res.ok) throw new Error('Failed to fetch bank rules');
      const data = await res.json();
      setRules(Array.isArray(data) ? data : []);
      setRulesReady(true);
    } catch (_) {
      setRules([]);
      setRulesReady(true);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { loadBanks(); }, [loadBanks]);
  useEffect(() => {
    try { window.localStorage.setItem('bankrules_active', active || ''); } catch(_) {}
  }, [active]);
  useEffect(() => {
    try { window.localStorage.setItem('bankrules_filter_order', filter.order || ''); } catch(_) {}
  }, [filter.order]);
  useEffect(() => { loadRules(active); }, [active, loadRules]);

  // Handle external prefill from Transactions: open Add/Edit modal with pattern, credit and order, and row attributes
  useEffect(() => {
    let consumed = false;
    const run = async () => {
      try {
        const shouldOpen = window.localStorage.getItem('bankrules_prefill_open') === '1';
        const patt = window.localStorage.getItem('bankrules_prefill_pattern') || '';
        const orderPref = window.localStorage.getItem('bankrules_prefill_order') || '';
        const creditPref = window.localStorage.getItem('bankrules_prefill_credit') || '';
        const ttypePref = (window.localStorage.getItem('bankrules_prefill_ttype') || '').toLowerCase();
        const taxPref = (window.localStorage.getItem('bankrules_prefill_tax') || '').toLowerCase();
        const propPref = (window.localStorage.getItem('bankrules_prefill_property') || '').toLowerCase();
        const groupPref = (window.localStorage.getItem('bankrules_prefill_group') || '').toLowerCase();
        const companyPref = (window.localStorage.getItem('bankrules_prefill_company') || '').toLowerCase();
        const otherPref = (window.localStorage.getItem('bankrules_prefill_otherentity') || '');
        const forceAdd = window.localStorage.getItem('bankrules_prefill_force_add') === '1';
        if (!shouldOpen) return;
        if (!active) return;
        if (!rulesReady) return; // wait until rules loaded to compute nextOrder accurately
        // compute next order similar to handleAdd (max valid > 0 + 1)
        const fallbackMax = (rules || []).reduce((m, r) => {
          const o = Number(r && r.order);
          return (Number.isFinite(o) && o > 0) ? Math.max(m, o) : m;
        }, 0);
        let nextOrder = fallbackMax + 1;
        // Prefer server-computed max order
        try {
          const qsMO = new URLSearchParams({ bankaccountname: (active||'').toLowerCase() });
          const resMO = await fetch(`/api/bank-rules/max-order?${qsMO}`);
          if (resMO.ok) {
            const dataMO = await resMO.json();
            const mo = Number(dataMO && dataMO.max_order);
            if (Number.isFinite(mo) && mo >= 0) nextOrder = mo + 1;
          }
        } catch(_) { /* ignore and use fallback */ }
        const parsedOrder = (() => { const n = Number((orderPref||'').trim()); return isNaN(n) ? null : n; })();
        let existing = null;
        if (!forceAdd && parsedOrder != null) {
          existing = (rules || []).find(r => Number(r.order||0) === parsedOrder);
        }
        // Parse patt into match + description/credit
        let match = 'desc_contains', description = '', credit = '';
        try {
          const m1 = patt.match(/^(desc_startswith|desc_contains)\s*=\s*(.*)$/i);
          const m2 = patt.match(/^credit_equals\s*=\s*([-+]?[0-9]*\.?[0-9]+)$/i);
          if (m1) { match = (m1[1]||'').toLowerCase(); description = m1[2] || ''; }
          else if (m2) { match = 'credit_equals'; credit = m2[1] || ''; }
        } catch(_) {}
        if (!credit && creditPref) { credit = creditPref; }
        if (existing) {
          setMode('edit');
          setOriginal(existing);
          const exo = Number(existing.order);
          const finalOrder = (Number.isFinite(exo) && exo > 0)
            ? exo
            : ((Number.isFinite(parsedOrder) && parsedOrder > 0) ? parsedOrder : Math.max(1, Number(nextOrder)||1));
          setForm({
            bankaccountname: (active||'').toLowerCase(),
            order: finalOrder,
            transaction_type: ttypePref || (existing.transaction_type||'').toLowerCase(),
            match, description, credit,
            tax_category: taxPref || (existing.tax_category||'').toLowerCase(),
            property: propPref || (existing.property||'').toLowerCase(),
            group: groupPref || (existing.group||'').toLowerCase(),
            company: companyPref || (existing.company||'').toLowerCase(),
            otherentity: otherPref || (existing.otherentity||'')
          });
        } else {
          setMode('add');
          setOriginal(null);
          const finalOrder = (Number.isFinite(parsedOrder) && parsedOrder > 0) ? parsedOrder : Math.max(1, Number(nextOrder)||1);
          setForm({
            bankaccountname: (active||'').toLowerCase(),
            order: finalOrder,
            transaction_type: ttypePref || '',
            match, description, credit,
            tax_category: taxPref || '',
            property: propPref || '',
            group: groupPref || '',
            company: companyPref || '',
            otherentity: otherPref || ''
          });
        }
        setOpen(true);
        consumed = true;
      } catch (_) { /* ignore */ }
      finally {
        if (consumed) {
          try {
            window.localStorage.removeItem('bankrules_prefill_open');
            window.localStorage.removeItem('bankrules_prefill_pattern');
            window.localStorage.removeItem('bankrules_prefill_order');
            window.localStorage.removeItem('bankrules_prefill_credit');
            window.localStorage.removeItem('bankrules_prefill_ttype');
            window.localStorage.removeItem('bankrules_prefill_tax');
            window.localStorage.removeItem('bankrules_prefill_property');
            window.localStorage.removeItem('bankrules_prefill_group');
            window.localStorage.removeItem('bankrules_prefill_company');
            window.localStorage.removeItem('bankrules_prefill_otherentity');
            window.localStorage.removeItem('bankrules_prefill_force_add');
            // ensure we are on Bank subtab
            window.localStorage.setItem('crSubTab','bank');
          } catch (_) {}
        }
      }
    };
    run();
  }, [active, rules, rulesReady]);

  const handleAdd = async () => {
    setMode('add'); setOriginal(null);
    // Fallback: compute from currently loaded rules
    const fallbackMax = (rules || []).reduce((m, r) => {
      const o = Number(r && r.order);
      return (Number.isFinite(o) && o > 0) ? Math.max(m, o) : m;
    }, 0);
    let nextOrder = fallbackMax + 1;
    // Prefer server-computed max order
    try {
      const qs = new URLSearchParams({ bankaccountname: (active||'').toLowerCase() });
      const res = await fetch(`/api/bank-rules/max-order?${qs}`);
      if (res.ok) {
        const data = await res.json();
        const mo = Number(data && data.max_order);
        if (Number.isFinite(mo) && mo >= 0) nextOrder = mo + 1;
      }
    } catch (_) { /* ignore and use fallback */ }
    const finalOrder = Math.max(1, Number(nextOrder)||1);
    setForm({ ...emptyForm, bankaccountname: (active||'').toLowerCase(), order: finalOrder, match: 'desc_contains', description: '', credit: '' });
    setOpen(true);
  };
  const handleEdit = (r) => {
    setMode('edit'); setOriginal(r);
    // Parse existing pattern_match_logic into match + description/credit
    const p = (r.pattern_match_logic || '').toString();
    let match = 'desc_contains', description = '', credit = '';
    const m1 = p.match(/^(desc_startswith|desc_contains)\s*=\s*(.*)$/i);
    if (m1) {
      match = m1[1].toLowerCase();
      description = (m1[2] || '').trim();
    } else {
      const m2 = p.match(/^credit_equals\s*=\s*([-+]?[0-9]*\.?[0-9]+)$/i);
      if (m2) {
        match = 'credit_equals';
        credit = (m2[1] || '').trim();
      }
    }
    setForm({
      bankaccountname: (r.bankaccountname||'').toLowerCase(),
      order: Number(r.order||10000),
      transaction_type: (r.transaction_type||'').toLowerCase(),
      match,
      description,
      credit,
      tax_category: (r.tax_category||'').toLowerCase(),
      property: (r.property||'').toLowerCase(),
      group: (r.group||'').toLowerCase(),
      company: (r.company||'').toLowerCase(),
      otherentity: (r.otherentity||''),
      comment: (r.comment||'')
    });
    setOpen(true);
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      // Compose pattern_match_logic from UI
      let pattern_match_logic = '';
      if (form.match === 'credit_equals') {
        pattern_match_logic = `credit_equals=${(form.credit||'').toString().trim()}`;
      } else {
        const desc = (form.description||'').toString().trim();
        pattern_match_logic = `${form.match}=${desc}`;
      }
      const payload = {
        bankaccountname: (form.bankaccountname||'').trim().toLowerCase(),
        order: Number(form.order || 10000),
        transaction_type: (form.transaction_type||'').trim().toLowerCase(),
        pattern_match_logic,
        tax_category: (form.tax_category||'').trim().toLowerCase(),
        property: (form.property||'').trim().toLowerCase(),
        group: (form.group||'').trim().toLowerCase(),
        company: (form.company||'').trim().toLowerCase(),
        otherentity: (form.otherentity||'').trim(),
        comment: (form.comment||'').trim().toLowerCase(),
      };
      const res = await fetch('/api/bank-rules', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error('Failed to save bank rule');
      if (mode === 'edit' && original) {
        // If key changed, delete old
        if (
          (original.bankaccountname||'').toLowerCase() !== payload.bankaccountname ||
          (original.transaction_type||'').toLowerCase() !== payload.transaction_type ||
          (original.pattern_match_logic||'') !== payload.pattern_match_logic ||
          (original.property||'').toLowerCase() !== payload.property ||
          (original.group||'').toLowerCase() !== payload.group ||
          (original.company||'').toLowerCase() !== payload.company ||
          (original.tax_category||'').toLowerCase() !== payload.tax_category ||
          (original.otherentity||'') !== payload.otherentity
        ) {
          const params = {
            bankaccountname: original.bankaccountname||'',
            transaction_type: original.transaction_type||'',
            pattern_match_logic: original.pattern_match_logic||'',
            property: original.property||'',
            group: original.group||'',
            company: original.company||'',
            tax_category: original.tax_category||'',
            otherentity: original.otherentity||''
          };
          const qs = new URLSearchParams(params).toString();
          await fetch(`/api/bank-rules?${qs}`, { method: 'DELETE' });
        }
      }
      setOpen(false);
      await loadRules(active);
      try { if (typeof window.requestTransactionsReload === 'function') await window.requestTransactionsReload(); } catch (_) {}
      try { window.setTopTab && window.setTopTab('transactions'); } catch(_) {}
    } catch (err) {
      console.error(err);
    } finally { setSaving(false); }
  };
  const handleDelete = async (r) => {
    if (!(await confirmAsync('Delete rule?'))) return;
    const params = {
      bankaccountname: r.bankaccountname||'',
      transaction_type: r.transaction_type||'',
      pattern_match_logic: r.pattern_match_logic||'',
      property: r.property||'',
      group: r.group||'',
      tax_category: r.tax_category||'',
      otherentity: r.otherentity||''
    };
    const qs = new URLSearchParams(params).toString();
    try {
      setLoading(true);
      const res = await fetch(`/api/bank-rules?${qs}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete bank rule');
      await loadRules(active);
      try { if (typeof window.requestTransactionsReload === 'function') await window.requestTransactionsReload(); } catch (_) {}
    } catch (e) { console.error(e); } finally { setLoading(false); }
  };

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="tabs" style={{ flexWrap: 'wrap', rowGap: 6 }}>
        {(banks||[]).map(b => (
          <button
            key={b}
            className={`tab ${active===b ? 'active' : ''}`}
            onClick={()=> setActive(b)}
            style={{ whiteSpace: 'normal', wordBreak: 'break-word', textAlign: 'left' }}
          >
            {b}
          </button>
        ))}
      </div>
      {!active && (<div className="muted">No bank rule files found</div>)}
      {active && (
        <div className="tabcontent">
          <div className="actions" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
            <div className="muted">BankRules: {active}</div>
            <div>
              <span className="mr-3 text-gray-600">Total: {(rules||[]).length}</span>
              <button type="button" onClick={handleAdd} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Add Rule</button>
              <button type="button" onClick={()=> loadRules(active)} disabled={loading} className="ml-2 px-3 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-60">Refresh</button>
            </div>
          </div>
          <Modal title={mode==='edit' ? 'Edit Bank Rule' : 'Add Bank Rule'} open={open} onClose={()=> { setOpen(false); setMode('add'); setOriginal(null); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'} submitDisabled={
            !((form.bankaccountname||'').trim())
            || !((form.transaction_type||'').trim())
            || !((form.tax_category||'').trim())
            || !((form.match||'').trim())
            || ((form.match!=='credit_equals') && !(form.description||'').trim())
            || ((form.match==='credit_equals') && !(form.credit||'').toString().trim())
            || (((form.tax_category||'').toLowerCase().trim() === 'personal') && (
                  ((form.property||'').trim()) || ((form.group||'').trim()) || ((form.company||'').trim())
               ))
            || (((form.tax_category||'').trim().toLowerCase()==='rental') && (
                  (((form.property||'').trim() && (form.group||'').trim())) ||
                  (!((form.property||'').trim()) && !((form.group||'').trim()))
               ))
            || (((form.tax_category||'').trim().toLowerCase()==='company') && (
                  !((form.company||'').trim()) ||
                  ((form.property||'').trim()) ||
                  ((form.group||'').trim())
               ))
          }>
            <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className="block text-sm font-medium text-gray-700">bankaccountname</label>
                <input name="bankaccountname" value={form.bankaccountname} onChange={onChange} readOnly className="mt-1 w-full border border-gray-300 rounded-md p-2 bg-gray-100" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">{mode==='edit' ? 'order' : 'insert as order'}</label>
                <input
                  name="order"
                  type="number"
                  value={form.order}
                  onChange={onChange}
                  readOnly={mode==='edit'}
                  className={`mt-1 w-full border rounded-md p-2 shadow-sm ${mode==='edit' ? 'bg-gray-100 border-gray-300 text-gray-600 cursor-not-allowed' : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'}`}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">match</label>
                <select name="match" value={form.match} onChange={onChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" required>
                  <option value="desc_startswith">desc_startswith</option>
                  <option value="desc_contains">desc_contains</option>
                  <option value="credit_equals">credit_equals</option>
                </select>
              </div>
              {form.match !== 'credit_equals' && (
                <div className="md:col-span-1">
                  <label className="block text-sm font-medium text-gray-700">description</label>
                  <input name="description" value={form.description} onChange={onChange} placeholder="text" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
                </div>
              )}
              {form.match === 'credit_equals' && (
                <div className="md:col-span-1">
                  <label className="block text-sm font-medium text-gray-700">credit</label>
                  <input name="credit" value={form.credit} onChange={onChange} placeholder="e.g., 100.00" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700">transaction_type</label>
                <input
                  name="transaction_type"
                  value={form.transaction_type}
                  onChange={onChange}
                  list="transaction-types-list"
                  placeholder="type to filter..."
                  className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  required
                />
                <datalist id="transaction-types-list">
                  {(transactionTypes || []).map(t => (
                    <option key={t.transactiontype} value={(t.transactiontype || '').toLowerCase()}>{t.transactiontype}</option>
                  ))}
                </datalist>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">tax_category</label>
                <select name="tax_category" value={form.tax_category} onChange={onChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500">
                  <option value="">Select tax category</option>
                  {(taxCategories || []).map(c => (
                    <option key={c.category} value={(c.category || '').toLowerCase()}>{c.category}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">property</label>
                <input
                  name="property"
                  value={form.property}
                  onChange={onChange}
                  list="properties-list"
                  placeholder="type to filter..."
                  className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500"
                />
                <datalist id="properties-list">
                  {(items || []).map(p => (
                    <option key={p.property} value={(p.property || '').toLowerCase()}>{p.property}</option>
                  ))}
                </datalist>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">group</label>
                <select name="group" value={form.group} onChange={onChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500">
                  <option value="">Select group (optional)</option>
                  {(bankGroupsData || []).map(g => (
                    <option key={g.groupname} value={(g.groupname || '').toLowerCase()}>{g.groupname}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">company</label>
                <select name="company" value={form.company} onChange={onChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500">
                  <option value="">Select company (optional)</option>
                  {(companiesData || []).map(c => (
                    <option key={c.companyname} value={(c.companyname || '').toLowerCase()}>{c.companyname}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">otherentity</label>
                <input name="otherentity" value={form.otherentity} onChange={onChange} placeholder="optional" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700">comment</label>
                <input name="comment" value={form.comment} onChange={onChange} placeholder="optional note (lowercased in backend)" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
              </div>
            </form>
          </Modal>
          {loading ? (<div>Loading...</div>) : (
            <div className="overflow-x-auto">
              <div style={{ display:'flex', justifyContent:'flex-end', marginBottom: 6 }}>
                <button type="button" className="text-sm text-gray-600 hover:text-gray-900" onClick={()=> setShowFilterTips(v=>!v)}>Filter tips ?</button>
              </div>
              {showFilterTips && (
                <div className="mb-4 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-md p-3">
                  <div className="font-semibold mb-1">Filter syntax</div>
                  <ul className="list-disc pl-4 space-y-1">
                    <li>Plain text: <code>foo</code> matches any value containing <code>foo</code>.</li>
                    <li>Negation: <code>!foo</code> matches values that do <em>not</em> contain <code>foo</code>.</li>
                    <li>Empty transaction_type is surfaced as <code>empty</code> so you can filter on that literal.</li>
                  </ul>
                </div>
              )}
              <table style={{ tableLayout: 'auto', width: '100%' }}>
                <thead>
                  <tr>
                    <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>order</th>
                    <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>transaction_type</th>
                    <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>pattern_match_logic</th>
                    <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>tax_category</th>
                    <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>property</th>
                    <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>group</th>
                    <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>company</th>
                    <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>otherentity</th>
                    <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>usedcount</th>
                    <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>actions</th>
                  </tr>
                  <tr>
                    <th><input name="order" value={filterDraft.order} onChange={e=> onFilterChange('order', e.target.value)} className="w-full border border-gray-300 rounded-md p-1" placeholder="filter" /></th>
                    <th><input name="transaction_type" value={filterDraft.transaction_type} onChange={e=> onFilterChange('transaction_type', e.target.value)} className="w-full border border-gray-300 rounded-md p-1" placeholder="filter" /></th>
                    <th><input name="pattern_match_logic" value={filterDraft.pattern_match_logic} onChange={e=> onFilterChange('pattern_match_logic', e.target.value)} className="w-full border border-gray-300 rounded-md p-1" placeholder="filter" /></th>
                    <th><input name="tax_category" value={filterDraft.tax_category} onChange={e=> onFilterChange('tax_category', e.target.value)} className="w-full border border-gray-300 rounded-md p-1" placeholder="filter" /></th>
                    <th><input name="property" value={filterDraft.property} onChange={e=> onFilterChange('property', e.target.value)} className="w-full border border-gray-300 rounded-md p-1" placeholder="filter" /></th>
                    <th><input name="group" value={filterDraft.group} onChange={e=> onFilterChange('group', e.target.value)} className="w-full border border-gray-300 rounded-md p-1" placeholder="filter" /></th>
                    <th><input name="company" value={filterDraft.company} onChange={e=> onFilterChange('company', e.target.value)} className="w-full border border-gray-300 rounded-md p-1" placeholder="filter" /></th>
                    <th><input name="otherentity" value={filterDraft.otherentity} onChange={e=> onFilterChange('otherentity', e.target.value)} className="w-full border border-gray-300 rounded-md p-1" placeholder="filter" /></th>
                    <th><input name="usedcount" value={filterDraft.usedcount} onChange={e=> onFilterChange('usedcount', e.target.value)} className="w-full border border-gray-300 rounded-md p-1" placeholder="filter" /></th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {(() => {
                    const filtered = (rules || []).filter(r => {
                      if (!matchesText(r.order, filter.order)) return false;
                      if (!matchesText(r.transaction_type, filter.transaction_type)) return false;
                      if (!matchesText(r.pattern_match_logic, filter.pattern_match_logic)) return false;
                      if (!matchesText(r.tax_category, filter.tax_category)) return false;
                      if (!matchesText(r.property, filter.property)) return false;
                      if (!matchesText(r.group, filter.group)) return false;
                      if (!matchesText(r.company, filter.company)) return false;
                      if (!matchesText(r.otherentity, filter.otherentity)) return false;
                      if (!matchesText(r.usedcount, filter.usedcount)) return false;
                      return true;
                    });
                    if (filtered.length === 0) {
                      return (
                        <tr><td colSpan="10" className="muted">No rules</td></tr>
                      );
                    }
                    return filtered.map((r, idx) => (
                      <tr key={`rule-${idx}`}>
                        <td>{r.order}</td>
                        <td>{r.transaction_type}</td>
                        <td>{r.pattern_match_logic}</td>
                        <td>{r.tax_category}</td>
                        <td>{r.property}</td>
                        <td>{r.group}</td>
                        <td>{r.company}</td>
                        <td>{r.otherentity}</td>
                        <td>{r.usedcount}</td>
                        <td>
                          <div className="actions flex gap-2">
                            <button
                              type="button"
                              className="px-2 py-1 bg-blue-600 text-white rounded-md text-xs hover:bg-blue-700"
                              onClick={() => handleEdit(r)}
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              className="px-2 py-1 bg-red-600 text-white rounded-md text-xs hover:bg-red-700"
                              onClick={() => handleDelete(r)}
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ));
                  })()}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

window.BankRulesTabs = BankRulesTabs;
