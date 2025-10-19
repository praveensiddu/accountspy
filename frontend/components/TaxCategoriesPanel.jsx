const TaxCategoriesPanelExt = ({ taxCategories, loading, reload }) => {
  const Modal = window.Modal;
  const [form, setForm] = React.useState({ category: '' });
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState('');
  const [open, setOpen] = React.useState(false);
  const [mode, setMode] = React.useState('add');
  const [originalKey, setOriginalKey] = React.useState('');
  const onChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: name === 'category' ? (value || '').trim().toLowerCase() : value }));
  };
  const onSubmit = async (e) => {
    e.preventDefault(); setSaving(true); setError('');
    try {
      const category = (form.category || '').trim().toLowerCase();
      if (!category) throw new Error('category is required');
      if (mode === 'edit' && originalKey) {
        await window.api.removeTaxCategory(originalKey);
      }
      await window.api.addTaxCategory({ category });
      setForm({ category: '' });
      setOriginalKey('');
      setMode('add');
      setOpen(false);
      await reload();
    } catch (err) { setError(err.message || 'Error'); } finally { setSaving(false); }
  };
  const onDelete = async (category) => {
    if (!confirm(`Delete ${category}?`)) return;
    try { await window.api.removeTaxCategory(category); await reload(); } catch (err) { alert(err.message || 'Error'); }
  };
  const onEdit = (t) => {
    setMode('edit');
    setOriginalKey(t.category);
    setForm({ category: t.category });
    setOpen(true);
  };
  return (
    <React.Fragment>
      <h2>Tax Categories</h2>
      <div className="actions" style={{ marginBottom: 12 }}>
        <button type="button" onClick={() => { setForm({ category: '' }); setMode('add'); setOriginalKey(''); setOpen(true); }}>Add category</button>
        <button type="button" onClick={reload} disabled={loading}>Refresh</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Category' : 'Add Category'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'}>
        <div className="row" style={{display:'block'}}>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>category<br/>
              <input name="category" value={form.category} onChange={onChange} placeholder="lowercase [a-z0-9_]" />
            </label>
            <span className="muted" style={{flex:1}}>Lowercase identifier</span>
          </div>
          {error && <div className="error" style={{ marginTop: 8 }}>{error}</div>}
        </div>
      </Modal>
      <div className="card">
        {loading ? (<div>Loading...</div>) : (
          <table>
            <thead>
              <tr>
                <th>category</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {taxCategories.map(t => (
                <tr key={t.category}>
                  <td>{t.category}</td>
                  <td>
                    <button onClick={() => onEdit(t)} style={{marginRight:8, background:'#374151'}}>Edit</button>
                    <button onClick={() => onDelete(t.category)}>Delete</button>
                  </td>
                </tr>
              ))}
              {taxCategories.length === 0 && (<tr><td colSpan="2" className="muted">No tax categories</td></tr>)}
            </tbody>
          </table>
        )}
      </div>
    </React.Fragment>
  );
};

window.TaxCategoriesPanelExt = TaxCategoriesPanelExt;
