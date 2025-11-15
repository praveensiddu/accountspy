const OwnersPanelExt = ({ owners, loading, reload, bankaccounts, items, companies }) => {
  const Modal = window.Modal;
  const MultiSelect = window.MultiSelect;
  const empty = { name: '', bankaccounts: [], properties: [], companies: [] };
  const [form, setForm] = React.useState(empty);
  const [saving, setSaving] = React.useState(false);
  const [open, setOpen] = React.useState(false);
  const [mode, setMode] = React.useState('add');
  const [originalKey, setOriginalKey] = React.useState('');
  const [filter, setFilter] = React.useState({ name: '', bankaccounts: '', properties: '', companies: '' });
  const onChange = (e) => {
    const { name, value, multiple, selectedOptions } = e.target;
    if (name === 'name') {
      setForm({ ...form, [name]: (value || '').toLowerCase().replace(/[^a-z0-9_]/g, '') });
    } else if (multiple) {
      const selected = Array.from(selectedOptions || []).map(o => (o.value || '').toLowerCase());
      setForm({ ...form, [name]: selected });
    } else {
      setForm({ ...form, [name]: value });
    }
  };
  const onSubmit = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      if (!form.name) throw new Error('name is required');
      const payload = {
        name: form.name,
        bankaccounts: Array.from(new Set((form.bankaccounts || []).map(s => (s || '').toLowerCase()))),
        properties: Array.from(new Set((form.properties || []).map(s => (s || '').toLowerCase()))),
        companies: Array.from(new Set((form.companies || []).map(s => (s || '').toLowerCase()))),
      };
      if (mode === 'edit' && originalKey) {
        await window.api.removeOwner(originalKey);
      }
      await window.api.addOwner(payload);
      setForm(empty);
      setOriginalKey('');
      setMode('add');
      setOpen(false);
      await reload();
    } catch (e) { alert(e.message || 'Error'); } finally { setSaving(false); }
  };
  const onDelete = async (name) => {
    if (!(await window.showConfirm(`Delete ${name}?`))) return;
    try { await window.api.removeOwner(name); await reload(); } catch (e) { alert(e.message || 'Error'); }
  };
  const onEdit = (x) => {
    setMode('edit');
    setOriginalKey(x.name);
    const lc = (arr) => (arr || []).map(v => (v || '').toLowerCase());
    setForm({
      name: (x.name || '').toLowerCase(),
      bankaccounts: lc(x.bankaccounts),
      properties: lc(x.properties),
      companies: lc(x.companies),
    });
    setOpen(true);
  };
  const onExport = async (name) => {
    try {
      const res = await fetch('/api/owners/export', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json().catch(()=>({ status:'ok' }));
      alert(`Export requested: ${data.owner || name}`);
    } catch (e) {
      alert(e.message || 'Export failed');
    }
  };
  return (
    <React.Fragment>
      <h2>Owners</h2>
      <div className="actions" style={{ marginBottom: 12 }}>
        <span className="mr-3 text-gray-600">Total: {owners.length}</span>
        <button type="button" onClick={() => { setForm(empty); setMode('add'); setOriginalKey(''); setOpen(true); }} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Add owner</button>
        <button type="button" onClick={reload} disabled={loading} className="px-3 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-60">Refresh</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Owner' : 'Add Owner'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'} submitDisabled={!((form.name || '').trim()) || !((form.properties || []).length) || !((form.bankaccounts || []).length)}>
        <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700">name</label>
            <input
              name="name"
              value={form.name}
              onChange={onChange}
              placeholder="lowercase [a-z0-9_]"
              readOnly={mode === 'edit'}
              className={`mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500 ${mode === 'edit' ? 'bg-gray-100 text-gray-600 cursor-not-allowed' : ''}`}
            />
            <p className="text-xs text-gray-500 mt-1">Lowercase identifier</p>
          </div>
          <div>
            <MultiSelect
              label="bankaccounts"
              options={(bankaccounts || []).map(ba => ({ value: (ba.bankaccountname || '').toLowerCase(), label: ba.bankaccountname }))}
              selected={form.bankaccounts}
              onChange={(vals) => setForm({ ...form, bankaccounts: (vals || []).map(v => (v || '').toLowerCase()) })}
              placeholder="Select bank accounts..."
            />
          </div>
          <div>
            <MultiSelect
              label="properties"
              options={(items || []).map(p => ({ value: (p.property || '').toLowerCase(), label: p.property }))}
              selected={form.properties}
              onChange={(vals) => setForm({ ...form, properties: (vals || []).map(v => (v || '').toLowerCase()) })}
              placeholder="Select properties..."
            />
          </div>
          <div>
            <MultiSelect
              label="companies"
              options={(companies || []).map(c => ({ value: (c || '').toLowerCase(), label: c }))}
              selected={form.companies}
              onChange={(vals) => setForm({ ...form, companies: (vals || []).map(v => (v || '').toLowerCase()) })}
              placeholder="Select companies..."
            />
          </div>
        </form>
      </Modal>
      <div className="card">
        {loading ? (<div>Loading...</div>) : (
          <table>
            <thead>
              <tr>
                <th>name</th>
                <th>bankaccounts</th>
                <th>properties</th>
                <th>companies</th>
                <th></th>
              </tr>
              <tr>
                <th><input placeholder="filter" value={filter.name} onChange={(e)=> setFilter(f=>({...f, name: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.bankaccounts} onChange={(e)=> setFilter(f=>({...f, bankaccounts: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.properties} onChange={(e)=> setFilter(f=>({...f, properties: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.companies} onChange={(e)=> setFilter(f=>({...f, companies: e.target.value }))} /></th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {owners
                .filter(x => {
                  const matchesText = (val, query) => { const s = (val||'').toString().toLowerCase(); const t = (query||'').toString().toLowerCase().trim(); if (!t) return true; const isNeg = t.startsWith('!'); const needle = isNeg ? t.slice(1) : t; if (!needle) return true; const has = s.includes(needle); return isNeg ? !has : has; };
                  return (
                    matchesText(x.name, filter.name) &&
                    matchesText((x.bankaccounts||[]).join(' '), filter.bankaccounts) &&
                    matchesText((x.properties||[]).join(' '), filter.properties) &&
                    matchesText((x.companies||[]).join(' '), filter.companies)
                  );
                })
                .map(x => (
                <tr key={x.name}>
                  <td>{x.name}</td>
                  <td>{x.bankaccounts.join(' | ')}</td>
                  <td>{x.properties.join(' | ')}</td>
                  <td>{x.companies.join(' | ')}</td>
                  <td>
                    <button onClick={() => onEdit(x)} className="px-2 py-1 mr-2 bg-gray-700 text-white rounded hover:bg-gray-800">Edit</button>
                    <button onClick={() => onExport(x.name)} className="px-2 py-1 mr-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">Export</button>
                    <button onClick={() => onDelete(x.name)} className="px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700">Delete</button>
                  </td>
                </tr>
              ))}
              {owners.length === 0 && (<tr><td colSpan="5" className="muted">No owners</td></tr>)}
            </tbody>
          </table>
        )}
      </div>
    </React.Fragment>
  );
};

window.OwnersPanelExt = OwnersPanelExt;
