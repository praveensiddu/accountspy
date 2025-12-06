const { useState } = React;

// Hook encapsulating the full PropertiesPanelExt form behavior, including
// add/edit modes, originalKey tracking, modal open state, and error handling.
function usePropertyForm({ reload }) {
  const empty = { property: '', cost: 0, landValue: 0, renovation: 0, loanClosingCost: 0, ownerCount: 1, purchaseDate: '', propMgmtComp: '' };
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState('add'); // 'add' | 'edit'
  const [originalKey, setOriginalKey] = useState('');

  const onChange = (e) => {
    const { name, value } = e.target;
    if ([ 'cost','landValue','renovation','loanClosingCost','ownerCount' ].includes(name)) {
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
        propMgmtComp: (form.propMgmtComp || '').trim().toLowerCase(),
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
    } catch (e2) { setError(e2.message || 'Error'); } finally { setSaving(false); }
  };

  const onDelete = async (id) => {
    if (!(await window.showConfirm(`Delete ${id}?`))) return;
    try { await window.api.remove(id); await reload(); } catch (e2) { alert(e2.message || 'Error'); }
  };

  const onEdit = (item) => {
    setMode('edit');
    setOriginalKey(item.property);
    setForm({
      property: item.property,
      cost: item.cost,
      landValue: item.landValue,
      renovation: item.renovation,
      loanClosingCost: item.loanClosingCost != null ? item.loanClosingCost : item.loanClosingCost,
      ownerCount: item.ownerCount,
      purchaseDate: item.purchaseDate,
      propMgmtComp: item.propMgmtComp,
    });
    setOpen(true);
  };

  return {
    empty,
    form,
    setForm,
    saving,
    error,
    setError,
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

window.usePropertyForm = usePropertyForm;
