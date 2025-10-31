const API_BASE = `${window.location.origin.replace(/:\d+$/, ':8000')}/api/v1`;
const toast = document.querySelector('#toast');
const yearEl = document.querySelector('#year');
yearEl.textContent = new Date().getFullYear();

function showToast(message) {
  toast.textContent = message;
  toast.show();
  setTimeout(() => toast.close(), 2500);
}

async function exportExcel(endpoint, body) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error('Échec de la génération du fichier');
  }
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${endpoint.split('/').pop()}_${Date.now()}.xlsx`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

function defaultSimulationPayload() {
  return {
    simulation_info: {
      hotel_id: 'hotel-demo',
      room: 'Suite Deluxe',
      plan: 'OTA RO FLEX',
      partner: 'Booking.com',
      start_date: '2024-05-01',
      end_date: '2024-05-14',
      nights: 14,
    },
    summary: {
      subtotal_brut: 15890,
      total_partner_discount: 840,
      total_promo_discount: 220,
      total_commission: 1480,
      total_net: 13240,
    },
    results: Array.from({ length: 14 }).map((_, index) => {
      const base = 220 + Math.sin(index / 3) * 15;
      return {
        date: `2024-05-${(index + 1).toString().padStart(2, '0')}`,
        date_display: new Date(2024, 4, index + 1).toLocaleDateString('fr-FR'),
        gross_price: base,
        price_after_partner_discount: base * 0.92,
        price_after_promo: base * 0.88,
        commission: base * 0.16,
        net_price: base * 0.74,
        stock: index % 5 === 0 ? 0 : 8,
      };
    }),
  };
}

document.querySelector('#export-simulation').addEventListener('click', async () => {
  try {
    await exportExcel('/exports/simulation', defaultSimulationPayload());
    showToast('Export simulation lancé');
  } catch (error) {
    console.error(error);
    showToast(error.message);
  }
});

const reservationPayload = () => ({
  results: defaultSimulationPayload().results,
});

document.querySelector('#export-reservation').addEventListener('click', async () => {
  try {
    await exportExcel('/exports/reservation', reservationPayload());
    showToast('Export réservation lancé');
  } catch (error) {
    console.error(error);
    showToast(error.message);
  }
});

const pricingForm = document.querySelector('#pricing-form');
const pricingResult = document.querySelector('#pricing-result');

pricingForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(pricingForm));
  try {
    const response = await fetch(`${API_BASE}/price-tracking/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Impossible de simuler les tarifs');
    const result = await response.json();
    const { analytics, price_data } = result;
    pricingResult.innerHTML = `
      <h3>Vue d'ensemble</h3>
      <p>Période : <strong>${analytics.period}</strong></p>
      <p>Prix moyen : <strong>${analytics.average_price} €</strong> · Min/Max :
        <strong>${analytics.min_price} €</strong> / <strong>${analytics.max_price} €</strong></p>
      <p>Tendance : <strong>${analytics.trend}</strong> · Disponibilité :
        <strong>${analytics.availability_rate}%</strong></p>
      <details>
        <summary>Données quotidiennes</summary>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Prix final (€)</th>
              <th>Commission (€)</th>
              <th>Disponible</th>
            </tr>
          </thead>
          <tbody>
            ${price_data
              .map(
                (item) => `
                  <tr>
                    <td>${item.date}</td>
                    <td>${item.final_price}</td>
                    <td>${item.commission}</td>
                    <td>${item.is_available ? '✅' : '❌'}</td>
                  </tr>
                `,
              )
              .join('')}
          </tbody>
        </table>
      </details>
    `;
  } catch (error) {
    console.error(error);
    showToast(error.message);
  }
});

async function refreshHistory() {
  const response = await fetch(`${API_BASE}/excel/history`);
  if (!response.ok) return;
  const files = await response.json();
  const container = document.querySelector('#history');
  if (!files.length) {
    container.innerHTML = '<p class="placeholder">Aucun fichier téléversé pour le moment.</p>';
    return;
  }
  container.innerHTML = files
    .map(
      (file) => `
        <div class="history-card">
          <div>
            <strong>${file.filename}</strong>
            <small>${new Date(file.uploaded_at).toLocaleString('fr-FR')} · ${Math.round(file.file_size / 1024)} Ko</small>
          </div>
          <div class="actions">
            <a href="${API_BASE}/excel/${file.id}/download" class="secondary">Télécharger</a>
            <button data-id="${file.id}">Supprimer</button>
          </div>
        </div>
      `,
    )
    .join('');
  container.querySelectorAll('button[data-id]').forEach((button) => {
    button.addEventListener('click', async () => {
      const id = button.dataset.id;
      await fetch(`${API_BASE}/excel/${id}`, { method: 'DELETE' });
      showToast('Fichier supprimé');
      refreshHistory();
    });
  });
}

refreshHistory();

const uploadForm = document.querySelector('#upload-form');

uploadForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(uploadForm);
  try {
    const response = await fetch(`${API_BASE}/excel/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error('Téléversement impossible');
    showToast('Fichier téléversé');
    uploadForm.reset();
    refreshHistory();
  } catch (error) {
    console.error(error);
    showToast(error.message);
  }
});

async function loadSettings() {
  const response = await fetch(`${API_BASE}/excel/settings`);
  if (!response.ok) return;
  const data = await response.json();
  const form = document.querySelector('#settings-form');
  form.hotel_name.value = data.hotel_name;
  form.currency.value = data.currency;
  form.locale.value = data.locale;
  form.default_partner.value = data.default_partner;
}

loadSettings();

const settingsForm = document.querySelector('#settings-form');

settingsForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(settingsForm));
  try {
    const response = await fetch(`${API_BASE}/excel/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error("Impossible d'enregistrer les paramètres");
    showToast('Paramètres mis à jour');
  } catch (error) {
    console.error(error);
    showToast(error.message);
  }
});
