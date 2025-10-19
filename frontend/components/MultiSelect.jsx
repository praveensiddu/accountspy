const { useState, useRef, useEffect } = React;

const MultiSelect = ({ options, selected, onChange, placeholder = 'Select...', label }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const containerRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleOption = (value) => {
    if ((selected || []).includes(value)) {
      onChange((selected || []).filter((v) => v !== value));
    } else {
      onChange([...(selected || []), value]);
    }
  };

  const filtered = (options || []).filter((o) =>
    (o.label || '').toLowerCase().includes((search || '').toLowerCase())
  );

  const allSelected = (selected || []).length === (options || []).length && (options || []).length > 0;

  const selectAll = (e) => {
    e.stopPropagation();
    if (allSelected) onChange([]);
    else onChange((options || []).map((o) => o.value));
  };

  return (
    <div className="relative w-full" ref={containerRef}>
      {label && (
        <label className="block text-sm font-medium mb-1 text-gray-700">{label}</label>
      )}
      <div
        className="flex flex-wrap gap-1 border border-gray-300 rounded-md p-2 bg-white cursor-pointer focus-within:ring-2 focus-within:ring-blue-500"
        onClick={() => setIsOpen((o) => !o)}
      >
        {(!selected || selected.length === 0) && (
          <span className="text-gray-400 text-sm">{placeholder}</span>
        )}

        {(selected || []).map((val) => {
          const opt = (options || []).find((o) => o.value === val);
          return (
            <span
              key={val}
              className="bg-blue-100 text-blue-700 px-2 py-0.5 text-sm rounded-full flex items-center"
            >
              {opt ? opt.label : val}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onChange((selected || []).filter((v) => v !== val));
                }}
                className="ml-1 text-blue-500 hover:text-blue-700 focus:outline-none"
                type="button"
              >
                ×
              </button>
            </span>
          );
        })}
      </div>

      {isOpen && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg max-h-64 overflow-y-auto">
          <div className="sticky top-0 bg-gray-50 p-2 border-b border-gray-200 flex items-center">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search..."
              className="w-full border border-gray-300 rounded-md px-2 py-1 text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
            <button onClick={selectAll} className="ml-2 text-xs text-blue-600 hover:underline" type="button">
              {allSelected ? 'Clear All' : 'Select All'}
            </button>
          </div>

          {filtered.length === 0 ? (
            <p className="p-3 text-gray-500 text-sm">No matches found.</p>
          ) : (
            filtered.map((opt) => (
              <label
                key={opt.value}
                className="flex items-center gap-2 px-3 py-2 hover:bg-gray-100 cursor-pointer text-sm"
                onClick={(e) => e.stopPropagation()}
              >
                <input
                  type="checkbox"
                  checked={(selected || []).includes(opt.value)}
                  onChange={() => toggleOption(opt.value)}
                  className="form-checkbox h-4 w-4 text-blue-600"
                />
                <span>{opt.label}</span>
              </label>
            ))
          )}
        </div>
      )}
    </div>
  );
};

window.MultiSelect = MultiSelect;
