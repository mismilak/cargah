(function () {
    // Modal
    const modal = document.getElementById('reception-modal');
    const btnOpen = document.getElementById('btn-open-reception');
    const btnClose = document.getElementById('btn-close-modal');
    const btnCancel = document.getElementById('btn-cancel');

    function openModal() {
        modal && modal.classList.add('open');
    }

    function closeModal() {
        modal && modal.classList.remove('open');
    }

    btnOpen && btnOpen.addEventListener('click', openModal);
    btnClose && btnClose.addEventListener('click', closeModal);
    btnCancel && btnCancel.addEventListener('click', closeModal);
    modal && modal.addEventListener('click', function (e) {
        if (e.target === modal) closeModal();
    });

    // File drop zone
    const dropZone = document.getElementById('file-drop-zone');
    const fileInput = document.getElementById('file-input');
    const filePreview = document.getElementById('file-preview');

    if (dropZone && fileInput) {
        dropZone.addEventListener('dragover', function (e) {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });
        dropZone.addEventListener('dragleave', function () {
            dropZone.classList.remove('drag-over');
        });
        dropZone.addEventListener('drop', function (e) {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            updateFiles(e.dataTransfer.files);
        });
        fileInput.addEventListener('change', function () {
            updateFiles(fileInput.files);
        });
    }

    let selectedFiles = [];

    function updateFiles(newFiles) {
        for (let f of newFiles) selectedFiles.push(f);
        renderPreview();
        syncInput();
    }

    function renderPreview() {
        if (!filePreview) return;
        filePreview.innerHTML = '';
        selectedFiles.forEach(function (f, i) {
            const chip = document.createElement('div');
            chip.className = 'file-chip';
            chip.innerHTML = f.name + ' <span class="file-chip-remove" data-i="' + i + '">&times;</span>';
            filePreview.appendChild(chip);
        });
        filePreview.querySelectorAll('.file-chip-remove').forEach(function (btn) {
            btn.addEventListener('click', function () {
                selectedFiles.splice(parseInt(btn.dataset.i), 1);
                renderPreview();
                syncInput();
            });
        });
    }

    function syncInput() {
        if (!fileInput) return;
        const dt = new DataTransfer();
        selectedFiles.forEach(function (f) {
            dt.items.add(f);
        });
        fileInput.files = dt.files;
    }

    // Toast auto-dismiss
    const toast = document.getElementById('toast');
    if (toast) {
        setTimeout(function () {
            toast.style.transition = 'opacity .4s';
            toast.style.opacity = '0';
            setTimeout(function () {
                toast.remove();
            }, 400);
        }, 5000);
    }

    // Back button — set href from outside
    // Usage: document.getElementById('btn-back').href = '/your/back/url/';
})();

