function escapeHtml(s) {
    return String(s ?? '').replace(/[&<>"']/g, c =>
        ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
}

function getCookie(name) {
    const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
}

function formatNumber(num) {
    return parseFloat(num).toLocaleString('en-US');
}

function formatAmountInput(input) {
    let value = input.value.replace(/[^0-9]/g, '');
    input.value = value ? parseInt(value).toLocaleString('en-US') : '';
}

function parseAmount(formatted) {
    return formatted.replace(/[^0-9]/g, '');
}

let selectedPayDate = '';
let selectedCheckDue = '';

// تبدیل تاریخ شمسی به میلادی
function jalaliToGregorian(jalaliStr) {
    if (!jalaliStr) return '';
    const parts = jalaliStr.split('/');
    if (parts.length !== 3) return '';

    let jy = parseInt(parts[0]), jm = parseInt(parts[1]), jd = parseInt(parts[2]);

    // الگوریتم تبدیل شمسی به میلادی
    jy += 1595;
    let days = -355779 + (365 * jy) + (Math.floor(jy / 33) * 8) +
        Math.floor(((jy % 33) + 3) / 4) + jd +
        (jm < 7 ? (jm - 1) * 31 : ((jm - 7) * 30) + 186);

    let gy = 400 * Math.floor(days / 146097);
    days %= 146097;
    if (days > 36524) {
        gy += 100 * Math.floor(--days / 36524);
        days %= 36524;
        if (days >= 365) days++;
    }
    gy += 4 * Math.floor(days / 1461);
    days %= 1461;
    if (days > 365) {
        gy += Math.floor((days - 1) / 365);
        days = (days - 1) % 365;
    }

    let gd = days + 1;
    const sal_a = [0, 31, (gy % 4 === 0 && gy % 100 !== 0) || gy % 400 === 0 ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    let gm = 0;
    for (gm = 0; gm < 13 && gd > sal_a[gm]; gm++) gd -= sal_a[gm];

    return `${gy}-${String(gm).padStart(2, '0')}-${String(gd).padStart(2, '0')}`;
}


function gregorianToJalali(gregorianDateString) {
    if (!gregorianDateString) return '';
    const gDate = new Date(gregorianDateString);
    const pDate = new persianDate(gDate);
    return pDate.format('YYYY/MM/DD');
}

function toJalaliDateTime(gregorianDateTimeString) {
    if (!gregorianDateTimeString) return '';
    const gDate = new Date(gregorianDateTimeString);
    const pDate = new persianDate(gDate);
    return pDate.format('YYYY/MM/DD HH:mm:ss');
}

// راه‌اندازی datepicker
$(function () {
    $('#pay-date').persianDatepicker({
        format: 'YYYY/MM/DD',
        autoClose: true,
        initialValue: false,
        calendar: {persian: {locale: 'fa'}},
        onSelect: function (unix) {
            const d = new persianDate(unix);
            selectedPayDate = d.year() + '/' +
                String(d.month()).padStart(2, '0') + '/' +
                String(d.date()).padStart(2, '0');
            document.getElementById('pay-date').value = selectedPayDate;
        }
    });
    $('#pay-check-due').persianDatepicker({
        format: 'YYYY/MM/DD',
        autoClose: true,
        initialValue: false,
        calendar: {persian: {locale: 'fa'}},
        onSelect: function (unix) {
            const d = new persianDate(unix);
            selectedCheckDue = d.year() + '/' +
                String(d.month()).padStart(2, '0') + '/' +
                String(d.date()).padStart(2, '0');
            document.getElementById('pay-check-due').value = selectedCheckDue;
        }
    });
});

// ---- Acc tabs ----
document.querySelectorAll('.acc-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.acc-tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.acc-tab-pane').forEach(p => p.style.display = 'none');
        btn.classList.add('active');
        document.getElementById('acc-tab-' + btn.dataset.tab).style.display = '';
    });
});

// ---- Invoice modal inner tabs ----
document.querySelectorAll('.inv-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.inv-tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.inv-tab-pane').forEach(p => p.style.display = 'none');
        btn.classList.add('active');
        document.getElementById('inv-tab-' + btn.dataset.itab).style.display = '';
    });
});

