const CompaniesPanelExt = ({ companyRecords, loading, reload }) => {
  const Modal = window.Modal;
  const empty = { companyname: '', rentPercentage: 0 };
  const [form, setForm] = React.useState(empty);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState('');
  const [open, setOpen] = React.useState(false);
  const [mode, setMode] = React.useState('add');
  const [originalKey, setOriginalKey] = React.useState('');
  const onChange = (e) => {
    const { name, value } = e.target;
    if (name === 'rentPercentage') setForm({ ...form, [name]: Number(value || 0) });
    else if (name === 'companyname') setForm({ ...form, [name]: (value || '').toLowerCase().replace(/[^a-z0-9]/g, '') });
    else setForm({ ...form, [name]: value });
  };
  const onSubmit = async (e) => {
    e.preventDefault(); setSaving(true); setError('');
    try {
      if (!form.companyname) throw new Error('companyname is required');
      const payload = { ...form, companyname: form.companyname.trim().toLowerCase() };
      if (mode === 'edit' && originalKey) {
        await window.api.removeCompanyRecord(originalKey);
      }
      await window.api.addCompanyRecord(payload);
      setForm(empty);
      setOriginalKey('');
      setMode('add');
      setOpen(false);
      await reload();
    } catch (e) { setError(e.message || 'Error'); } finally { setSaving(false); }
  };
  const onDelete = async (name) => {
    if (!confirm(`Delete ${name}?`)) return;
    try { await window.api.removeCompanyRecord(name); await reload(); } catch (e) { alert(e.message || 'Error'); }
  };
  const onEdit = (x) => {
    setMode('edit');
    setOriginalKey(x.companyname);
    setForm({ companyname: x.companyname, rentPercentage: x.rentPercentage });
    setOpen(true);
  };
  return (
    <React.Fragment>
      <h2>Company Records</h2>
      <div className="actions" style={{ marginBottom: 12 }}>
        <button type="button" onClick={() => { setForm(empty); setMode('add'); setOriginalKey(''); setOpen(true); }}>Add company</button>
        <button type="button" onClick={reload} disabled={loading}>Refresh</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Company' : 'Add Company'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'}>
        <div className="row" style={{display:'block'}}>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>companyname<br/>
              <input name="companyname" value={form.companyname} onChange={onChange} placeholder="company name (lowercased)" />
            </label>
            <span className="muted" style={{flex:1}}>Lowercase alphanumeric</span>
          </div>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>rentPercentage<br/>
              <input name="rentPercentage" type="number" value={form.rentPercentage} onChange={onChange} min="0" />
            </label>
            <span className="muted" style={{flex:1}}>Whole number</span>
          </div>
          {error && <div className="error" style={{ marginTop: 8 }}>{error}</div>}
        </div>
      </Modal>
      <div className="card">
        {loading ? (<div>Loading...</div>) : (
          <table>
            <thead>
              <tr>
                <th>companyname</th>
                <th>rentPercentage</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {companyRecords.map((x) => (
                <tr key={x.companyname}>
                  <td>{x.companyname}</td>
                  <td>{x.rentPercentage}</td>
                  <td>
                    <button onClick={() => onEdit(x)} style={{marginRight:8, background:'#374151'}}>Edit</button>
                    <button onClick={() => onDelete(x.companyname)}>Delete</button>
                  </td>
                </tr>
              ))}
              {companyRecords.length === 0 && (<tr><td colSpan="3" className="muted">No company records</td></tr>)}
            </tbody>
          </table>
        )}
      </div>
    </React.Fragment>
  );
};

window.CompaniesPanelExt = CompaniesPanelExt;
