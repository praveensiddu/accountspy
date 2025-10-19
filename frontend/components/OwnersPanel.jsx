const OwnersPanelExt = ({ owners, loading, reload, bankaccounts, items, companies }) => {
  const Modal = window.Modal;
  const empty = { name: '', bankaccounts: [], properties: [], companies: [] };
  const [form, setForm] = React.useState(empty);
  const [saving, setSaving] = React.useState(false);
  const [open, setOpen] = React.useState(false);
  const [mode, setMode] = React.useState('add');
  const [originalKey, setOriginalKey] = React.useState('');
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
    if (!confirm(`Delete ${name}?`)) return;
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
  return (
    <React.Fragment>
      <h2>Owners</h2>
      <div className="actions" style={{ marginBottom: 12 }}>
        <button type="button" onClick={() => { setForm(empty); setMode('add'); setOriginalKey(''); setOpen(true); }} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Add owner</button>
        <button type="button" onClick={reload} disabled={loading} className="px-3 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-60">Refresh</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Owner' : 'Add Owner'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'}>
        <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700">name</label>
            <input name="name" value={form.name} onChange={onChange} placeholder="lowercase [a-z0-9_]" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            <p className="text-xs text-gray-500 mt-1">Lowercase identifier</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">bankaccounts (multi-select)</label>
            <select name="bankaccounts" multiple value={form.bankaccounts} onChange={onChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500 min-h-28">
              {(bankaccounts || []).map(ba => (
                <option key={ba.bankaccountname} value={(ba.bankaccountname || '').toLowerCase()}>{ba.bankaccountname}</option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">Hold Cmd/Ctrl to select multiple</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">properties (multi-select)</label>
            <select name="properties" multiple value={form.properties} onChange={onChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500 min-h-28">
              {(items || []).map(p => (
                <option key={p.property} value={(p.property || '').toLowerCase()}>{p.property}</option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">Hold Cmd/Ctrl to select multiple</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">companies (multi-select)</label>
            <select name="companies" multiple value={form.companies} onChange={onChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500 min-h-28">
              {(companies || []).map(c => (
                <option key={c} value={(c || '').toLowerCase()}>{c}</option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">Hold Cmd/Ctrl to select multiple</p>
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
            </thead>
            <tbody>
              {owners.map(x => (
                <tr key={x.name}>
                  <td>{x.name}</td>
                  <td>{x.bankaccounts.join(' | ')}</td>
                  <td>{x.properties.join(' | ')}</td>
                  <td>{x.companies.join(' | ')}</td>
                  <td>
                    <button onClick={() => onEdit(x)} className="px-2 py-1 mr-2 bg-gray-700 text-white rounded hover:bg-gray-800">Edit</button>
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
