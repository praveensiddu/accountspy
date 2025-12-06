const { useState } = React;

function useOwnerForm(api, owners, setOwners, setError) {
  const emptyOwner = { name: '', bankaccounts: [], properties: [], companies: [] };
  const [ownerForm, setOwnerForm] = useState(emptyOwner);
  const [savingOwner, setSavingOwner] = useState(false);

  const onOwnerChange = (e) => {
    const { name, value } = e.target;
    if (name === 'name') {
      const sanitized = (value || '').toLowerCase().replace(/[^a-z0-9_]/g, '');
      setOwnerForm({ ...ownerForm, [name]: sanitized });
    } else if (e.target.multiple) {
      const selected = Array.from(e.target.selectedOptions).map(o => (o.value || '').toLowerCase());
      setOwnerForm({ ...ownerForm, [name]: selected });
    } else {
      setOwnerForm({ ...ownerForm, [name]: value });
    }
  };

  const onOwnerSubmit = async (e) => {
    e.preventDefault(); setSavingOwner(true); setError('');
    try {
      if (!ownerForm.name) throw new Error('name is required');
      const payload = {
        name: ownerForm.name,
        bankaccounts: Array.from(new Set((ownerForm.bankaccounts || []).map(s => (s || '').toLowerCase()))),
        properties: Array.from(new Set((ownerForm.properties || []).map(s => (s || '').toLowerCase()))),
        companies: Array.from(new Set((ownerForm.companies || []).map(s => (s || '').toLowerCase()))),
      };
      const created = await api.addOwner(payload);
      setOwners([ ...owners, created ]);
      setOwnerForm(emptyOwner);
    } catch (e2) { setError(e2.message || 'Error'); } finally { setSavingOwner(false); }
  };

  const onOwnerDelete = async (name) => {
    if (!confirm(`Delete ${name}?`)) return;
    try { await api.removeOwner(name); setOwners(owners.filter(x => x.name !== name)); }
    catch (e2) { alert(e2.message || 'Error'); }
  };

  return { ownerForm, setOwnerForm, savingOwner, onOwnerChange, onOwnerSubmit, onOwnerDelete };
}

window.useOwnerForm = useOwnerForm;
