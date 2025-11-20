const API_BASE = "http://127.0.0.1:8000/api/v1";

const grid = document.getElementById("products-grid");
const searchInput = document.getElementById("search-input");
const categorySelect = document.getElementById("category-filter");
const totalProductsSpan = document.getElementById("total-products");
const reloadBtn = document.getElementById("reload-btn");

let fullMenu = {}; 
let flatProducts = [];

async function loadMenu() {
  try {
    grid.innerHTML = "<p>Cargando...</p>";
    const res = await fetch(`${API_BASE}/menu`);
    fullMenu = await res.json();
    buildFlatProducts();
    buildCategoryFilter();
    renderProducts();
  } catch (err) {
    grid.innerHTML = "<p>Error al cargar.</p>";
  }
}

function buildFlatProducts() {
  flatProducts = [];
  for (const [cat, items] of Object.entries(fullMenu)) {
    items.forEach((p) =>
      flatProducts.push({
        ...p,
        _categoriaNombre: cat,
      })
    );
  }
}

function buildCategoryFilter() {
  categorySelect.innerHTML = `<option value="__all__">Todas las categorías</option>`;
  Object.keys(fullMenu).forEach((cat) => {
    const opt = document.createElement("option");
    opt.value = cat;
    opt.textContent = cat;
    categorySelect.appendChild(opt);
  });
}

function renderProducts() {
  const term = searchInput.value.toLowerCase();
  const cat = categorySelect.value;

  const filtered = flatProducts.filter((p) => {
    return (
      (cat === "__all__" || p._categoriaNombre === cat) &&
      (!term ||
        p.nombre.toLowerCase().includes(term) ||
        p.descripcion.toLowerCase().includes(term))
    );
  });

  totalProductsSpan.textContent = filtered.length;
  grid.innerHTML = "";

  filtered.forEach((p) => {
    const html = `
      <article class="product-card">
        <header class="product-header">
          <h3 class="product-name">${p.nombre}</h3>
          <span class="product-badge">${p._categoriaNombre}</span>
        </header>
        <p class="product-description">${p.descripcion}</p>
        <div class="product-meta">
          <span class="product-price">$${p.precio}</span>
          <span>${p.disponible ? "Disponible" : "No disponible"}</span>
        </div>
      </article>
    `;
    grid.insertAdjacentHTML("beforeend", html);
  });
}

searchInput.addEventListener("input", renderProducts);
categorySelect.addEventListener("change", renderProducts);
reloadBtn.addEventListener("click", loadMenu);

loadMenu();
