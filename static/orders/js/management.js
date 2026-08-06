(function () {
    const form = document.getElementById('service-form');
    const tbody = document.getElementById('service-tbody');
    const serviceIdInput = document.getElementById('service-id');
    const btnSubmit = document.getElementById('btn-submit');

    const workshopId = window.location.pathname.match(/\/(\d+)\//)?.[1];

    form.addEventListener('submit', (e) => {
        if (form.dataset.submitting) {
            e.preventDefault();
            return;
        }
        const serviceId = serviceIdInput.value;
        form.action = serviceId
            ? `/${workshopId}/management/edit/${serviceId}/`
            : '';
        form.dataset.submitting = '1';
    });

    tbody.addEventListener('click', (e) => {
        const btn = e.target;

        if (btn.classList.contains('btn-edit')) {
            serviceIdInput.value = btn.dataset.id;
            document.getElementById('service-name').value = btn.dataset.name;
            document.getElementById('service-machine').value = btn.dataset.machine;
            document.getElementById('service-unit').value = btn.dataset.unit;
            document.getElementById('service-price').value = btn.dataset.price;
            btnSubmit.textContent = 'ذخیره';
        }

        if (btn.classList.contains('btn-delete')) {
            if (!confirm('آیا از حذف این خدمت اطمینان دارید؟')) return;
            const f = document.createElement('form');
            f.method = 'POST';
            f.action = `/${workshopId}/management/delete/${btn.dataset.id}/`;
            f.innerHTML = `<input type="hidden" name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]').value}">`;
            document.body.appendChild(f);
            f.submit();
        }
    });
})();


const URLS = {
    orderDetail: "{% url 'orders:order_detail' workshop.id 0 %}".replace('/0/', '/'),
    orderAction: "{% url 'orders:order_action' workshop.id 0 %}".replace('/0/', '/'),
};

document.querySelectorAll('.order-row').forEach(row => {
    row.addEventListener('click', () => openOrderModal(row.dataset.id));
});

function openOrderModal(orderId) {
    fetch(URLS.orderDetail + orderId + '/')
        .then(r => r.json())
        .then(data => {
            document.getElementById('modal-title').textContent = 'سفارش ' + data.code;
            document.getElementById('modal-body').innerHTML =
                `<b>مشتری:</b> ${data.customer}<br>
                 <b>وضعیت:</b> ${data.status_display}<br>
                 <b>تاریخ:</b> ${data.created_at}<br>
                 <b>توضیحات:</b> ${data.description || '—'}`;
            buildActions(orderId, data);
            const modal = document.getElementById('order-modal');
            modal.style.display = 'flex';
        });
}

function buildActions(orderId, data) {
    const wrap = document.getElementById('modal-actions');
    wrap.innerHTML = '';
    const post = (action, label, style) => {
        const f = document.createElement('form');
        f.method = 'post';
        f.action = URLS.orderAction + orderId + '/';
        f.innerHTML = `<input type="hidden" name="csrfmiddlewaretoken" value="${getCookie('csrftoken')}">
                       <input type="hidden" name="action" value="${action}">
                       <button type="submit" class="btn-primary" style="${style}">${label}</button>`;
        wrap.appendChild(f);
    };
    if (!data.is_stopped && !data.is_archived) {
        post('reception', '📥 پذیرش', '');
        post('technical', '🔧 فنی', '');
        post('accounting', '💰 حسابداری', '');
        post('done', '✅ تکمیل', 'background:#22c55e;');
        post('stop', '⛔ توقف', 'background:#ef4444;');
    }
    if (!data.is_archived) {
        post('archive', '📦 آرشیو', 'background:#64748b;');
    }
}

function closeOrderModal() {
    document.getElementById('order-modal').style.display = 'none';
}

function getCookie(name) {
    return document.cookie.split(';').map(c => c.trim())
        .find(c => c.startsWith(name + '='))?.split('=')[1] || '';
}

