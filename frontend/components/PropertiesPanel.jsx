const PropertiesPanelExt = ({ items, companies, loading, reload }) => {
  const empty = { property: '', cost: 0, landValue: 0, renovation: 0, loanClosingCOst: 0, ownerCount: 1, purchaseDate: '', propMgmgtComp: '' };
  const [form, setForm] = React.useState(empty);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState('');
  const [open, setOpen] = React.useState(false);
  const [mode, setMode] = React.useState('add'); // 'add' | 'edit'
  const [originalKey, setOriginalKey] = React.useState('');
  const Modal = window.Modal;
  const onChange = (e) => {
    const { name, value } = e.target;
    if ([ 'cost','landValue','renovation','loanClosingCOst','ownerCount' ].includes(name)) {
      setForm({ ...form, [name]: Number(value || 0) });
    } else {
      setForm({ ...form, [name]: value });
    }
  };
  const onSubmit = async (e) => {
    e.preventDefault(); setSaving(true); setError('');
    try {
      if (!form.property) throw new Error('property is required');
      const payload = {
        ...form,
        property: (form.property || '').trim().toLowerCase(),
        purchaseDate: (form.purchaseDate || '').trim().toLowerCase(),
        propMgmgtComp: (form.propMgmgtComp || '').trim().toLowerCase(),
      };
      if (mode === 'edit') {
        if (originalKey && originalKey !== payload.property) {
          await window.api.remove(originalKey);
        } else if (originalKey) {
          await window.api.remove(originalKey);
        }
      }
      await window.api.add(payload);
      setForm(empty);
      setOriginalKey('');
      setMode('add');
      setOpen(false);
      await reload();
    } catch (e) { setError(e.message || 'Error'); } finally { setSaving(false); }
  };
  const onDelete = async (id) => {
    if (!confirm(`Delete ${id}?`)) return;
    try { await window.api.remove(id); await reload(); } catch (e) { alert(e.message || 'Error'); }
  };
  const onEdit = (item) => {
    setMode('edit');
    setOriginalKey(item.property);
    setForm({
      property: item.property,
      cost: item.cost,
      landValue: item.landValue,
      renovation: item.renovation,
      loanClosingCOst: item.loanClosingCOst,
      ownerCount: item.ownerCount,
      purchaseDate: item.purchaseDate,
      propMgmgtComp: item.propMgmgtComp,
    });
    setOpen(true);
  };
  return (
    <React.Fragment>
      <h2>Properties</h2>
      <div className="actions" style={{ marginBottom: 12 }}>
        <button type="button" onClick={() => setOpen(true)}>Add property</button>
        <button type="button" onClick={reload} disabled={loading}>Refresh</button>
        <span className="muted">All data is in-memory only.</span>
      </div>
      <Modal title={mode === 'edit' ? 'Edit Property' : 'Add Property'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'}>
        <div className="row" style={{display:'block'}}>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>property<br/>
              <input name="property" value={form.property} onChange={onChange} placeholder="unique id" required />
            </label>
            <span className="muted" style={{flex:1}}>Lowercase unique ID</span>
          </div>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>cost<br/>
              <input name="cost" type="number" value={form.cost} onChange={onChange} />
            </label>
            <span className="muted" style={{flex:1}}>Whole number</span>
          </div>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>landValue<br/>
              <input name="landValue" type="number" value={form.landValue} onChange={onChange} />
            </label>
            <span className="muted" style={{flex:1}}>Whole number</span>
          </div>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>renovation<br/>
              <input name="renovation" type="number" value={form.renovation} onChange={onChange} />
            </label>
            <span className="muted" style={{flex:1}}>Whole number</span>
          </div>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>loanClosingCOst<br/>
              <input name="loanClosingCOst" type="number" value={form.loanClosingCOst} onChange={onChange} />
            </label>
            <span className="muted" style={{flex:1}}>Whole number</span>
          </div>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>ownerCount<br/>
              <input name="ownerCount" type="number" value={form.ownerCount} onChange={onChange} min="1" />
            </label>
            <span className="muted" style={{flex:1}}>Number of owners</span>
          </div>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>purchaseDate<br/>
              <input name="purchaseDate" type="text" value={form.purchaseDate} onChange={onChange} placeholder="MM/DD/YYYY" />
            </label>
            <span className="muted" style={{flex:1}}>Format MM/DD/YYYY</span>
          </div>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>propMgmgtComp<br/>
              <select name="propMgmgtComp" value={form.propMgmgtComp} onChange={onChange}>
                <option value="">Select company</option>
                {companies.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </label>
            <span className="muted" style={{flex:1}}>Select one</span>
          </div>
          {error && <div className="error" style={{ marginTop: 8 }}>{error}</div>}
        </div>
      </Modal>
      <div className="card">
        {loading ? (<div>Loading...</div>) : (
          <table>
            <thead>
              <tr>
                <th>property</th>
                <th>cost</th>
                <th>landValue</th>
                <th>renovation</th>
                <th>loanClosingCOst</th>
                <th>ownerCount</th>
                <th>purchaseDate</th>
                <th>propMgmgtComp</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((x) => (
                <tr key={x.property}>
                  <td>{x.property}</td>
                  <td>{x.cost}</td>
                  <td>{x.landValue}</td>
                  <td>{x.renovation}</td>
                  <td>{x.loanClosingCOst}</td>
                  <td>{x.ownerCount}</td>
                  <td>{x.purchaseDate}</td>
                  <td>{x.propMgmgtComp}</td>
                  <td>
                    <button onClick={() => onEdit(x)} style={{marginRight:8, background:'#374151'}}>Edit</button>
                    <button onClick={() => onDelete(x.property)}>Delete</button>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (<tr><td colSpan="9" className="muted">No items</td></tr>)}
            </tbody>
          </table>
        )}
      </div>
    </React.Fragment>
  );
};

window.PropertiesPanelExt = PropertiesPanelExt;
