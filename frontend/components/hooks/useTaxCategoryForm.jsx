const { useState } = React;

// Hook for TaxCategoriesPanelExt add/edit/delete behavior
function useTaxCategoryForm({ reload }) {
  const empty = { category: '' };
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState('add');
  const [originalKey, setOriginalKey] = useState('');

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
      setForm(empty);
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

window.useTaxCategoryForm = useTaxCategoryForm;
