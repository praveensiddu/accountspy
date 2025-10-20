const ClassifyRulesPanelExt = ({ classifyRules, loading, reload, bankaccounts, items, taxCategories, transactionTypes, groups }) => {
  const Modal = window.Modal;
  const [open, setOpen] = React.useState(false);
  const [mode, setMode] = React.useState('add');
  const empty = { bankaccountname: '', transaction_type: '', pattern_match_logic: '', tax_category: '', property: '', group: '', otherentity: '' };
  const [form, setForm] = React.useState(empty);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState('');
  const [originalKey, setOriginalKey] = React.useState(null);
  const [filter, setFilter] = React.useState({ bankaccountname:'', transaction_type:'', pattern_match_logic:'', tax_category:'', property:'', group:'', otherentity:'' });

  // Local fallback for groups if props are not yet populated
  const [groupsData, setGroupsData] = React.useState(groups || []);
  React.useEffect(() => { setGroupsData(groups || []); }, [groups]);
  React.useEffect(() => {
    if (!groups || groups.length === 0) {
      try {
        const fn = (window.api && window.api.listGroups) ? window.api.listGroups : null;
        if (typeof fn === 'function') {
          fn().then(gs => { if (Array.isArray(gs)) setGroupsData(gs); }).catch(() => {});
        }
      } catch (_) {}
    }
  }, []);

  const onChange = (e) => {
    const { name, value } = e.target;
    const v = (value || '').toString();
    setForm(prev => ({ ...prev, [name]: ['bankaccountname','transaction_type','tax_category','property','group'].includes(name) ? v.toLowerCase() : v }));
  };

  const onSubmit = async (e) => {
    e.preventDefault(); setSaving(true); setError('');
    try {
      const payload = {
        ...form,
        bankaccountname: (form.bankaccountname || '').trim().toLowerCase(),
        transaction_type: (form.transaction_type || '').trim().toLowerCase(),
        tax_category: (form.tax_category || '').trim().toLowerCase(),
        property: (form.property || '').trim().toLowerCase(),
        group: (form.group || '').trim().toLowerCase(),
        pattern_match_logic: (form.pattern_match_logic || '').trim(),
        otherentity: (form.otherentity || '').trim(),
      };
      if (!payload.bankaccountname || !payload.transaction_type || !payload.pattern_match_logic || !payload.tax_category || !payload.property || !payload.otherentity) {
        throw new Error('All fields are required');
      }
      if (mode === 'edit' && originalKey) {
        // naive: delete old and add new, similar to other panels patterns
        await window.api.removeClassifyRule(originalKey);
      }
      await window.api.addClassifyRule(payload);
      setForm(empty);
      setOriginalKey(null);
      setMode('add');
      setOpen(false);
      await reload();
    } catch (err) { setError(err.message || 'Error'); } finally { setSaving(false); }
  };

  const onDelete = async (rule) => {
    const label = `${rule.bankaccountname} / ${rule.transaction_type}`;
    if (!(await window.showConfirm(`Delete rule ${label}?`))) return;
    try { await window.api.removeClassifyRule(rule); await reload(); } catch (err) { alert(err.message || 'Error'); }
  };

  const onEdit = (rule) => {
    setMode('edit');
    setOriginalKey(rule); // pass entire object for removal (backend can key appropriately)
    setForm({
      bankaccountname: (rule.bankaccountname || '').toLowerCase(),
      transaction_type: (rule.transaction_type || '').toLowerCase(),
      pattern_match_logic: rule.pattern_match_logic || '',
      tax_category: (rule.tax_category || '').toLowerCase(),
      property: (rule.property || '').toLowerCase(),
      group: (rule.group || '').toLowerCase(),
      otherentity: rule.otherentity || '',
    });
    setOpen(true);
  };

  const submitDisabled = !((form.bankaccountname || '').trim()) ||
    !((form.transaction_type || '').trim()) ||
    !((form.pattern_match_logic || '').trim()) ||
    !((form.tax_category || '').trim()) ||
    !((form.property || '').trim()) ||
    !((form.otherentity || '').trim());

  return (
    <React.Fragment>
      <h2>Classify Rules</h2>
      <div className="actions" style={{ marginBottom: 12 }}>
        <button type="button" onClick={() => { setForm(empty); setMode('add'); setOriginalKey(null); setOpen(true); }} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Add rule</button>
        <button type="button" onClick={reload} disabled={loading} className="px-3 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-60">Refresh</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Classify Rule' : 'Add Classify Rule'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(null); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'} submitDisabled={submitDisabled}>
        <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700">bankaccountname</label>
            <input
              name="bankaccountname"
              value={form.bankaccountname}
              onChange={onChange}
              placeholder="lowercase [a-z0-9_]"
              required
              readOnly={mode === 'edit'}
              className={`mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500 ${mode === 'edit' ? 'bg-gray-100 text-gray-600 cursor-not-allowed' : ''}`}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">transaction_type</label>
            <select name="transaction_type" value={form.transaction_type} onChange={onChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" required>
              <option value="">Select transaction type</option>
              {(transactionTypes || []).map(t => (
                <option key={t.transactiontype} value={(t.transactiontype || '').toLowerCase()}>{t.transactiontype}</option>
              ))}
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700">pattern_match_logic</label>
            <textarea name="pattern_match_logic" value={form.pattern_match_logic} onChange={onChange} rows={3} placeholder="e.g., description contains 'rent' and amount < 0" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">tax_category</label>
            <select name="tax_category" value={form.tax_category} onChange={onChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" required>
              <option value="">Select tax category</option>
              {(taxCategories || []).map(c => (
                <option key={c.category} value={(c.category || '').toLowerCase()}>{c.category}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">property</label>
            <select name="property" value={form.property} onChange={onChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" required>
              <option value="">Select property</option>
              {(items || []).map(p => (
                <option key={p.property} value={(p.property || '').toLowerCase()}>{p.property}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">group</label>
            <select name="group" value={form.group} onChange={onChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500">
              <option value="">Select group (optional)</option>
              {(groupsData || []).map(g => (
                <option key={g.groupname} value={(g.groupname || '').toLowerCase()}>{g.groupname}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">otherentity</label>
            <input name="otherentity" value={form.otherentity} onChange={onChange} placeholder="e.g., vendor or payee" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" required />
          </div>
          {error && <div className="md:col-span-2 text-red-600 mt-2">{error}</div>}
        </form>
      </Modal>
      <div className="card">
        {loading ? (<div>Loading...</div>) : (
          <table>
            <thead>
              <tr>
                <th>bankaccountname</th>
                <th>transaction_type</th>
                <th>pattern_match_logic</th>
                <th>tax_category</th>
                <th>property</th>
                <th>group</th>
                <th>otherentity</th>
                <th></th>
              </tr>
              <tr>
                <th>
                  <select value={filter.bankaccountname} onChange={(e)=> setFilter(f=>({...f, bankaccountname: e.target.value }))}>
                    <option value="">All bank accounts</option>
                    {(bankaccounts || []).slice().sort((a,b)=> (a.bankaccountname||'').localeCompare(b.bankaccountname||'', undefined, { sensitivity:'base' })).map(b => (
                      <option key={b.bankaccountname} value={(b.bankaccountname || '').toLowerCase()}>{b.bankaccountname}</option>
                    ))}
                  </select>
                </th>
                <th><input placeholder="filter" value={filter.transaction_type} onChange={(e)=> setFilter(f=>({...f, transaction_type: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.pattern_match_logic} onChange={(e)=> setFilter(f=>({...f, pattern_match_logic: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.tax_category} onChange={(e)=> setFilter(f=>({...f, tax_category: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.property} onChange={(e)=> setFilter(f=>({...f, property: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.group} onChange={(e)=> setFilter(f=>({...f, group: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.otherentity} onChange={(e)=> setFilter(f=>({...f, otherentity: e.target.value }))} /></th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {(classifyRules || [])
                .slice()
                .sort((a, b) => {
                  const an = (a.bankaccountname || '').toLowerCase();
                  const bn = (b.bankaccountname || '').toLowerCase();
                  if (an < bn) return -1; if (an > bn) return 1;
                  const at = (a.transaction_type || '').toLowerCase();
                  const bt = (b.transaction_type || '').toLowerCase();
                  if (at < bt) return -1; if (at > bt) return 1;
                  return 0;
                })
                .filter(r => (
                  (filter.bankaccountname ? (r.bankaccountname||'').toLowerCase().includes(filter.bankaccountname.toLowerCase()) : true) &&
                  (filter.transaction_type ? (r.transaction_type||'').toLowerCase().includes(filter.transaction_type.toLowerCase()) : true) &&
                  (filter.pattern_match_logic ? (r.pattern_match_logic||'').toLowerCase().includes(filter.pattern_match_logic.toLowerCase()) : true) &&
                  (filter.tax_category ? (r.tax_category||'').toLowerCase().includes(filter.tax_category.toLowerCase()) : true) &&
                  (filter.property ? (r.property||'').toLowerCase().includes(filter.property.toLowerCase()) : true) &&
                  (filter.group ? (r.group||'').toLowerCase().includes(filter.group.toLowerCase()) : true) &&
                  (filter.otherentity ? (r.otherentity||'').toLowerCase().includes(filter.otherentity.toLowerCase()) : true)
                ))
                .map((r, idx) => (
                <tr key={`${r.bankaccountname}-${r.transaction_type}-${idx}`}>
                  <td>{r.bankaccountname}</td>
                  <td>{r.transaction_type}</td>
                  <td className="whitespace-pre-wrap">{r.pattern_match_logic}</td>
                  <td>{r.tax_category}</td>
                  <td>{r.property}</td>
                  <td>{r.group}</td>
                  <td>{r.otherentity}</td>
                  <td>
                    <button onClick={() => onEdit(r)} className="px-2 py-1 mr-2 bg-gray-700 text-white rounded hover:bg-gray-800">Edit</button>
                    <button onClick={() => onDelete(r)} className="px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700">Delete</button>
                  </td>
                </tr>
              ))}
              {(classifyRules || []).length === 0 && (<tr><td colSpan="7" className="muted">No classify rules</td></tr>)}
            </tbody>
          </table>
        )}
      </div>
    </React.Fragment>
  );
};

window.ClassifyRulesPanelExt = ClassifyRulesPanelExt;
