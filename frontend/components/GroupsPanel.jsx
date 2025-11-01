const GroupsPanelExt = ({ groups, loading, reload, items }) => {
  const Modal = window.Modal;
  const MultiSelect = window.MultiSelect;
  const empty = { groupname: '', propertylist: [] };
  const [form, setForm] = React.useState(empty);
  const [saving, setSaving] = React.useState(false);
  const [open, setOpen] = React.useState(false);
  const [mode, setMode] = React.useState('add');
  const [originalKey, setOriginalKey] = React.useState('');
  const [filter, setFilter] = React.useState({ groupname: '', propertylist: '' });
  const onChange = (e) => {
    const { name, value, multiple, selectedOptions } = e.target;
    if (name === 'groupname') {
      const sanitized = (value || '').toLowerCase().replace(/[^a-z0-9_]/g, '');
      setForm({ ...form, [name]: sanitized });
    } else if (name === 'propertylist' && multiple) {
      const selected = Array.from(selectedOptions || []).map(o => (o.value || '').toLowerCase());
      setForm({ ...form, [name]: selected });
    } else {
      setForm({ ...form, [name]: value });
    }
  };
  const onSubmit = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      const payload = { groupname: form.groupname, propertylist: Array.from(new Set((form.propertylist || []).map(s=> (s || '').toLowerCase())))};
      if (!payload.groupname) throw new Error('groupname is required');
      if (mode === 'edit' && originalKey) {
        await window.api.removeGroup(originalKey);
      }
      await window.api.addGroup(payload);
      setForm(empty);
      setOriginalKey('');
      setMode('add');
      setOpen(false);
      await reload();
    } catch (e) { alert(e.message || 'Error'); } finally { setSaving(false); }
  };
  const onDelete = async (name) => {
    if (!(await window.showConfirm(`Delete ${name}?`))) return;
    try { await window.api.removeGroup(name); await reload(); } catch (e) { alert(e.message || 'Error'); }
  };
  const onEdit = (x) => {
    setMode('edit');
    setOriginalKey(x.groupname);
    setForm({ groupname: (x.groupname || '').toLowerCase(), propertylist: (x.propertylist || []).map(v => (v || '').toLowerCase()) });
    setOpen(true);
  };
  return (
    <React.Fragment>
      <h2>Groups</h2>
      <div className="actions" style={{ marginBottom: 12 }}>
        <span className="mr-3 text-gray-600">Total: {groups.length}</span>
        <button type="button" onClick={() => { setForm(empty); setMode('add'); setOriginalKey(''); setOpen(true); }} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Add group</button>
        <button type="button" onClick={reload} disabled={loading} className="px-3 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-60">Refresh</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Group' : 'Add Group'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'} submitDisabled={!((form.groupname || '').trim()) || !((form.propertylist || []).length)}>
        <form onSubmit={onSubmit} className="grid grid-cols-1 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700">groupname</label>
            <input
              name="groupname"
              value={form.groupname}
              onChange={onChange}
              placeholder="lowercase [a-z0-9_]"
              required
              readOnly={mode === 'edit'}
              className={`mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500 ${mode === 'edit' ? 'bg-gray-100 text-gray-600 cursor-not-allowed' : ''}`}
            />
            <p className="text-xs text-gray-500 mt-1">Lowercase identifier</p>
          </div>
          <div>
            <MultiSelect
              label="propertylist"
              options={(items || []).map(p => ({ value: (p.property || '').toLowerCase(), label: p.property }))}
              selected={form.propertylist}
              onChange={(vals) => setForm({ ...form, propertylist: (vals || []).map(v => (v || '').toLowerCase()) })}
              placeholder="Select properties..."
            />
          </div>
        </form>
      </Modal>
      <div className="card">
        {loading ? (<div>Loading...</div>) : (
          <table>
            <thead>
              <tr>
                <th>groupname</th>
                <th>propertylist</th>
                <th></th>
              </tr>
              <tr>
                <th>
                  <input placeholder="filter" value={filter.groupname} onChange={(e)=> setFilter(f=>({...f, groupname: e.target.value }))} />
                </th>
                <th>
                  <input placeholder="filter" value={filter.propertylist} onChange={(e)=> setFilter(f=>({...f, propertylist: e.target.value }))} />
                </th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {groups
                .filter(x => (
                  (filter.groupname ? (x.groupname||'').toLowerCase().includes(filter.groupname.toLowerCase()) : true) &&
                  (filter.propertylist ? (x.propertylist||[]).join(' ').toLowerCase().includes(filter.propertylist.toLowerCase()) : true)
                ))
                .map(x => (
                <tr key={x.groupname}>
                  <td>{x.groupname}</td>
                  <td>{x.propertylist.join(' | ')}</td>
                  <td>
                    <button onClick={() => onEdit(x)} className="px-2 py-1 mr-2 bg-gray-700 text-white rounded hover:bg-gray-800">Edit</button>
                    <button onClick={() => onDelete(x.groupname)} className="px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700">Delete</button>
                  </td>
                </tr>
              ))}
              {groups.length === 0 && (<tr><td colSpan="3" className="muted">No groups</td></tr>)}
            </tbody>
          </table>
        )}
      </div>
    </React.Fragment>
  );
};

window.GroupsPanelExt = GroupsPanelExt;
