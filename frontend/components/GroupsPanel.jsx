const GroupsPanelExt = ({ groups, loading, reload }) => {
  const Modal = window.Modal;
  const empty = { groupname: '', propertylist: '' };
  const [form, setForm] = React.useState(empty);
  const [saving, setSaving] = React.useState(false);
  const [open, setOpen] = React.useState(false);
  const [mode, setMode] = React.useState('add');
  const [originalKey, setOriginalKey] = React.useState('');
  const onChange = (e) => {
    const { name, value } = e.target;
    if (name === 'groupname') {
      const sanitized = (value || '').toLowerCase().replace(/[^a-z0-9_]/g, '');
      setForm({ ...form, [name]: sanitized });
    } else {
      setForm({ ...form, [name]: value });
    }
  };
  const onSubmit = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      const payload = { groupname: form.groupname, propertylist: (form.propertylist || '').split('|').map(s=>s.trim().toLowerCase()).filter(Boolean) };
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
    if (!confirm(`Delete ${name}?`)) return;
    try { await window.api.removeGroup(name); await reload(); } catch (e) { alert(e.message || 'Error'); }
  };
  const onEdit = (x) => {
    setMode('edit');
    setOriginalKey(x.groupname);
    setForm({ groupname: x.groupname, propertylist: (x.propertylist || []).join('|') });
    setOpen(true);
  };
  return (
    <React.Fragment>
      <h2>Groups</h2>
      <div className="actions" style={{ marginBottom: 12 }}>
        <button type="button" onClick={() => setOpen(true)}>Add group</button>
        <button type="button" onClick={reload} disabled={loading}>Refresh</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Group' : 'Add Group'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'}>
        <div className="row" style={{display:'block'}}>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>groupname<br/>
              <input name="groupname" value={form.groupname} onChange={onChange} placeholder="lowercase [a-z0-9_]" />
            </label>
            <span className="muted" style={{flex:1}}>Lowercase identifier</span>
          </div>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>propertylist (pipe-separated)<br/>
              <input name="propertylist" value={form.propertylist} onChange={onChange} placeholder="p1|p2|p3" />
            </label>
            <span className="muted" style={{flex:1}}>Use | as separator</span>
          </div>
        </div>
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
            </thead>
            <tbody>
              {groups.map(x => (
                <tr key={x.groupname}>
                  <td>{x.groupname}</td>
                  <td>{x.propertylist.join(' | ')}</td>
                  <td>
                    <button onClick={() => onEdit(x)} style={{marginRight:8, background:'#374151'}}>Edit</button>
                    <button onClick={() => onDelete(x.groupname)}>Delete</button>
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
