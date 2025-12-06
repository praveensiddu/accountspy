const { useState } = React;

function TransactionsPanel({
  bankaccounts,
  transactionsByBA,
  txnBATab,
  setTxnBATab,
  txnOpen,
  setTxnOpen,
  txnSaving,
  isTxnSaveEnabled,
  txnMonth,
  txnDay,
  txnForm,
  txnFilters,
  onTxnAdd,
  onTxnSubmit,
  onTxnChange,
  onTxnFilterChange,
  requestTransactionsReload,
  setTopTab,
  txnEditMode,
  onTxnEdit,
}) {
  const Modal = window.Modal;

  return (
    <div className="tabcontent">
      <div className="tabs" style={{ marginBottom: 12, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
        {(bankaccounts || []).map(b => {
          const name = b.bankaccountname || '';
          return (
            <button
              key={name}
              className={`tab ${txnBATab===name ? 'active' : ''}`}
              onClick={() => setTxnBATab(name)}
            >
              {name}
            </button>
          );
        })}
      </div>
      <div className="card">
        {(() => {
          const currentBA = (bankaccounts || []).find(b => (b.bankaccountname || '') === txnBATab);
          if (!currentBA) return (<div className="muted">Select a bank account to view transactions.</div>);
          const rows = transactionsByBA[txnBATab] || [];
          return (
            <div>
              <div className="actions" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <div className="muted">Transactions for: <strong>{currentBA.bankaccountname}</strong></div>
                <div>
                  <span className="mr-3 text-gray-600">Total: {rows.length}</span>
                  <button type="button" onClick={onTxnAdd} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Add Transaction</button>
                </div>
              </div>
              <Modal
                title={txnEditMode ? 'Edit Transaction' : 'Add Transaction'}
                open={txnOpen}
                onClose={() => setTxnOpen(false)}
                onSubmit={onTxnSubmit}
                submitLabel={txnSaving ? 'Saving...' : 'Save'}
                submitDisabled={!isTxnSaveEnabled}
              >
                <form onSubmit={onTxnSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">month</label>
                    <select
                      name="month"
                      value={txnMonth}
                      onChange={(e)=> setTxnMonth(e.target.value)}
                      className="mt-1 w-full border border-gray-300 rounded-md p-2"
                    >
                      <option value="01">JAN</option>
                      <option value="02">FEB</option>
                      <option value="03">MAR</option>
                      <option value="04">APR</option>
                      <option value="05">MAY</option>
                      <option value="06">JUN</option>
                      <option value="07">JUL</option>
                      <option value="08">AUG</option>
                      <option value="09">SEP</option>
                      <option value="10">OCT</option>
                      <option value="11">NOV</option>
                      <option value="12">DEC</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">day</label>
                    <select
                      name="day"
                      value={txnDay}
                      onChange={(e)=> setTxnDay(e.target.value)}
                      className="mt-1 w-full border border-gray-300 rounded-md p-2"
                    >
                      {Array.from({length:31}, (_,i)=> String(i+1)).map(d => (
                        <option key={d} value={d}>{d}</option>
                      ))}
                    </select>
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700">description</label>
                    <input
                      name="description"
                      value={txnForm.description}
                      onChange={onTxnChange}
                      className="mt-1 w-full border border-gray-300 rounded-md p-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">credit</label>
                    <input
                      name="credit"
                      type="number"
                      step="any"
                      value={txnForm.credit}
                      onChange={onTxnChange}
                      className="mt-1 w-full border border-gray-300 rounded-md p-2"
                    />
                  </div>
                </form>
              </Modal>
              {(() => {
                const matchesText = (val, query) => {
                  const s = (val||'').toString().toLowerCase();
                  const t = (query||'').toString().toLowerCase().trim();
                  if (!t) return true;
                  const isNeg = t.startsWith('!');
                  const needle = isNeg ? t.slice(1) : t;
                  if (!needle) return true;
                  const has = s.includes(needle);
                  return isNeg ? !has : has;
                };
                const filteredRows = (rows || []).filter(r => {
                  const f = txnFilters; const keys = Object.keys(f);
                  for (let k of keys) {
                    const fv = (f[k] || '').toString().trim();
                    if (!fv) continue;
                    let rv = '';
                    if (k === 'pgc') {
                      rv = [r.property, r.group, r.company].map(x => (x == null ? '' : String(x))).join(' ');
                    } else if (k === 'transaction_type') {
                      const t = (r.transaction_type == null ? '' : String(r.transaction_type));
                      rv = (t.trim() ? t : 'empty');
                    } else {
                      rv = (r[k] == null ? '' : String(r[k]));
                    }
                    if (!matchesText(rv, fv)) return false;
                  }
                  return true;
                });
                const sortedRows = [...filteredRows].sort((a, b) => {
                  const ad = String(a.date || '');
                  const bd = String(b.date || '');
                  if (ad !== bd) return ad < bd ? 1 : -1; // descending date
                  const adesc = String(a.description || '').toLowerCase();
                  const bdesc = String(b.description || '').toLowerCase();
                  if (adesc !== bdesc) return adesc < bdesc ? -1 : 1;
                  const acr = String(a.credit || '');
                  const bcr = String(b.credit || '');
                  if (acr === bcr) return 0;
                  return acr < bcr ? -1 : 1;
                });
                return (
                  <table style={{ tableLayout: 'auto', width: '100%' }}>
                    <thead>
                      <tr>
                        <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>date</th>
                        <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>description</th>
                        <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>credit</th>
                        <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>ruleid</th>
                        <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>comment</th>
                        <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>transaction_type</th>
                        <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>tax_category</th>
                        <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>property/group/company</th>
                        <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>otherentity</th>
                        <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>actions</th>
                      </tr>
                      <tr>
                        <th><input name="date" value={txnFilters.date} onChange={onTxnFilterChange} className="w-full border border-gray-300 rounded-md p-1" placeholder="filter" /></th>
                        <th><input name="description" value={txnFilters.description} onChange={onTxnFilterChange} className="w-full border border-gray-300 rounded-md p-1" placeholder="filter" /></th>
                        <th><input name="credit" value={txnFilters.credit} onChange={onTxnFilterChange} className="w-full border border-gray-300 rounded-md p-1" placeholder="filter" /></th>
                        <th><input name="ruleid" value={txnFilters.ruleid} onChange={onTxnFilterChange} className="w-full border border-gray-300 rounded-md p-1" placeholder="filter" /></th>
                        <th><input name="comment" value={txnFilters.comment} onChange={onTxnFilterChange} className="w-full border border-gray-300 rounded-md p-1" placeholder="filter" /></th>
                        <th><input name="transaction_type" value={txnFilters.transaction_type} onChange={onTxnFilterChange} className="w-full border border-gray-300 rounded-md p-1" placeholder="filter" /></th>
                        <th><input name="tax_category" value={txnFilters.tax_category} onChange={onTxnFilterChange} className="w-full border border-gray-300 rounded-md p-1" placeholder="filter" /></th>
                        <th><input name="pgc" value={txnFilters.pgc} onChange={onTxnFilterChange} className="w-full border border-gray-300 rounded-md p-1" placeholder="filter" /></th>
                        <th><input name="otherentity" value={txnFilters.otherentity} onChange={onTxnFilterChange} className="w-full border border-gray-300 rounded-md p-1" placeholder="filter" /></th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedRows.length === 0 ? (
                        <tr><td colSpan="10" className="muted">No transactions</td></tr>
                      ) : (
                        sortedRows.map((r, idx) => (
                          <tr key={`txn-${idx}`}>
                            <td style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>{r.date}</td>
                            <td style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>{r.description}</td>
                            <td style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>{r.credit}</td>
                            <td style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>
                              {r.ruleid ? (
                                <a
                                  href="#"
                                  className="link"
                                  onClick={(e)=>{
                                    e.preventDefault();
                                    try {
                                      window.localStorage.setItem('crSubTab','bank');
                                      window.localStorage.setItem('bankrules_active', (currentBA.bankaccountname||'').toLowerCase());
                                      window.localStorage.setItem('bankrules_filter_order', String(r.ruleid||''));
                                    } catch(_) {}
                                    setTopTab('classifyrules');
                                  }}
                                >
                                  {r.ruleid}
                                </a>
                              ) : ''}
                            </td>
                            <td style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>{r.comment}</td>
                            <td style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>{((r.transaction_type||'').trim() ? r.transaction_type : 'empty')}</td>
                            <td style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>{r.tax_category}</td>
                            <td style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>{(r.property||'') || (r.group||'') || (r.company||'')}</td>
                            <td style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>{r.otherentity}</td>
                            <td>
                              <div className="actions flex flex-col items-start gap-2">
                                <div className="flex gap-2">
                                  <button
                                    type="button"
                                    className="px-2 py-1 bg-blue-700 text-white rounded hover:bg-blue-800"
                                    onClick={async()=>{ try {
                                      // ADD RULE: prefill from transaction row; insert order = server max_order
                                      const bank = (currentBA.bankaccountname||'').toLowerCase();
                                      let maxOrder = 0;
                                      try {
                                        const qsMO = new URLSearchParams({ bankaccountname: bank });
                                        const resMO = await fetch(`/api/bank-rules/max-order?${qsMO}`);
                                        if (resMO.ok) {
                                          const dataMO = await resMO.json();
                                          const mo = Number(dataMO && dataMO.max_order);
                                          if (Number.isFinite(mo) && mo >= 0) maxOrder = mo;
                                        }
                                      } catch(_) {}
                                      const patt = `desc_contains=${(r.description||'').toString()}`;
                                      const ordFromRow = (r.ruleid != null && String(r.ruleid).trim() !== '') ? Number(String(r.ruleid).trim()) : null;
                                      const insertOrder = (Number.isFinite(ordFromRow) && ordFromRow > 0) ? ordFromRow : (maxOrder + 1);
                                      window.localStorage.setItem('crSubTab','bank');
                                      window.localStorage.setItem('bankrules_active', bank);
                                      window.localStorage.setItem('bankrules_prefill_pattern', patt);
                                      window.localStorage.setItem('bankrules_prefill_order', String(insertOrder||''));
                                      window.localStorage.setItem('bankrules_prefill_credit', String(r.credit||''));
                                      window.localStorage.setItem('bankrules_prefill_ttype', String(r.transaction_type||''));
                                      window.localStorage.setItem('bankrules_prefill_tax', String(r.tax_category||''));
                                      window.localStorage.setItem('bankrules_prefill_property', String(r.property||''));
                                      window.localStorage.setItem('bankrules_prefill_group', String(r.group||''));
                                      window.localStorage.setItem('bankrules_prefill_company', String(r.company||''));
                                      window.localStorage.setItem('bankrules_prefill_otherentity', String(r.otherentity||''));
                                      window.localStorage.setItem('bankrules_prefill_force_add', '1');
                                      window.localStorage.setItem('bankrules_prefill_open', '1');
                                      setTopTab('classifyrules');
                                    } catch(_) {} }}
                                  >
                                    INSERT_RULE
                                  </button>
                                  <button
                                    type="button"
                                    className="px-2 py-1 bg-gray-700 text-white rounded hover:bg-gray-800 disabled:opacity-60"
                                    disabled={!(r.ruleid != null && String(r.ruleid).trim() !== '')}
                                    onClick={async()=>{ try {
                                      const bank = (currentBA.bankaccountname||'').toLowerCase();
                                      const hasRuleId = (r.ruleid != null && String(r.ruleid).trim() !== '');
                                      let pref = null;
                                      if (hasRuleId) {
                                        try {
                                          const qs = new URLSearchParams({ bankaccountname: bank });
                                          const res = await fetch(`/api/bank-rules?${qs}`);
                                          if (res.ok) {
                                            const rules = await res.json();
                                            const rid = Number(String(r.ruleid).trim());
                                            if (Array.isArray(rules)) {
                                              pref = rules.find(x => Number(x && x.order) === rid) || null;
                                            }
                                          }
                                        } catch(_) { /* ignore; will fallback */ }
                                      }
                                      // Set prefill from rule if found, else fallback to transaction row
                                      const isRule = !!pref;
                                      const pattern = isRule ? String(pref.pattern_match_logic||'') : `desc_contains=${(r.description||'').toString()}`;
                                      const orderStr = isRule ? String(pref.order||'') : ((r.ruleid != null && String(r.ruleid).trim() !== '') ? String(r.ruleid).trim() : '');
                                      const creditStr = isRule ? '' : String(r.credit||'');
                                      const ttype = isRule ? String(pref.transaction_type||'') : String(r.transaction_type||'');
                                      const tax = isRule ? String(pref.tax_category||'') : String(r.tax_category||'');
                                      const prop = isRule ? String(pref.property||'') : String(r.property||'');
                                      const grp = isRule ? String(pref.group||'') : String(r.group||'');
                                      const comp = isRule ? String(pref.company||'') : String(r.company||'');
                                      const other = isRule ? String(pref.otherentity||'') : String(r.otherentity||'');
                                      window.localStorage.setItem('crSubTab','bank');
                                      window.localStorage.setItem('bankrules_active', bank);
                                      window.localStorage.setItem('bankrules_prefill_pattern', pattern);
                                      window.localStorage.setItem('bankrules_prefill_order', orderStr);
                                      window.localStorage.setItem('bankrules_prefill_credit', creditStr);
                                      window.localStorage.setItem('bankrules_prefill_ttype', ttype);
                                      window.localStorage.setItem('bankrules_prefill_tax', tax);
                                      window.localStorage.setItem('bankrules_prefill_property', prop);
                                      window.localStorage.setItem('bankrules_prefill_group', grp);
                                      window.localStorage.setItem('bankrules_prefill_company', comp);
                                      window.localStorage.setItem('bankrules_prefill_otherentity', other);
                                      window.localStorage.setItem('bankrules_prefill_open', '1');
                                      setTopTab('classifyrules');
                                    } catch(_) {} }}
                                  >
                                    UPDATE_RULE
                                  </button>
                                </div>
                                {r.fromaddendum && (
                                  <div className="flex gap-2 mt-1">
                                    <button
                                      type="button"
                                      className="px-2 py-1 bg-gray-700 text-white rounded hover:bg-gray-800"
                                      onClick={() => onTxnEdit && onTxnEdit(r)}
                                    >
                                      EDIT
                                    </button>
                                    <button
                                      type="button"
                                      className="px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-60"
                                      title="Delete row"
                                      onClick={async()=>{
                                        try {
                                          const ba = txnBATab || '';
                                          const res = await fetch(`/api/transactions/${encodeURIComponent(ba)}`, {
                                            method: 'DELETE',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify(r),
                                          });
                                          if (!res.ok) {
                                            const msg = await res.text().catch(()=> '');
                                            throw new Error(msg || 'Failed to delete');
                                          }
                                          await requestTransactionsReload();
                                        } catch(e) {
                                          console.error(e);
                                          alert((e && e.message) || 'Failed to delete');
                                        }
                                      }}
                                    >
                                      DEL
                                    </button>
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                );
              })()}
            </div>
          );
        })()}
      </div>
    </div>
  );
}

window.TransactionsPanel = TransactionsPanel;
