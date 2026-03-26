// Tab Navigation
const navButtons = document.querySelectorAll('.nav-btn');
const tabContents = document.querySelectorAll('.tab-content');

navButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    const targetTab = btn.dataset.tab;

    navButtons.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    tabContents.forEach(tab => {
      tab.classList.remove('active');
      if (tab.id === targetTab) tab.classList.add('active');
    });
  });
});

// Filter functionality
document.querySelectorAll('.filter-bar').forEach(bar => {
  bar.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const filter = btn.dataset.filter;
      const section = btn.closest('.tab-content');
      const cards = section.querySelectorAll('.card');

      bar.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      cards.forEach(card => {
        if (filter === 'all' || card.dataset.category === filter) {
          card.classList.remove('hidden');
        } else {
          card.classList.add('hidden');
        }
      });
    });
  });
});

// Itinerary Management
let itinerary = JSON.parse(localStorage.getItem('sf-itinerary') || '{"transport":[],"food":[],"sightseeing":[]}');

function addToItinerary(category, name, cost) {
  const exists = itinerary[category].some(item => item.name === name);
  if (exists) {
    showToast('Already in your itinerary!');
    return;
  }

  itinerary[category].push({ name, cost });
  saveItinerary();
  renderItinerary();
  showToast(`Added "${name}" to your itinerary!`);
}

function removeFromItinerary(category, index) {
  itinerary[category].splice(index, 1);
  saveItinerary();
  renderItinerary();
  showToast('Removed from itinerary');
}

function clearItinerary() {
  if (!confirm('Clear your entire itinerary?')) return;
  itinerary = { transport: [], food: [], sightseeing: [] };
  saveItinerary();
  renderItinerary();
  showToast('Itinerary cleared');
}

function saveItinerary() {
  localStorage.setItem('sf-itinerary', JSON.stringify(itinerary));
}

function renderItinerary() {
  const totalItems = itinerary.transport.length + itinerary.food.length + itinerary.sightseeing.length;
  const emptyState = document.getElementById('itinerary-empty');
  const content = document.getElementById('itinerary-content');
  const actions = document.getElementById('itinerary-actions');

  if (totalItems === 0) {
    emptyState.classList.remove('hidden');
    content.classList.add('hidden');
    actions.classList.add('hidden');
  } else {
    emptyState.classList.add('hidden');
    content.classList.remove('hidden');
    actions.classList.remove('hidden');
  }

  ['transport', 'food', 'sightseeing'].forEach(category => {
    const section = document.getElementById(`itinerary-${category}`);
    const list = section.querySelector('.itinerary-list');
    list.innerHTML = '';

    if (itinerary[category].length === 0) {
      section.style.display = 'none';
      return;
    }

    section.style.display = 'block';

    itinerary[category].forEach((item, index) => {
      const li = document.createElement('li');
      li.innerHTML = `
        <div class="itinerary-item-info">
          <span class="itinerary-item-name">${item.name}</span>
          <span class="itinerary-item-cost">${item.cost}</span>
        </div>
        <button class="btn-remove" onclick="removeFromItinerary('${category}', ${index})" title="Remove">✕</button>
      `;
      list.appendChild(li);
    });
  });
}

// Trip Form
const tripForm = document.getElementById('trip-form');
tripForm.addEventListener('submit', (e) => {
  e.preventDefault();

  const arrival = document.getElementById('arrival-date').value;
  const departure = document.getElementById('departure-date').value;
  const travelers = document.getElementById('travelers').value;
  const budget = document.getElementById('budget').value;

  const tripData = { arrival, departure, travelers, budget };
  localStorage.setItem('sf-trip-data', JSON.stringify(tripData));

  updateTripSummary(tripData);
  showToast('Trip details saved!');
});

function updateTripSummary(data) {
  const summary = document.getElementById('trip-summary');
  const datesEl = document.getElementById('summary-dates');
  const travelersEl = document.getElementById('summary-travelers');
  const budgetEl = document.getElementById('summary-budget');

  if (data.arrival && data.departure) {
    const arrDate = new Date(data.arrival).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const depDate = new Date(data.departure).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    datesEl.textContent = `${arrDate} – ${depDate}`;
  } else {
    datesEl.textContent = 'Dates not set';
  }

  travelersEl.textContent = data.travelers;
  budgetEl.textContent = data.budget.charAt(0).toUpperCase() + data.budget.slice(1);
  summary.classList.remove('hidden');
}

// Toast notification
function showToast(message) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.classList.remove('hidden');
  toast.classList.add('show');

  setTimeout(() => {
    toast.classList.remove('show');
    toast.classList.add('hidden');
  }, 2500);
}

// Print itinerary
function printItinerary() {
  window.print();
}

// Load saved data on page load
function init() {
  renderItinerary();

  const savedTrip = JSON.parse(localStorage.getItem('sf-trip-data') || 'null');
  if (savedTrip) {
    if (savedTrip.arrival) document.getElementById('arrival-date').value = savedTrip.arrival;
    if (savedTrip.departure) document.getElementById('departure-date').value = savedTrip.departure;
    if (savedTrip.travelers) document.getElementById('travelers').value = savedTrip.travelers;
    if (savedTrip.budget) document.getElementById('budget').value = savedTrip.budget;
    updateTripSummary(savedTrip);
  }
}

init();
