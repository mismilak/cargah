(function () {
    const form = document.getElementById('service-form');
    const tbody = document.getElementById('service-tbody');
    const errorDiv = document.getElementById('form-error');
    const serviceIdInput = document.getElementById('service-id');
    const btnSubmit = document.getElementById('btn-submit');

    // Format number با جداکننده فارسی
    function formatPrice(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '،');
    }

    // Clear form
    function clearForm() {
        serviceIdInput.value = '';
        document.getElementById('service-name').value = '';
        document.getElementById('service-machine').value = '';
        document.getElementById('service-unit').value = '';
        document.getElementById('service-price').value = '';
        btnSubmit.textContent = 'افزودن';
        errorDiv.style.display = 'none';
    }

    // Submit (افزودن یا ویرایش)
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const serviceId = serviceIdInput.value;

        try {
            const res = await fetch(window.location.pathname, {
                method: 'POST',
                body: formData,
                headers: {'X-Requested-With': 'XMLHttpRequest'}
            });
            const data = await res.json();
            if (res.ok) {
                if (serviceId) {
                    // ویرایش
                    const row = tbody.querySelector(`tr[data-id="${serviceId}"]`);
                    row.querySelector('td:nth-child(1)').textContent = data.name;
                    row.querySelector('td:nth-child(2)').textContent = data.machine_name;
                    row.querySelector('td:nth-child(3)').textContent = data.unit_display;
                    row.querySelector('td:nth-child(4)').innerHTML = `${formatPrice(data.base_price)} ریال`;
                    row.querySelector('.btn-edit').dataset.name = data.name;
                    row.querySelector('.btn-edit').dataset.machine = data.machine_name;
                    row.querySelector('.btn-edit').dataset.unit = data.unit;
                    row.querySelector('.btn-edit').dataset.price = data.base_price;
                } else {
                    // افزودن
                    const newRow = `
            <tr data-id="${data.id}">
              <td>${data.name}</td>
              <td>${data.machine_name}</td>
              <td>${data.unit_display}</td>
              <td class="text-end">${formatPrice(data.base_price)} ریال</td>
              <td>${data.created_at}</td>
              <td>
                <button class="btn-icon btn-edit" data-id="${data.id}"
                        data-name="${data.name}"
                        data-machine="${data.machine_name}"
                        data-unit="${data.unit}"
                        data-price="${data.base_price}">✏️</button>
                <button class="btn-icon btn-delete" data-id="${data.id}">🗑️</button>
              </td>
            </tr>
          `;
                    tbody.insertAdjacentHTML('afterbegin', newRow);
                }
                clearForm();
            } else {
                errorDiv.textContent = data.error || 'خطایی رخ داد';
                errorDiv.style.display = 'block';
            }
        } catch (err) {
            errorDiv.textContent = 'خطا در ارتباط با سرور';
            errorDiv.style.display = 'block';
        }
    });

    // Edit
    tbody.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-edit')) {
            const btn = e.target;
            serviceIdInput.value = btn.dataset.id;
            document.getElementById('service-name').value = btn.dataset.name;
            document.getElementById('service-machine').value = btn.dataset.machine;
            document.getElementById('service-unit').value = btn.dataset.unit;
            document.getElementById('service-price').value = btn.dataset.price;
            btnSubmit.textContent = 'ذخیره';
        }
    });

    // Delete
    tbody.addEventListener('click', async (e) => {
        if (e.target.classList.contains('btn-delete')) {
            if (!confirm('آیا از حذف این خدمت اطمینان دارید؟')) return;
            const id = e.target.dataset.id;
            try {
                const res = await fetch(`${window.location.pathname}delete/${id}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                if (res.ok) {
                    tbody.querySelector(`tr[data-id="${id}"]`).remove();
                } else {
                    alert('خطا در حذف');
                }
            } catch (err) {
                alert('خطا در ارتباط با سرور');
            }
        }
    });
})();
