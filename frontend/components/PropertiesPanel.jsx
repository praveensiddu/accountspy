const PropertiesPanelExt = ({ items, companies, loading, reload }) => {
  const {
    empty,
    form,
    setForm,
    saving,
    error,
    open,
    setOpen,
    mode,
    setMode,
    onChange,
    onSubmit,
    onDelete,
    onEdit,
    setOriginalKey,
  } = window.usePropertyForm({ reload });
  const [filter, setFilter] = React.useState({ property: '', cost: '', landValue: '', renovation: '', loanClosingCost: '', ownerCount: '', purchaseDate: '', propMgmtComp: '' });
  const Modal = window.Modal;
  return (
    <React.Fragment>
      <h2>Properties</h2>
      <div className="actions" style={{ marginBottom: 12 }}>
        <span className="mr-3 text-gray-600">Total: {items.length}</span>
        <button type="button" onClick={() => { setForm(empty); setMode('add'); setOriginalKey(''); setOpen(true); }} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Add property</button>
        <button type="button" onClick={reload} disabled={loading} className="px-3 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-60">Refresh</button>
      </div>
      <Modal title={mode === 'edit' ? 'Edit Property' : 'Add Property'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'} submitDisabled={!((form.property || '').trim()) || !((form.purchaseDate || '').trim()) || (form.cost === '' || form.cost == null) || !((form.propMgmtComp || '').trim())}>
        <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700">property</label>
            <input
              name="property"
              value={form.property}
              onChange={onChange}
              placeholder="unique id"
              required
              readOnly={mode === 'edit'}
              className={`mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500 ${mode === 'edit' ? 'bg-gray-100 text-gray-600 cursor-not-allowed' : ''}`}
            />
            <p className="text-xs text-gray-500 mt-1">Lowercase unique ID</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">cost</label>
            <input name="cost" type="number" value={form.cost} onChange={onChange} required className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
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
            <label className="block text-sm font-medium text-gray-700">loanClosingCost</label>
            <input name="loanClosingCost" type="number" value={form.loanClosingCost} onChange={onChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            <p className="text-xs text-gray-500 mt-1">Whole number</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">ownerCount</label>
            <input name="ownerCount" type="number" value={form.ownerCount} onChange={onChange} min="1" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            <p className="text-xs text-gray-500 mt-1">Number of owners</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">purchaseDate</label>
            <input name="purchaseDate" type="text" value={form.purchaseDate} onChange={onChange} placeholder="MM/DD/YYYY" required className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            <p className="text-xs text-gray-500 mt-1">Format MM/DD/YYYY</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">propMgmtComp</label>
            <select name="propMgmtComp" value={form.propMgmtComp} onChange={onChange} required className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500">
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
                <th>loanClosingCost</th>
                <th>ownerCount</th>
                <th>purchaseDate</th>
                <th>propMgmtComp</th>
                <th></th>
              </tr>
              <tr>
                <th><input placeholder="filter" value={filter.property} onChange={(e)=> setFilter(f=>({...f, property: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.cost} onChange={(e)=> setFilter(f=>({...f, cost: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.landValue} onChange={(e)=> setFilter(f=>({...f, landValue: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.renovation} onChange={(e)=> setFilter(f=>({...f, renovation: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.loanClosingCost} onChange={(e)=> setFilter(f=>({...f, loanClosingCost: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.ownerCount} onChange={(e)=> setFilter(f=>({...f, ownerCount: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.purchaseDate} onChange={(e)=> setFilter(f=>({...f, purchaseDate: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.propMgmtComp} onChange={(e)=> setFilter(f=>({...f, propMgmtComp: e.target.value }))} /></th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items
                .slice()
                .sort((a, b) => {
                  const ap = (a.property || '').toLowerCase();
                  const bp = (b.property || '').toLowerCase();
                  if (ap < bp) return -1; if (ap > bp) return 1; return 0;
                })
                .filter(x => {
                  const matchesText = (val, query) => { const s = (val||'').toString().toLowerCase(); const t = (query||'').toString().toLowerCase().trim(); if (!t) return true; const isNeg = t.startsWith('!'); const needle = isNeg ? t.slice(1) : t; if (!needle) return true; const has = s.includes(needle); return isNeg ? !has : has; };
                  const lcc = (x.loanClosingCost != null ? x.loanClosingCost : x.loanClosingCost);
                  return (
                    matchesText(x.property, filter.property) &&
                    matchesText(String(x.cost||''), filter.cost) &&
                    matchesText(String(x.landValue||''), filter.landValue) &&
                    matchesText(String(x.renovation||''), filter.renovation) &&
                    matchesText(String(lcc||''), filter.loanClosingCost) &&
                    matchesText(String(x.ownerCount||''), filter.ownerCount) &&
                    matchesText(String(x.purchaseDate||''), filter.purchaseDate) &&
                    matchesText(String(x.propMgmtComp||''), filter.propMgmtComp)
                  );
                })
                .map((x) => (
                <tr key={x.property}>
                  <td>{x.property}</td>
                  <td>{x.cost}</td>
                  <td>{x.landValue}</td>
                  <td>{x.renovation}</td>
                  <td>{x.loanClosingCost != null ? x.loanClosingCost : x.loanClosingCost}</td>
                  <td>{x.ownerCount}</td>
                  <td>{x.purchaseDate}</td>
                  <td>{x.propMgmtComp}</td>
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
