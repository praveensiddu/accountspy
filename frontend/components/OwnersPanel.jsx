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
        <button type="button" onClick={() => { setForm(empty); setMode('add'); setOriginalKey(''); setOpen(true); }}>Add owner</button>
        <button type="button" onClick={reload} disabled={loading}>Refresh</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Owner' : 'Add Owner'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'}>
        <div className="row" style={{display:'block'}}>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>name<br/>
              <input name="name" value={form.name} onChange={onChange} placeholder="lowercase [a-z0-9_]" />
            </label>
            <span className="muted" style={{flex:1}}>Lowercase identifier</span>
          </div>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>bankaccounts (multi-select)<br/>
              <select name="bankaccounts" multiple value={form.bankaccounts} onChange={onChange}>
                {(bankaccounts || []).map(ba => (
                  <option key={ba.bankaccountname} value={(ba.bankaccountname || '').toLowerCase()}>{ba.bankaccountname}</option>
                ))}
              </select>
            </label>
            <span className="muted" style={{flex:1}}>Hold Cmd/Ctrl to select multiple</span>
          </div>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>properties (multi-select)<br/>
              <select name="properties" multiple value={form.properties} onChange={onChange}>
                {(items || []).map(p => (
                  <option key={p.property} value={(p.property || '').toLowerCase()}>{p.property}</option>
                ))}
              </select>
            </label>
            <span className="muted" style={{flex:1}}>Hold Cmd/Ctrl to select multiple</span>
          </div>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>companies (multi-select)<br/>
              <select name="companies" multiple value={form.companies} onChange={onChange}>
                {(companies || []).map(c => (
                  <option key={c} value={(c || '').toLowerCase()}>{c}</option>
                ))}
              </select>
            </label>
            <span className="muted" style={{flex:1}}>Hold Cmd/Ctrl to select multiple</span>
          </div>
        </div>
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
                    <button onClick={() => onEdit(x)} style={{marginRight:8, background:'#374151'}}>Edit</button>
                    <button onClick={() => onDelete(x.name)}>Delete</button>
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