// ---- سفارش‌های تاییدشده ----
let currentInvoiceId = null;
let currentRemainingAmount = 0;
let currentOrderId = null;


document.querySelectorAll('.approved-order-row').forEach(row => {
    row.addEventListener('click', () => openInvoiceModal(row.dataset.orderId));
});

function openInvoiceModal(orderId) {
    currentOrderId = orderId;

    document.querySelectorAll('.inv-tab-btn').forEach((b, i) => b.classList.toggle('active', i === 0));
    document.querySelectorAll('.inv-tab-pane').forEach((p, i) => p.style.display = i === 0 ? '' : 'none');

    document.getElementById('inv-detail-body').innerHTML = '<tr><td colspan="2">در حال بارگذاری...</td></tr>';
    document.getElementById('invoiceModal').style.display = 'flex';

    fetch(`/orders/api/order/${orderId}/activities/`)
        .then(r => r.json())
        .then(data => {
            const info = data.order_info;
            document.getElementById('inv-order-code').textContent = data.order_code || info.code;

            document.getElementById('inv-detail-body').innerHTML = `
                <tr><td>کد سفارش</td><td>${escapeHtml(info.code)}</td></tr>
                <tr><td>مشتری</td><td>${escapeHtml(info.customer)}</td></tr>
                <tr><td>موبایل</td><td>${escapeHtml(info.phone)}</td></tr>
                <tr><td>ثبت‌کننده</td><td>${escapeHtml(info.created_by)}</td></tr>
                <tr><td>تاریخ</td><td>${escapeHtml(toJalaliDateTime(info.created_at))}</td></tr>
                <tr><td>وضعیت</td><td>${escapeHtml(info.status)}</td></tr>
                <tr><td>توضیحات</td><td>${escapeHtml(info.description)}</td></tr>`;

            const activities = data.activities || [];
            if (activities.length) {
                const rows = activities.map((a, i) => `
                    <tr>
                        <td>${i + 1}</td>
                        <td>${escapeHtml(a.service_name || a.service__name)}</td>
                        <td>${escapeHtml(a.service__machine_name || '')}</td>
                        <td>${formatNumber(a.duration_value)} ${escapeHtml(a.unit || a.service__unit || '')}</td>
                        <td>${formatNumber(a.price)} ریال</td>
                        <td>${formatNumber(parseFloat(a.duration_value) * parseFloat(a.price))} ریال</td>
                    </tr>`).join('');
                document.getElementById('inv-services-body').innerHTML = `
                    <div style="overflow-x:auto;">
                    <table class="orders-table">
                        <thead><tr><th>#</th><th>خدمت</th><th>دستگاه</th><th>مقدار</th><th>قیمت واحد</th><th>جمع</th></tr></thead>
                        <tbody>${rows}</tbody>
                    </table></div>`;
            } else {
                document.getElementById('inv-services-body').innerHTML = '<p class="empty-state">خدمتی ثبت نشده.</p>';
            }
        });

    fetch(`/billing/${WORKSHOP_ID}/order/${currentOrderId}/invoice-detail/`)
        .then(r => r.json())
        .then(data => {
            if (!data.ok) return;
            currentInvoiceId = data.invoice_id;
            currentRemainingAmount = parseFloat(data.remaining_amount);
            renderPaymentTab(data);
        });
}

