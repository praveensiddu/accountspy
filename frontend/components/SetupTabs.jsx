function SetupTabs({
  setupTab,
  setSetupTab,
  prepYear,
  setPrepYear,
  loading,
  items,
  companies,
  companyRecords,
  bankaccounts,
  groups,
  owners,
  taxCategories,
  transactionTypes,
  banks,
  load,
}) {
  const TabButton = window.TabButton;
  return (
    <div className="tabcontent">
      <div className="actions" style={{ marginBottom: 12, flexWrap: 'wrap' }}>
        <TabButton active={setupTab==='settings'} onClick={() => setSetupTab('settings')}>Settings</TabButton>
        <TabButton active={setupTab==='banks'} onClick={() => setSetupTab('banks')}>Banks</TabButton>
        <TabButton active={setupTab==='bankaccounts'} onClick={() => setSetupTab('bankaccounts')}>Bank Accounts</TabButton>
        <TabButton active={setupTab==='companies'} onClick={() => setSetupTab('companies')}>Company Records</TabButton>
        <TabButton active={setupTab==='properties'} onClick={() => setSetupTab('properties')}>Properties</TabButton>
        <TabButton active={setupTab==='groups'} onClick={() => setSetupTab('groups')}>Groups</TabButton>
        <TabButton active={setupTab==='owners'} onClick={() => setSetupTab('owners')}>Owners</TabButton>
        <TabButton active={setupTab==='taxcats'} onClick={() => setSetupTab('taxcats')}>Tax Categories</TabButton>
        <TabButton active={setupTab==='txtypes'} onClick={() => setSetupTab('txtypes')}>Transaction Types</TabButton>
      </div>

      {setupTab === 'settings' && (
        <div className="card">
          <div className="row" style={{ alignItems:'flex-end' }}>
            <div className="col">
              <label>Prepare for year<br/>
                {(() => {
                  const yearOptions = Array.from({ length: 38 }, (_, i) => 2023 + i).map(y => ({ value: String(y), label: String(y) }));
                  const selectedArr = prepYear ? [String(prepYear)] : [];
                  return (
                    <MultiSelect
                      options={yearOptions}
                      selected={selectedArr}
                      onChange={(arr)=>{ const y = (arr && arr[0]) || ''; setPrepYear(y); }}
                      placeholder="Select year..."
                    />
                  );
                })()}
              </label>
            </div>
            <div className="col" style={{ textAlign:'right' }}>
              <button
                type="button"
                style={{ padding:'6px 12px', background:'#2563eb', color:'#fff', border:'none', borderRadius:'4px', cursor:'pointer' }}
                onClick={async ()=>{
                  try {
                    const y = String(prepYear||'');
                    if (!y) { alert('Select a year'); return; }
                    const res = await fetch('/api/settings/prepyear', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ year: y }) });
                    if (!res.ok) { const t = await res.text().catch(()=> ''); throw new Error(t || 'prepyear failed'); }
                    alert('Year prepared: ' + y);
                  } catch (e2) { alert(e2.message || 'Failed'); }
                }}
              >prepare</button>
            </div>
          </div>
        </div>
      )}

      {setupTab === 'properties' && (
        <PropertiesPanelExt items={items} companies={companies} loading={loading} reload={load} />
      )}

      {setupTab === 'companies' && (
        <CompaniesPanelExt companyRecords={companyRecords} loading={loading} reload={load} />
      )}

      {setupTab === 'banks' && (
        <BanksPanelExt banks={banks} loading={loading} reload={load} />
      )}

      {setupTab === 'taxcats' && (
        <TaxCategoriesPanelExt taxCategories={taxCategories} loading={loading} reload={load} />
      )}

      {setupTab === 'txtypes' && (
        <TransactionTypesPanelExt transactionTypes={transactionTypes} loading={loading} reload={load} />
      )}

      {setupTab === 'bankaccounts' && (
        <BankAccountsPanelExt bankaccounts={bankaccounts} loading={loading} reload={load} banks={banks} />
      )}

      {setupTab === 'groups' && (
        <GroupsPanelExt groups={groups} loading={loading} reload={load} items={items} />
      )}

      {setupTab === 'owners' && (
        <OwnersPanelExt owners={owners} loading={loading} reload={load} bankaccounts={bankaccounts} items={items} companies={companies} />
      )}
    </div>
  );
}

window.SetupTabs = SetupTabs;
