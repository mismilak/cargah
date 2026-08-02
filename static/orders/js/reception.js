// ── helpers ──────────────────────────────────────────────
function show(id) {
    document.getElementById(id).classList.add('open');
}

function hide(id) {
    document.getElementById(id).classList.remove('open');
}

// ── مودال اصلی پذیرش ─────────────────────────────────────
document.getElementById('btn-open-reception').onclick = () => show('reception-modal');
document.getElementById('btn-close-modal').onclick = () => hide('reception-modal');
document.getElementById('btn-cancel').onclick = () => hide('reception-modal');

// ── انتخاب مشتری ─────────────────────────────────────────
document.getElementById('btn-pick-customer').onclick = () => {
    hide('reception-modal');
    show('customer-pick-modal');
    loadCustomers('');
};
document.getElementById('btn-close-pick').onclick = () => {
    hide('customer-pick-modal');
    show('reception-modal');
};

let searchTimer;
document.getElementById('customer-search').oninput = function () {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => loadCustomers(this.value), 300);
};

function loadCustomers(q) {
    fetch(`${CUSTOMER_LIST_URL}?q=${encodeURIComponent(q)}`)
        .then(r => r.json())
        .then(data => renderCustomers(data.customers));
}

function renderCustomers(list) {
    const el = document.getElementById('customer-list');
    if (!list.length) {
        el.innerHTML = '<p class="empty-state">مشتری‌ای یافت نشد.</p>';
        return;
    }
    el.innerHTML = list.map(c => `
    <div class="customer-item" data-id="${c.id}" data-name="${c.name}"
         data-workshop="${c.customer_workshop_name}" data-phone="${c.phone}"
         data-legal="${c.is_legal}">
      <strong>${c.name}</strong>
      ${c.customer_workshop_name && c.customer_workshop_name !== 'None' ? `<span> — ${c.customer_workshop_name}</span>` : ''}
      ${c.phone ? `<span class="muted">${c.phone}</span>` : ''}
      ${c.is_legal ? '<span class="badge">حقوقی</span>' : ''}
    </div>
  `).join('');
    el.querySelectorAll('.customer-item').forEach(item => {
        item.onclick = () => selectCustomer(item.dataset);
    });
}

function selectCustomer(d) {
    document.getElementById('selected-customer-id').value = d.id;
    const display = document.getElementById('selected-customer-display');
    display.innerHTML = `<strong>${d.name}</strong>${d.phone ? ' — ' + d.phone : ''}`;
    document.getElementById('btn-submit-reception').disabled = false;
    hide('customer-pick-modal');
    show('reception-modal');
}

// ── ایجاد مشتری جدید ─────────────────────────────────────
document.getElementById('btn-new-customer').onclick = () => {
    hide('customer-pick-modal');
    show('customer-create-modal');
};
document.getElementById('btn-close-create').onclick = () => {
    hide('customer-create-modal');
    show('customer-pick-modal');
};
document.getElementById('btn-back-to-pick').onclick = () => {
    hide('customer-create-modal');
    show('customer-pick-modal');
};

document.getElementById('customer-create-form').onsubmit = function (e) {
    e.preventDefault();
    const fd = new FormData(this);
    fetch(CUSTOMER_CREATE_URL, {
        method: 'POST',
        headers: {'X-CSRFToken': CSRF_TOKEN},
        body: fd,
    })
        .then(r => r.json())
        .then(data => {
            if (data.errors) {
                const errEl = document.getElementById('create-error');
                errEl.textContent = Object.values(data.errors).flat().join(' | ');
                errEl.style.display = 'block';
                return;
            }
            selectCustomer({id: data.id, name: data.name, phone: data.phone, is_legal: data.is_legal});
            hide('customer-create-modal');
            this.reset();
            document.getElementById('create-error').style.display = 'none';
        });
};

// ── فایل drag-and-drop ───────────────────────────────────
const dropZone = document.getElementById('file-drop-zone');
const fileInput = document.getElementById('file-input');
const preview = document.getElementById('file-preview');
let fileList = new DataTransfer();

dropZone.onclick = () => fileInput.click();
dropZone.ondragover = e => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
};
dropZone.ondragleave = () => dropZone.classList.remove('drag-over');
dropZone.ondrop = e => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    addFiles(e.dataTransfer.files);
};
fileInput.onchange = () => {
    addFiles(fileInput.files);
    fileInput.value = '';
};

function addFiles(files) {
    for (const f of files) fileList.items.add(f);
    fileInput.files = fileList.files;
    renderPreview();
}

function renderPreview() {
    preview.innerHTML = Array.from(fileList.files).map((f, i) =>
        `<div class="file-chip">${f.name} <span class="file-chip-remove" data-i="${i}">&times;</span></div>`
    ).join('');
    preview.querySelectorAll('.file-chip-remove').forEach(btn => {
        btn.onclick = () => {
            const dt = new DataTransfer();
            Array.from(fileList.files).forEach((f, i) => {
                if (i != btn.dataset.i) dt.items.add(f);
            });
            fileList = dt;
            fileInput.files = fileList.files;
            renderPreview();
        };
    });
}

