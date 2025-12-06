const { useState, useEffect, useCallback } = React;

function useRentalSummary(api, topTab) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({ property:'', rent:'', commissions:'', insurance:'', proffees:'', mortgageinterest:'', repairs:'', tax:'', utilities:'', depreciation:'', hoa:'', other:'', costbasis:'', renteddays:'', profit:'' });

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.listRentalSummary();
      setRows(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error(e);
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    // Initial load so data is ready even before visiting the tab
    load();
  }, [load]);

  useEffect(() => {
    if (topTab === 'rentalsummary') load();
  }, [topTab, load]);

  return { rentalRows: rows, rentalLoading: loading, rentalFilters: filters, setRentalFilters: setFilters, loadRentalSummary: load };
}

function useRentTracker(api, topTab) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.listRentTracker();
      setRows(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error(e);
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    // Initial load so data is ready even before visiting the tab
    load();
  }, [load]);

  useEffect(() => {
    if (topTab === 'renttracker') load();
  }, [topTab, load]);

  return { rentTrackerRows: rows, rentTrackerLoading: loading, loadRentTracker: load };
}

function useCompanySummary(api, topTab) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({ Name:'', income:'', rentpassedtoowners:'', bankfees:'', c_auto:'', c_donate:'', c_entertainment:'', c_internet:'', c_license:'', c_mobile:'', c_off_exp:'', c_parktoll:'', c_phone:'', c_website:'', ignore:'', insurane:'', proffees:'', utilities:'', profit:'' });

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.listCompanySummary();
      setRows(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error(e);
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (topTab === 'companysummary') load();
  }, [topTab, load]);

  return { companyRows: rows, companyLoading: loading, companyFilters: filters, setCompanyFilters: setFilters, loadCompanySummary: load };
}

window.useSummaries = { useRentalSummary, useRentTracker, useCompanySummary };
