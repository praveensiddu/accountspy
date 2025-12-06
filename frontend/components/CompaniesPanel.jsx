const CompaniesPanelExt = ({ companyRecords, loading, reload }) => {
  const Modal = window.Modal;
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
    originalKey,
    setOriginalKey,
    onChange,
    onSubmit,
    onDelete,
    onEdit,
  } = window.useCompanyForm({ reload });
  const [filter, setFilter] = React.useState({ companyname: '', rentPercentage: '' });
  return (
    <React.Fragment>
      <h2>Company Records</h2>
      <div className="actions" style={{ marginBottom: 12 }}>
        <span className="mr-3 text-gray-600">Total: {companyRecords.length}</span>
        <button type="button" onClick={() => { setForm(empty); setMode('add'); setOriginalKey(''); setOpen(true); }} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Add company</button>
        <button type="button" onClick={reload} disabled={loading} className="px-3 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-60">Refresh</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Company' : 'Add Company'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'} submitDisabled={!((form.companyname || '').trim()) || !(Number(form.rentPercentage) > 0)}>
        <div className="row" style={{display:'block'}}>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>companyname<br/>
              <input name="companyname" value={form.companyname} onChange={onChange} placeholder="company name (lowercased)" required readOnly={mode==='edit'} style={mode==='edit' ? { background:'#f3f4f6', color:'#6b7280', cursor:'not-allowed' } : {}} />
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
              <tr>
                <th>
                  <input
                    placeholder="filter"
                    value={filter.companyname}
                    onChange={(e)=> setFilter(f=>({...f, companyname: e.target.value }))}
                  />
                </th>
                <th>
                  <input
                    placeholder="filter"
                    value={filter.rentPercentage}
                    onChange={(e)=> setFilter(f=>({...f, rentPercentage: e.target.value }))}
                  />
                </th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {companyRecords
                .filter(x => {
                  const matchesText = (val, query) => { const s = (val||'').toString().toLowerCase(); const t = (query||'').toString().toLowerCase().trim(); if (!t) return true; const isNeg = t.startsWith('!'); const needle = isNeg ? t.slice(1) : t; if (!needle) return true; const has = s.includes(needle); return isNeg ? !has : has; };
                  return (
                    matchesText(x.companyname, filter.companyname) &&
                    matchesText(String(x.rentPercentage||''), filter.rentPercentage)
                  );
                })
                .map((x) => (
                <tr key={x.companyname}>
                  <td>{x.companyname}</td>
                  <td>{x.rentPercentage}</td>
                  <td>
                    <button onClick={() => onEdit(x)} className="px-2 py-1 mr-2 bg-gray-700 text-white rounded hover:bg-gray-800">Edit</button>
                    <button onClick={() => onDelete(x.companyname)} className="px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700">Delete</button>
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
