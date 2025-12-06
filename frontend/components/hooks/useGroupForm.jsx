const { useState } = React;

// Hook encapsulating the full GroupsPanelExt behavior, including
// add/edit modes, originalKey tracking, and modal open state.
function useGroupForm({ reload }) {
  const empty = { groupname: '', propertylist: [] };
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState('add');
  const [originalKey, setOriginalKey] = useState('');

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
      const payload = { groupname: form.groupname, propertylist: Array.from(new Set((form.propertylist || []).map(s=> (s || '').toLowerCase()))) };
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
    } catch (e2) { alert(e2.message || 'Error'); } finally { setSaving(false); }
  };

  const onDelete = async (name) => {
    if (!(await window.showConfirm(`Delete ${name}?`))) return;
    try { await window.api.removeGroup(name); await reload(); }
    catch (e2) { alert(e2.message || 'Error'); }
  };

  const onEdit = (x) => {
    setMode('edit');
    setOriginalKey(x.groupname);
    setForm({ groupname: (x.groupname || '').toLowerCase(), propertylist: (x.propertylist || []).map(v => (v || '').toLowerCase()) });
    setOpen(true);
  };

  return {
    empty,
    form,
    setForm,
    saving,
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
  };
}

window.useGroupForm = useGroupForm;
