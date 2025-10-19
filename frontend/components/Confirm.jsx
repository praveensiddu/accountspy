const ConfirmModal = ({ message, onConfirm, onCancel }) => (
  <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/40">
    <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-5">
      <h3 className="text-lg font-semibold mb-2">Confirm</h3>
      <p className="text-sm text-gray-700 mb-4">{message}</p>
      <div className="flex justify-end gap-2">
        <button onClick={onCancel} className="px-3 py-1.5 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300">Cancel</button>
        <button onClick={onConfirm} className="px-3 py-1.5 bg-red-600 text-white rounded-md hover:bg-red-700">Delete</button>
      </div>
    </div>
  </div>
);

window.showConfirm = (message) => {
  return new Promise((resolve) => {
    const mount = document.createElement('div');
    document.body.appendChild(mount);
    const root = ReactDOM.createRoot(mount);

    const handleClose = (result) => {
      try { root.unmount(); } catch (_) {}
      if (mount && mount.parentNode) mount.parentNode.removeChild(mount);
      resolve(result);
    };

    root.render(
      <ConfirmModal
        message={message}
        onConfirm={() => handleClose(true)}
        onCancel={() => handleClose(false)}
      />
    );
  });
};
