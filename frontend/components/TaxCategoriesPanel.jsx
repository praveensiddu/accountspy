const TaxCategoriesPanelExt = ({ taxCategories, loading, reload }) => {
  const Modal = window.Modal;
  const [form, setForm] = React.useState({ category: '' });
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState('');
  const [open, setOpen] = React.useState(false);
  const [mode, setMode] = React.useState('add');
  const [originalKey, setOriginalKey] = React.useState('');
  const [filter, setFilter] = React.useState({ category: '' });
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
    if (!(await window.showConfirm(`Delete ${category}?`))) return;
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
        <button type="button" onClick={() => { setForm({ category: '' }); setMode('add'); setOriginalKey(''); setOpen(true); }} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Add category</button>
        <button type="button" onClick={reload} disabled={loading} className="px-3 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-60">Refresh</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Category' : 'Add Category'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'} submitDisabled={!((form.category || '').trim())}>
        <form onSubmit={onSubmit} className="grid grid-cols-1 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700">category</label>
            <input name="category" value={form.category} onChange={onChange} placeholder="lowercase [a-z0-9_]" required className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            <p className="text-xs text-gray-500 mt-1">Lowercase identifier</p>
          </div>
          {error && <div className="text-red-600 mt-2">{error}</div>}
        </form>
      </Modal>
      <div className="card">
        {loading ? (<div>Loading...</div>) : (
          <table>
            <thead>
              <tr>
                <th>category</th>
                <th></th>
              </tr>
              <tr>
                <th><input placeholder="filter" value={filter.category} onChange={(e)=> setFilter({ category: e.target.value })} /></th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {taxCategories
                .filter(t => (filter.category ? (t.category||'').toLowerCase().includes(filter.category.toLowerCase()) : true))
                .map(t => (
                <tr key={t.category}>
                  <td>{t.category}</td>
                  <td>
                    <button onClick={() => onDelete(t.category)} className="px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700">Delete</button>
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