// ── toast ─────────────────────────────────────────────────
const toast = document.getElementById('toast');
if (toast) {
    const progress = document.getElementById('toast-progress');
    progress.style.transition = 'width 5s linear';
    setTimeout(() => {
        progress.style.width = '0';
    }, 50);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 400);
    }, 5000);
}

// ── ویرایش ───────────────────────────────────────────────
let editOrderUrl = null;

document.querySelectorAll('.btn-edit').forEach(btn => {
    btn.addEventListener('click', () => {
        editOrderUrl = btn.dataset.url;
        document.getElementById('edit-description').value = btn.dataset.description;
        show('edit-modal');
    });
});

document.getElementById('btn-close-edit').onclick = () => hide('edit-modal');
document.getElementById('btn-cancel-edit').onclick = () => hide('edit-modal');

document.getElementById('edit-form').onsubmit = function (e) {
    e.preventDefault();
    const fd = new FormData(this);
    fetch(editOrderUrl, {
        method: 'POST',
        headers: {'X-CSRFToken': CSRF_TOKEN},
        body: fd,
    }).then(r => r.json()).then(data => {
        if (data.ok) {
            hide('edit-modal');
            location.reload();
        } else {
            const err = document.getElementById('edit-error');
            err.textContent = data.error || 'خطا';
            err.style.display = 'block';
        }
    });
};

// ── حذف ──────────────────────────────────────────────────
let deleteOrderUrl = null;

document.querySelectorAll('.btn-delete').forEach(btn => {
    btn.onclick = () => {
        deleteOrderUrl = btn.dataset.url;
        document.getElementById('delete-order-code').textContent = btn.dataset.code;
        show('delete-modal');
    };
});

document.getElementById('btn-close-delete').onclick = () => hide('delete-modal');
document.getElementById('btn-cancel-delete').onclick = () => hide('delete-modal');
document.getElementById('btn-confirm-delete').onclick = () => {
    fetch(deleteOrderUrl, {
        method: 'POST',
        headers: {'X-CSRFToken': CSRF_TOKEN},
    }).then(r => r.json()).then(data => {
        if (data.ok) location.reload();
    });
    hide('delete-modal');
};

// ── ارجاع ─────────────────────────────────────────────────
let referOrderUrl = null;

document.querySelectorAll('.btn-refer').forEach(btn => {
    btn.onclick = () => {
        referOrderUrl = btn.dataset.url;
        document.getElementById('refer-order-code').textContent = btn.dataset.code;
        show('refer-modal');
    };
});

document.getElementById('btn-close-refer').onclick = () => hide('refer-modal');
document.getElementById('btn-cancel-refer').onclick = () => hide('refer-modal');
document.getElementById('btn-confirm-refer').onclick = () => {
    const fd = new FormData();
    fd.append('unit', document.getElementById('refer-unit').value);
    fetch(referOrderUrl, {
        method: 'POST',
        headers: {'X-CSRFToken': CSRF_TOKEN},
        body: fd,
    }).then(r => r.json()).then(data => {
        if (data.ok) location.reload();
    });
    hide('refer-modal');
};


// ── جزئیات سفارش ─────────────────────────────────────────
document.querySelectorAll('.order-row').forEach(row => {
    row.addEventListener('click', (e) => {
        if (e.target.closest('button, a')) return;

        const detailUrl = row.dataset.detailUrl;
        if (!detailUrl) return;

        fetch(detailUrl)
            .then(r => {
                if (!r.ok) throw new Error('Network response was not ok');
                return r.json();
            })
            .then(data => {
                document.getElementById('detail-code').textContent = data.code || '—';
                document.getElementById('detail-customer').textContent = data.customer_name || '—';
                document.getElementById('detail-phone').textContent = data.customer_phone || '—';
                document.getElementById('detail-date').textContent = data.created_at || '—';
                document.getElementById('detail-created-by').textContent = data.created_by || '—';
                document.getElementById('detail-status').textContent = data.status || '—';
                document.getElementById('detail-description').textContent = data.description || '—';

                const attWrap = document.getElementById('detail-attachments');

                if (data.attachments && data.attachments.length > 0) {
                    attWrap.innerHTML = '';

                    data.attachments.forEach(att => {
                        const item = document.createElement('div');
                        item.className = 'attachment-item';

                        const fileName = att.name.split('/').pop();

                        if (att.kind === 'image') {
                            item.innerHTML = `
                                <a href="${att.url}" target="_blank">
                                    <img src="${att.url}" alt="پیش‌نمایش پیوست">
                                </a>
                            `;
                        } else if (att.kind === 'pdf') {
                            item.innerHTML = `
                                <iframe src="${att.url}" title="پیش‌نمایش PDF"></iframe>
                                <a href="${att.url}" target="_blank">باز کردن PDF</a>
                            `;
                        } else {
                            item.innerHTML = `
                                <div style="font-size: 2rem; color: #999;">📄</div>
                                <a href="${att.url}" download>${fileName}</a>
                            `;
                        }

                        attWrap.appendChild(item);
                    });
                } else {
                    attWrap.innerHTML = '<p class="empty-state">پیوستی وجود ندارد.</p>';
                }

                show('detail-modal');
            })
            .catch(err => {
                console.error('خطا در دریافت جزئیات:', err);
                alert('خطا در بارگذاری جزئیات سفارش');
            });
    });
});

document.getElementById('btn-close-detail').onclick = () => hide('detail-modal');