function renderPaymentTab(data) {
    const remaining = parseFloat(data.remaining_amount);

    document.getElementById('inv-payment-summary').innerHTML = `
        <div style="display:flex;gap:1.5rem;flex-wrap:wrap;">
            <span>مبلغ فاکتور: <b>${formatNumber(data.final_amount)} ریال</b></span>
            <span>پرداخت‌شده: <b style="color:#0f766e;">${formatNumber(data.paid_amount)} ریال</b></span>
            <span>مانده: <b style="color:${remaining > 0 ? '#dc2626' : '#0f766e'};">${formatNumber(remaining)} ریال</b></span>
            <span>وضعیت: <b>${escapeHtml(data.status_display)}</b></span>
        </div>`;

    document.getElementById('remaining-amount-value').textContent = formatNumber(remaining) + ' ریال';

    const payments = data.payments || [];
    if (payments.length) {
        document.getElementById('payments-list').innerHTML =
            '<div style="font-size:.85rem;font-weight:600;color:#475569;margin-bottom:.5rem;">پرداخت‌های ثبت‌شده</div>' +
            payments.map(p => {
                let badgeColor = '#475569';
                let badgeBg = '#e2e8f0';

                if (p.method === 'cash') {
                    badgeColor = '#166534';
                    badgeBg = '#dcfce7';
                } else if (p.method === 'transfer') {
                    badgeColor = '#1d4ed8';
                    badgeBg = '#dbeafe';
                } else if (p.method === 'check') {
                    badgeColor = '#92400e';
                    badgeBg = '#fef3c7';
                }

                return `
    <div class="payment-item" style="cursor:pointer;" onclick="openPaymentDetail(${JSON.stringify(p).replace(/"/g, '&quot;')})">
        <div style="display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;">
            <span class="payment-item__amount">${formatNumber(p.amount)} ریال</span>
            <span style="
                display:inline-block;
                padding:.15rem .5rem;
                border-radius:999px;
                background:${badgeBg};
                color:${badgeColor};
                font-size:.78rem;
                font-weight:600;
            ">
                ${escapeHtml(p.method_display)}
            </span>
            ${p.check_number ? `<span class="payment-item__meta">چک: ${escapeHtml(p.check_number)}</span>` : ''}
        </div>
        <div class="payment-item__meta">
            ${escapeHtml(gregorianToJalali(p.paid_at))}${p.notes ? ` — ${escapeHtml(p.notes)}` : ''}
        </div>
    </div>`;
            }).join('');


    } else {
        document.getElementById('payments-list').innerHTML = '<p style="font-size:.85rem;color:#94a3b8;">پرداختی ثبت نشده.</p>';
    }
}

function fillFullAmount() {
    // مقدار currentRemainingAmount که قبلاً در openInvoiceModal ست شده است
    if (currentRemainingAmount > 0) {
        const amountInput = document.getElementById('pay-amount');
        amountInput.value = parseInt(currentRemainingAmount).toLocaleString('en-US');
    }
}

let currentPaymentId = null;
let currentCheckStatus = null;

function openPaymentDetail(p) {
    currentPaymentId = p.id;
    currentCheckStatus = p.check_status || null;

    const isCheck = p.method === 'check';

    document.getElementById('paymentDetailBody').innerHTML = `
        <div style="margin-bottom:1rem;padding:.85rem 1rem;border-radius:10px;background:#f8fafc;border:1px solid #e2e8f0;">
            <div style="font-size:.85rem;color:#64748b;margin-bottom:.25rem;">مبلغ پرداخت</div>
            <div style="font-size:1.4rem;font-weight:700;color:#0f766e;direction:ltr;">
                ${formatNumber(p.amount)} ریال
            </div>
        </div>

        <table class="orders-table">
            <tbody>
                <tr><td>روش پرداخت</td><td>${escapeHtml(p.method_display || '—')}</td></tr>
                <tr><td>تاریخ پرداخت</td><td>${escapeHtml(gregorianToJalali(p.paid_at))}</td></tr>
                <tr><td>یادداشت</td><td>${escapeHtml(p.notes || '—')}</td></tr>
                ${isCheck ? `
                    <tr><td>شماره چک</td><td>${escapeHtml(p.check_number || '—')}</td></tr>
                    <tr><td>بانک</td><td>${escapeHtml(p.check_bank || '—')}</td></tr>
                    <tr><td>تاریخ سررسید</td><td>${escapeHtml(p.check_due_date ? gregorianToJalali(p.check_due_date) : '—')}</td></tr>
                    <tr><td>وضعیت چک</td><td>${escapeHtml(p.check_status_display || '—')}</td></tr>
                ` : ''}
            </tbody>
        </table>
    `;

    const actions = document.getElementById('checkStatusActions');
    if (isCheck && actions) {
        actions.style.display = 'block';
        actions.dataset.paymentId = p.id;
        actions.dataset.currentStatus = p.check_status || '';
    } else if (actions) {
        actions.style.display = 'none';
    }

    document.getElementById('paymentDetailModal').style.display = 'flex';
}

