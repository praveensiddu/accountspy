const { useState } = React;

function useGroupForm(api, groups, setGroups, setError) {
  const emptyGroup = { groupname: '', propertylist: '' };
  const [groupForm, setGroupForm] = useState(emptyGroup);
  const [savingGroup, setSavingGroup] = useState(false);

  const onGroupChange = (e) => {
    const { name, value } = e.target;
    if (name === 'groupname') {
      const sanitized = (value || '').toLowerCase().replace(/[^a-z0-9_]/g, '');
      setGroupForm({ ...groupForm, [name]: sanitized });
    } else {
      setGroupForm({ ...groupForm, [name]: value });
    }
  };

  const onGroupSubmit = async (e) => {
    e.preventDefault(); setSavingGroup(true); setError('');
    try {
      const payload = { groupname: groupForm.groupname, propertylist: (groupForm.propertylist || '').split('|').map(s=>s.trim().toLowerCase()).filter(Boolean) };
      if (!payload.groupname) throw new Error('groupname is required');
      const created = await api.addGroup(payload);
      setGroups([ ...groups, created ]);
      setGroupForm(emptyGroup);
    } catch (e2) { setError(e2.message || 'Error'); } finally { setSavingGroup(false); }
  };

  const onGroupDelete = async (name) => {
    if (!confirm(`Delete ${name}?`)) return;
    try { await api.removeGroup(name); setGroups(groups.filter(x => x.groupname !== name)); }
    catch (e2) { alert(e2.message || 'Error'); }
  };

  return { groupForm, setGroupForm, savingGroup, onGroupChange, onGroupSubmit, onGroupDelete };
}

window.useGroupForm = useGroupForm;
