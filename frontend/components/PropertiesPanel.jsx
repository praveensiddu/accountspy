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
        <button type="button" onClick={() => { setForm(empty); setMode('add'); setOriginalKey(''); setOpen(true); }} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Add property</button>
        <button type="button" onClick={reload} disabled={loading} className="px-3 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-60">Refresh</button>
        <span className="muted">All data is in-memory only.</span>
      </div>
      <Modal title={mode === 'edit' ? 'Edit Property' : 'Add Property'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'}>
        <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700">property</label>
            <input name="property" value={form.property} onChange={onChange} placeholder="unique id" required className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            <p className="text-xs text-gray-500 mt-1">Lowercase unique ID</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">cost</label>
            <input name="cost" type="number" value={form.cost} onChange={onChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            <p className="text-xs text-gray-500 mt-1">Whole number</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">landValue</label>
            <input name="landValue" type="number" value={form.landValue} onChange={onChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            <p className="text-xs text-gray-500 mt-1">Whole number</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">renovation</label>
            <input name="renovation" type="number" value={form.renovation} onChange={onChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            <p className="text-xs text-gray-500 mt-1">Whole number</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">loanClosingCOst</label>
            <input name="loanClosingCOst" type="number" value={form.loanClosingCOst} onChange={onChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            <p className="text-xs text-gray-500 mt-1">Whole number</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">ownerCount</label>
            <input name="ownerCount" type="number" value={form.ownerCount} onChange={onChange} min="1" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            <p className="text-xs text-gray-500 mt-1">Number of owners</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">purchaseDate</label>
            <input name="purchaseDate" type="text" value={form.purchaseDate} onChange={onChange} placeholder="MM/DD/YYYY" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            <p className="text-xs text-gray-500 mt-1">Format MM/DD/YYYY</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">propMgmgtComp</label>
            <select name="propMgmgtComp" value={form.propMgmgtComp} onChange={onChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500">
              <option value="">Select company</option>
              {companies.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">Select one</p>
          </div>
          {error && <div className="col-span-full text-red-600 mt-2">{error}</div>}
        </form>
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
                    <button onClick={() => onEdit(x)} className="px-2 py-1 mr-2 bg-gray-700 text-white rounded hover:bg-gray-800">Edit</button>
                    <button onClick={() => onDelete(x.property)} className="px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700">Delete</button>
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