function changeCheckStatus(status) {
    if (!currentPaymentId) return;

    fetch(`/billing/${WORKSHOP_ID}/payment/${currentPaymentId}/check-status/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({status}).toString(),
    })
        .then(r => r.json())
        .then(data => {
            if (!data.ok) {
                alert(data.error || 'خطا در تغییر وضعیت چک');
                return;
            }

            currentCheckStatus = data.check_status;
            document.getElementById('paymentDetailModal').style.display = 'none';

            fetch(`/billing/${WORKSHOP_ID}/order/${currentOrderId}/invoice-detail/`)
                .then(r => r.json())
                .then(d => {
                    if (d.ok) renderPaymentTab(d);
                });
        });
}


document.getElementById('paymentDetailModal').addEventListener('click', function (e) {
    if (e.target === this) this.style.display = 'none';
});


function toggleCheckFields() {
    const isCheck = document.getElementById('pay-method').value === 'check';
    const cf = document.getElementById('check-fields');
    cf.style.display = isCheck ? 'grid' : 'none';
}

function submitPayment() {
    if (!currentInvoiceId) return;
    const method = document.getElementById('pay-method').value;
    const amount = parseAmount(document.getElementById('pay-amount').value);
    const paid_at = jalaliToGregorian(selectedPayDate);
    const notes = document.getElementById('pay-notes').value;

    if (!amount || !paid_at) {
        alert('مبلغ و تاریخ پرداخت الزامی است.');
        return;
    }
    if (amount > currentRemainingAmount) {
        alert(`مبلغ وارد شده (${formatNumber(amount)}) بیشتر از مانده فاکتور (${formatNumber(currentRemainingAmount)}) است.`);
        return;
    }

    const body = new URLSearchParams({method, amount: amount, paid_at, notes});
    if (method === 'check') {
        body.append('check_number', document.getElementById('pay-check-number').value);
        body.append('check_bank', document.getElementById('pay-check-bank').value);
        body.append('check_due_date', jalaliToGregorian(selectedCheckDue));
        body.append('check_status', document.getElementById('pay-check-status').value);
    }

    fetch(`/billing/${WORKSHOP_ID}/invoice/${currentInvoiceId}/payment/`, {
        method: 'POST',
        headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/x-www-form-urlencoded'},
        body: body.toString(),
    })
        .then(r => r.json())
        .then(data => {
            if (!data.ok) {
                alert(data.error || 'خطا در ثبت پرداخت');
                return;
            }

            // بارگذاری مجدد اطلاعات فاکتور با استفاده از currentOrderId
            fetch(`/billing/${WORKSHOP_ID}/order/${currentOrderId}/invoice-detail/`)
                .then(r => r.json())
                .then(d => {
                    if (d.ok) renderPaymentTab(d);
                });

            // پاک‌کردن فیلدها فقط بعد از موفقیت
            document.getElementById('pay-amount').value = '';
            document.getElementById('pay-date').value = '';
            document.getElementById('pay-notes').value = '';
            selectedPayDate = '';
            selectedCheckDue = '';

            if (method === 'check') {
                document.getElementById('pay-check-number').value = '';
                document.getElementById('pay-check-bank').value = '';
                document.getElementById('pay-check-due').value = '';
            }
        });
}


function closeInvoiceModal() {
    document.getElementById('invoiceModal').style.display = 'none';
    currentInvoiceId = null;
}

document.getElementById('invoiceModal').addEventListener('click', function (e) {
    if (e.target === this) closeInvoiceModal();
});

// ---- سفارش‌های ارجاعی ----
document.querySelectorAll('.order-row').forEach(row => {
    row.addEventListener('click', function () {
        const orderId = this.dataset.orderId;
        fetch(`/orders/api/order/${orderId}/activities/`)
            .then(r => r.json())
            .then(data => {
                const info = data.order_info;
                document.getElementById('detailOrderCode').textContent = data.order_code;
                document.getElementById('detailInfoBody').innerHTML = `
                    <tr><td>کد سفارش</td><td>${escapeHtml(info.code)}</td></tr>
                    <tr><td>مشتری</td><td>${escapeHtml(info.customer)}</td></tr>
                    <tr><td>موبایل</td><td>${escapeHtml(info.phone)}</td></tr>
                    <tr><td>ثبت‌کننده</td><td>${escapeHtml(info.created_by)}</td></tr>
                    <tr><td>تاریخ</td><td>${escapeHtml(toJalaliDateTime(info.created_at))}</td></tr>
                    <tr><td>وضعیت</td><td>${escapeHtml(info.status)}</td></tr>
                    <tr><td>تعداد</td><td>${escapeHtml(String(info.count_request))}</td></tr>
                    <tr><td>توضیحات</td><td>${escapeHtml(info.description)}</td></tr>`;
                document.getElementById('orderDetailModal').style.display = 'flex';
            });
    });
});

document.getElementById('orderDetailModal').addEventListener('click', function (e) {
    if (e.target === this) closeDetailModal();
});

function closeDetailModal() {
    document.getElementById('orderDetailModal').style.display = 'none';
}

// ---- ارجاع ----
let currentReferOrderId, currentReferUrl;
document.querySelectorAll('.btn-refer').forEach(btn => {
    btn.addEventListener('click', () => {
        currentReferOrderId = btn.dataset.orderId;
        currentReferUrl = btn.dataset.url;
        document.getElementById('refer-order-code').textContent = btn.dataset.code;
        document.getElementById('refer-modal').style.display = 'flex';
    });
});

function closeReferModal() {
    document.getElementById('refer-modal').style.display = 'none';
}

document.getElementById('btn-cancel-refer').addEventListener('click', closeReferModal);
document.getElementById('btn-close-refer').addEventListener('click', closeReferModal);
document.getElementById('refer-modal').addEventListener('click', function (e) {
    if (e.target === this) closeReferModal();
});
document.getElementById('btn-confirm-refer').addEventListener('click', () => {
    const target = document.getElementById('refer-unit').value;
    fetch(currentReferUrl, {
        method: 'POST',
        headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/x-www-form-urlencoded'},
        body: `target_unit=${target}`,
    }).then(r => r.json()).then(data => {
        if (data.ok) location.reload();
        else alert(data.error || 'خطا در ارجاع سفارش');
    });
});

// ---- پیش‌فاکتور ----
function openProforma(btn) {
    const orderId = btn.dataset.orderId;
    document.getElementById('proformaContent').innerHTML = 'در حال بارگذاری...';
    document.getElementById('proformaModal').style.display = 'flex';
    fetch(`/orders/api/order/${orderId}/activities/`)
        .then(r => r.json())
        .then(data => {
            const info = data.order_info;
            const activities = data.activities;
            const groups = {};
            activities.forEach(a => {
                const key = `${a.service_id}_${a.price}`;
                if (!groups[key]) groups[key] = {
                    name: a.service_name, unit: a.unit || '',
                    price: parseFloat(a.price), qty: 0, total: 0
                };
                groups[key].qty += parseFloat(a.duration_value);
                groups[key].total += parseFloat(a.duration_value) * parseFloat(a.price);
            });
            const rows = Object.values(groups);
            const invoiceTotal = rows.reduce((s, r) => s + r.total, 0);
            const prevDebt = parseFloat(data.order_info.prev_debt || 0);
            const grandTotal = invoiceTotal + prevDebt;
            const rowsHtml = rows.map((r, i) => `
                <tr>
                    <td>${i + 1}</td><td>${escapeHtml(r.name)}</td>
                    <td>${formatNumber(r.qty)}</td>
                    <td>${formatNumber(r.price)} ریال</td>
                    <td>${formatNumber(r.total)} ریال</td>
                </tr>`).join('');
            document.getElementById('proformaContent').innerHTML = `
                <div class="proforma-wrap" id="printArea">
                    <div class="proforma-header">
                        <h2>پیش‌فاکتور</h2>
                        <p>تاریخ: ${escapeHtml(toJalaliDateTime(info.created_at))}</p>
                        <p>شماره سفارش: ${escapeHtml(info.code)}</p>
                        <p>مشتری: ${escapeHtml(info.customer)}</p>
                    </div>
                    <div class="proforma-workshop">${escapeHtml(data.workshop_name || '')}</div>
                    <table class="proforma-table">
                        <thead><tr><th>#</th><th>شرح خدمت</th><th>مقدار</th><th>قیمت واحد</th><th>جمع</th></tr></thead>
                        <tbody>${rowsHtml}</tbody>
                    </table>
                    <div class="proforma-totals">
                        <p>جمع فاکتور: ${formatNumber(invoiceTotal)} ریال</p>
                        ${prevDebt > 0 ? `<p>مانده حساب قبلی: ${formatNumber(prevDebt)} ریال</p>` : ''}
                        ${prevDebt > 0 ? `<p class="grand-total">جمع کل: ${formatNumber(grandTotal)} ریال</p>` : ''}
                    </div>
                </div>`;
        });
}

// ---- فاکتور ----
function openProformaConfirmed(btn) {
    const orderId = btn.dataset.orderId;
    document.getElementById('invoiceContent').innerHTML = 'در حال بارگذاری...';
    document.getElementById('proformaModalConfirm').style.display = 'flex';
    fetch(`/orders/api/order/${orderId}/activities/`)
        .then(r => r.json())
        .then(data => {
            const info = data.order_info;
            const activities = data.activities;
            const groups = {};
            activities.forEach(a => {
                const key = `${a.service_id}_${a.price}`;
                if (!groups[key]) groups[key] = {
                    name: a.service_name, unit: a.unit || '',
                    price: parseFloat(a.price), qty: 0, total: 0
                };
                groups[key].qty += parseFloat(a.duration_value);
                groups[key].total += parseFloat(a.duration_value) * parseFloat(a.price);
            });
            const rows = Object.values(groups);
            const invoiceTotal = rows.reduce((s, r) => s + r.total, 0);
            const prevDebt = parseFloat(data.order_info.prev_debt || 0);
            const grandTotal = invoiceTotal + prevDebt;
            const rowsHtml = rows.map((r, i) => `
                <tr>
                    <td>${i + 1}</td><td>${escapeHtml(r.name)}</td>
                    <td>${formatNumber(r.qty)}</td>
                    <td>${formatNumber(r.price)} ریال</td>
                    <td>${formatNumber(r.total)} ریال</td>
                </tr>`).join('');
            document.getElementById('invoiceContent').innerHTML = `
                <div class="proforma-wrap" id="printArea">
                    <div class="proforma-header">
                        <h2>فاکتور</h2>
                        <p>تاریخ: ${escapeHtml(toJalaliDateTime(info.created_at))}</p>
                        <p>شماره سفارش: ${escapeHtml(info.code)}</p>
                        <p>مشتری: ${escapeHtml(info.customer)}</p>
                    </div>
                    <div class="proforma-workshop">${escapeHtml(data.workshop_name || '')}</div>
                    <table class="proforma-table">
                        <thead><tr><th>#</th><th>شرح خدمت</th><th>مقدار</th><th>قیمت واحد</th><th>جمع</th></tr></thead>
                        <tbody>${rowsHtml}</tbody>
                    </table>
                    <div class="proforma-totals">
                        <p>جمع فاکتور: ${formatNumber(invoiceTotal)} ریال</p>
                        ${prevDebt > 0 ? `<p>مانده حساب قبلی: ${formatNumber(prevDebt)} ریال</p>` : ''}
                        ${prevDebt > 0 ? `<p class="grand-total">جمع کل: ${formatNumber(grandTotal)} ریال</p>` : ''}
                    </div>
                </div>`;
        });
}

function printProforma() {
    if (!document.getElementById('vazirmatn-print-font')) {
        const link = document.createElement('link');
        link.id = 'vazirmatn-print-font';
        link.rel = 'stylesheet';
        link.href = 'https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700&display=swap';
        document.head.appendChild(link);
    }
    window.print();
}


