const { useEffect, useState } = React;

function ClassifyRulesTabs({ classifyRules, loading, load, bankaccounts, items, taxCategories, transactionTypes, groups }) {
  const [crSubTab, setCrSubTab] = useState(() => {
    try {
      const v = window.localStorage.getItem('crSubTab');
      return v || 'bank';
    } catch (_) { return 'bank'; }
  });
  const [inheritGroupsData, setInheritGroupsData] = useState(groups || []);
  useEffect(() => { setInheritGroupsData(groups || []); }, [groups]);
  useEffect(() => {
    if (!groups || groups.length === 0) {
      try {
        const fn = (window.api && window.api.listGroups) ? window.api.listGroups : null;
        if (typeof fn === 'function') {
          fn().then(gs => { if (Array.isArray(gs)) setInheritGroupsData(gs); }).catch(()=>{});
        }
      } catch (_) {}
    }
  }, []);
  const [commonFilter, setCommonFilter] = useState({ transaction_type: '', pattern_match_logic: '' });
  const [inheritFilter, setInheritFilter] = useState({ bankaccountname: '', tax_category: '', property: '', group: '', otherentity: '' });
  const [commonRules, setCommonRules] = useState([]);
  const [inheritRules, setInheritRules] = useState([]);
  const [subLoading, setSubLoading] = useState(false);

  const fetchCommon = React.useCallback(async () => {
    try {
      setSubLoading(true);
      const res = await fetch('/api/common-rules');
      if (!res.ok) throw new Error('Failed to fetch common rules');
      const data = await res.json();
      setCommonRules(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error(e);
      setCommonRules([]);
    } finally { setSubLoading(false); }
  }, []);

  const fetchInherit = React.useCallback(async () => {
    try {
      setSubLoading(true);
      const res = await fetch('/api/inherit-common-to-bank');
      if (!res.ok) throw new Error('Failed to fetch inherit rules');
      const data = await res.json();
      setInheritRules(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error(e);
      setInheritRules([]);
    } finally { setSubLoading(false); }
  }, []);

  React.useEffect(() => {
    if (crSubTab === 'common') fetchCommon();
    if (crSubTab === 'inherit') fetchInherit();
  }, [crSubTab, fetchCommon, fetchInherit]);

  useEffect(() => {
    try {
      const raw = (window.location && window.location.pathname) || '/';
      const parts = raw.replace(/^\/+|\/+$/g,'').split('/');
      if ((parts[0]||'').toLowerCase() === 'classifyrules') {
        const p1 = (parts[1]||'').toLowerCase();
        const sub = ({ bankrules:'bank', common:'common', inherit:'inherit' })[p1] || null;
        if (sub && sub !== crSubTab) setCrSubTab(sub);
      }
    } catch(_) {}
  }, []);

  React.useEffect(() => {
    try { window.localStorage.setItem('crSubTab', crSubTab); } catch (_) {}
    try {
      const slug = ({ bank:'bankrules', common:'common', inherit:'inherit' })[crSubTab] || 'bankrules';
      if ((window.location && !/\/classifyrules\//.test(window.location.pathname))) {
        // If not on classifyrules path, let App manage routing
      } else {
        const path = `/classifyrules/${slug}`;
        if (window.location.pathname !== path) window.history.pushState(null, '', path);
      }
    } catch(_) {}
  }, [crSubTab]);

  const Modal = window.Modal;
  const confirmAsync = async (message) => {
    try {
      if (typeof window.showConfirm === 'function') {
        return await window.showConfirm(message);
      }
    } catch (e) { /* ignore and fallback */ }
    return window.confirm(message);
  };
  const [commonOpen, setCommonOpen] = useState(false);
  const [commonMode, setCommonMode] = useState('add');
  const [commonForm, setCommonForm] = useState({ transaction_type: '', pattern_match_logic: '' });
  const [commonSaving, setCommonSaving] = useState(false);
  const [commonOriginal, setCommonOriginal] = useState(null);
  const onCommonChange = (e) => {
    const { name, value } = e.target;
    const v = (value || '').toString();
    setCommonForm(prev => ({ ...prev, [name]: name === 'transaction_type' ? v.toLowerCase() : v }));
  };
  const handleAddCommon = () => {
    setCommonForm({ transaction_type: '', pattern_match_logic: '' });
    setCommonMode('add');
    setCommonOriginal(null);
    setCommonOpen(true);
  };
  const handleDeleteCommon = async (r) => {
    const qs = new URLSearchParams({ transaction_type: r.transaction_type || '', pattern_match_logic: r.pattern_match_logic || '' }).toString();
    if (!(await confirmAsync('Delete common rule?'))) return;
    try {
      setSubLoading(true);
      const res = await fetch(`/api/common-rules?${qs}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete common rule');
      await fetchCommon();
    } catch (e) { console.error(e); } finally { setSubLoading(false); }
  };
  const handleEditCommon = (r) => {
    setCommonMode('edit');
    setCommonOriginal(r);
    setCommonForm({ transaction_type: (r.transaction_type||'').toLowerCase(), pattern_match_logic: r.pattern_match_logic||'' });
    setCommonOpen(true);
  };
  const onSubmitCommon = async (e) => {
    e.preventDefault();
    if (!commonForm.transaction_type || !commonForm.pattern_match_logic) return;
    try {
      setCommonSaving(true);
      const res = await fetch('/api/common-rules', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transaction_type: (commonForm.transaction_type||'').trim().toLowerCase(), pattern_match_logic: (commonForm.pattern_match_logic||'').trim() })
      });
      if (!res.ok) throw new Error('Failed to save common rule');
      if (commonMode === 'edit' && commonOriginal && (commonOriginal.transaction_type !== commonForm.transaction_type || commonOriginal.pattern_match_logic !== commonForm.pattern_match_logic)) {
        const qs = new URLSearchParams({ transaction_type: commonOriginal.transaction_type || '', pattern_match_logic: commonOriginal.pattern_match_logic || '' }).toString();
        await fetch(`/api/common-rules?${qs}`, { method: 'DELETE' });
      }
      setCommonOpen(false);
      await fetchCommon();
    } catch (e) { console.error(e); } finally { setCommonSaving(false); }
  };

  const [inheritOpen, setInheritOpen] = useState(false);
  const [inheritMode, setInheritMode] = useState('add');
  const [inheritSaving, setInheritSaving] = useState(false);
  const [inheritOriginal, setInheritOriginal] = useState(null);
  const emptyInherit = { bankaccountname:'', tax_category:'', property:'', group:'', otherentity:'' };
  const [inheritForm, setInheritForm] = useState(emptyInherit);
  const onInheritChange = (e) => {
    const { name, value } = e.target;
    const v = (value || '').toString();
    if (['bankaccountname','tax_category','property','group'].includes(name)) {
      setInheritForm(prev => ({ ...prev, [name]: v.toLowerCase() }));
    } else {
      setInheritForm(prev => ({ ...prev, [name]: v }));
    }
  };
  const handleAddInherit = () => {
    setInheritForm(emptyInherit);
    setInheritMode('add');
    setInheritOriginal(null);
    setInheritOpen(true);
  };
  const handleDeleteInherit = async (r) => {
    const params = {
      bankaccountname: r.bankaccountname || '',
      transaction_type: r.transaction_type || '',
      pattern_match_logic: r.pattern_match_logic || '',
      property: r.property || '',
      group: r.group || '',
      tax_category: r.tax_category || '',
      otherentity: r.otherentity || ''
    };
    const qs = new URLSearchParams(params).toString();
    if (!(await confirmAsync('Delete inherit rule?'))) return;
    try {
      setSubLoading(true);
      const res = await fetch(`/api/inherit-common-to-bank?${qs}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete inherit rule');
      await fetchInherit();
    } catch (e) { console.error(e); } finally { setSubLoading(false); }
  };
  const handleEditInherit = (r) => {
    setInheritMode('edit');
    setInheritOriginal(r);
    setInheritForm({
      bankaccountname: (r.bankaccountname||'').toLowerCase(),
      tax_category: (r.tax_category||'').toLowerCase(),
      property: (r.property||'').toLowerCase(),
      group: (r.group||'').toLowerCase(),
      otherentity: r.otherentity || ''
    });
    setInheritOpen(true);
  };
  const onSubmitInherit = async (e) => {
    e.preventDefault();
    const payload = {
      bankaccountname: (inheritForm.bankaccountname||'').trim().toLowerCase(),
      tax_category: (inheritForm.tax_category||'').trim().toLowerCase(),
      property: (inheritForm.property||'').trim().toLowerCase(),
      group: (inheritForm.group||'').trim().toLowerCase(),
      otherentity: (inheritForm.otherentity||'').trim(),
    };
    if (!payload.bankaccountname) return;
    try {
      setInheritSaving(true);
      const res = await fetch('/api/inherit-common-to-bank', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error('Failed to save inherit rule');
      if (inheritMode === 'edit' && inheritOriginal) {
        const params = {
          bankaccountname: inheritOriginal.bankaccountname || '',
          property: inheritOriginal.property || '',
          group: inheritOriginal.group || '',
          tax_category: inheritOriginal.tax_category || '',
          otherentity: inheritOriginal.otherentity || ''
        };
        const qs = new URLSearchParams(params).toString();
        await fetch(`/api/inherit-common-to-bank?${qs}`, { method: 'DELETE' });
      }
      setInheritOpen(false);
      await fetchInherit();
    } catch (e) { console.error(e); } finally { setInheritSaving(false); }
  };

  return (
    <div>
      <div className="tabs" style={{ marginBottom: 12 }}>
        <button className={`tab ${crSubTab==='bank' ? 'active' : ''}`} onClick={() => setCrSubTab('bank')}>BankRules</button>
        <button className={`tab ${crSubTab==='common' ? 'active' : ''}`} onClick={() => setCrSubTab('common')}>CommonRules</button>
        <button className={`tab ${crSubTab==='inherit' ? 'active' : ''}`} onClick={() => setCrSubTab('inherit')}>InheritCommonToBank</button>
      </div>
      {crSubTab === 'bank' && (
        <div>
          <BankRulesTabs bankaccounts={bankaccounts} items={items} taxCategories={taxCategories} transactionTypes={transactionTypes} groups={groups} />
        </div>
      )}
      {crSubTab === 'common' && (
        <div className="card">
          <div className="actions" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
            <div className="muted">CommonRules</div>
            <div>
              <span className="mr-3 text-gray-600">Total: {(commonRules||[]).length}</span>
              <button type="button" onClick={handleAddCommon} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Add</button>
              <button type="button" onClick={fetchCommon} disabled={subLoading} className="ml-2 px-3 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-60">Refresh</button>
            </div>
          </div>
          <Modal title={commonMode==='edit' ? 'Edit Common Rule' : 'Add Common Rule'} open={commonOpen} onClose={() => { setCommonOpen(false); setCommonMode('add'); setCommonOriginal(null); }} onSubmit={onSubmitCommon} submitLabel={commonSaving ? 'Saving...' : 'Save'} submitDisabled={!((commonForm.transaction_type||'').trim()) || !((commonForm.pattern_match_logic||'').trim())}>
            <form onSubmit={onSubmitCommon} className="grid grid-cols-1 gap-5">
              <div>
                <label className="block text-sm font-medium text-gray-700">transaction_type</label>
                <select name="transaction_type" value={commonForm.transaction_type} onChange={onCommonChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" required>
                  <option value="">Select transaction type</option>
                  {(transactionTypes || []).map(t => (
                    <option key={t.transactiontype} value={(t.transactiontype || '').toLowerCase()}>{t.transactiontype}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">pattern_match_logic</label>
                <textarea name="pattern_match_logic" value={commonForm.pattern_match_logic} onChange={onCommonChange} rows={3} placeholder="e.g., desc_contains=rent" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" required />
              </div>
            </form>
          </Modal>
          {subLoading ? (<div>Loading...</div>) : (
            <table>
              <thead>
                <tr>
                  <th>transaction_type</th>
                  <th>pattern_match_logic</th>
                  <th>actions</th>
                </tr>
                <tr>
                  <th><input placeholder="filter" value={commonFilter.transaction_type} onChange={(e)=> setCommonFilter(f => ({...f, transaction_type: e.target.value}))} /></th>
                  <th><input placeholder="filter" value={commonFilter.pattern_match_logic} onChange={(e)=> setCommonFilter(f => ({...f, pattern_match_logic: e.target.value}))} /></th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {(commonRules || [])
                  .slice()
                  .sort((a, b) => {
                    const at = (a.transaction_type || '').toLowerCase();
                    const bt = (b.transaction_type || '').toLowerCase();
                    if (at < bt) return -1; if (at > bt) return 1; return 0;
                  })
                  .filter(r => {
                    const matchesText = (val, query) => { const s = (val||'').toString().toLowerCase(); const t = (query||'').toString().toLowerCase().trim(); if (!t) return true; const isNeg = t.startsWith('!'); const needle = isNeg ? t.slice(1) : t; if (!needle) return true; const has = s.includes(needle); return isNeg ? !has : has; };
                    return (
                      matchesText(r.transaction_type, commonFilter.transaction_type) &&
                      matchesText(r.pattern_match_logic, commonFilter.pattern_match_logic)
                    );
                  })
                  .map((r, idx) => (
                    <tr key={`common-${r.transaction_type}-${idx}`}>
                      <td>{r.transaction_type}</td>
                      <td className="whitespace-pre-wrap">{r.pattern_match_logic}</td>
                      <td>
                        <button onClick={() => handleEditCommon(r)} className="px-2 py-1 mr-2 bg-gray-700 text-white rounded hover:bg-gray-800">Edit</button>
                        <button onClick={() => handleDeleteCommon(r)} className="px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700">Delete</button>
                      </td>
                    </tr>
                  ))}
                {(commonRules || []).length === 0 && (
                  <tr><td colSpan="3" className="muted">No common rules</td></tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      )}
      {crSubTab === 'inherit' && (
        <div className="card">
          <div className="actions" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
            <div className="muted">InheritCommonToBank</div>
            <div>
              <span className="mr-3 text-gray-600">Total: {(inheritRules||[]).length}</span>
              <button type="button" onClick={handleAddInherit} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Add</button>
              <button type="button" onClick={fetchInherit} disabled={subLoading} className="ml-2 px-3 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-60">Refresh</button>
            </div>
          </div>
          <Modal title={inheritMode==='edit' ? 'Edit Inherit Rule' : 'Add Inherit Rule'} open={inheritOpen} onClose={() => { setInheritOpen(false); setInheritMode('add'); setInheritOriginal(null); }} onSubmit={onSubmitInherit} submitLabel={inheritSaving ? 'Saving...' : 'Save'} submitDisabled={!((inheritForm.bankaccountname||'').trim())}>
            <form onSubmit={onSubmitInherit} className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className="block text-sm font-medium text-gray-700">bankaccountname</label>
                <select name="bankaccountname" value={inheritForm.bankaccountname} onChange={onInheritChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" required>
                  <option value="">Select bank account</option>
                  {(bankaccounts || []).map(b => (
                    <option key={b.bankaccountname} value={(b.bankaccountname || '').toLowerCase()}>{b.bankaccountname}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">tax_category</label>
                <select name="tax_category" value={inheritForm.tax_category} onChange={onInheritChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500">
                  <option value="">Select tax category</option>
                  {(taxCategories || []).map(c => (
                    <option key={c.category} value={(c.category || '').toLowerCase()}>{c.category}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">property</label>
                <select name="property" value={inheritForm.property} onChange={onInheritChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500">
                  <option value="">Select property</option>
                  {(items || []).map(p => (
                    <option key={p.property} value={(p.property || '').toLowerCase()}>{p.property}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">group</label>
                <select name="group" value={inheritForm.group} onChange={onInheritChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500">
                  <option value="">Select group (optional)</option>
                  {(inheritGroupsData || []).map(g => (
                    <option key={g.groupname} value={(g.groupname || '').toLowerCase()}>{g.groupname}</option>
                  ))}
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700">otherentity</label>
                <input name="otherentity" value={inheritForm.otherentity} onChange={onInheritChange} placeholder="optional" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
              </div>
            </form>
          </Modal>
          {subLoading ? (<div>Loading...</div>) : (
            <table>
              <thead>
                <tr>
                  <th>bankaccountname</th>
                  <th>tax_category</th>
                  <th>property</th>
                  <th>group</th>
                  <th>otherentity</th>
                  <th>actions</th>
                </tr>
                <tr>
                  <th><input placeholder="filter" value={inheritFilter.bankaccountname} onChange={(e)=> setInheritFilter(f => ({...f, bankaccountname: e.target.value}))} /></th>
                  <th><input placeholder="filter" value={inheritFilter.tax_category} onChange={(e)=> setInheritFilter(f => ({...f, tax_category: e.target.value}))} /></th>
                  <th><input placeholder="filter" value={inheritFilter.property} onChange={(e)=> setInheritFilter(f => ({...f, property: e.target.value}))} /></th>
                  <th><input placeholder="filter" value={inheritFilter.group} onChange={(e)=> setInheritFilter(f => ({...f, group: e.target.value}))} /></th>
                  <th><input placeholder="filter" value={inheritFilter.otherentity} onChange={(e)=> setInheritFilter(f => ({...f, otherentity: e.target.value}))} /></th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {(inheritRules || [])
                  .slice()
                  .sort((a, b) => {
                    const an = (a.bankaccountname || '').toLowerCase();
                    const bn = (b.bankaccountname || '').toLowerCase();
                    if (an < bn) return -1; if (an > bn) return 1;
                    const atc = (a.tax_category || '').toLowerCase();
                    const btc = (b.tax_category || '').toLowerCase();
                    if (atc < btc) return -1; if (atc > btc) return 1;
                    return 0;
                  })
                  .filter(r => {
                    const matchesText = (val, query) => { const s = (val||'').toString().toLowerCase(); const t = (query||'').toString().toLowerCase().trim(); if (!t) return true; const isNeg = t.startsWith('!'); const needle = isNeg ? t.slice(1) : t; if (!needle) return true; const has = s.includes(needle); return isNeg ? !has : has; };
                    return (
                      matchesText(r.bankaccountname, inheritFilter.bankaccountname) &&
                      matchesText(r.tax_category, inheritFilter.tax_category) &&
                      matchesText(r.property, inheritFilter.property) &&
                      matchesText(r.group, inheritFilter.group) &&
                      matchesText(r.otherentity, inheritFilter.otherentity)
                    );
                  })
                  .map((r, idx) => (
                    <tr key={`inherit-${r.bankaccountname}-${r.property}-${idx}`}>
                      <td>{r.bankaccountname}</td>
                      <td>{r.tax_category}</td>
                      <td>{r.property}</td>
                      <td>{r.group}</td>
                      <td>{r.otherentity}</td>
                      <td>
                        <button onClick={() => handleEditInherit(r)} className="px-2 py-1 mr-2 bg-gray-700 text-white rounded hover:bg-gray-800">Edit</button>
                        <button onClick={() => handleDeleteInherit(r)} className="px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700">Delete</button>
                      </td>
                    </tr>
                  ))}
                {(inheritRules || []).length === 0 && (
                  <tr><td colSpan="6" className="muted">No bank-specific rules</td></tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}

window.ClassifyRulesTabs = ClassifyRulesTabs;
