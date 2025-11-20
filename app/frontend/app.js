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
    // Cambiar de /menu a /productos
    const res = await fetch(`${API_BASE}/productos`);
    if (!res.ok) throw new Error("Error al cargar productos");
    const productos = await res.json();
    
    // Obtener categorías para agrupar
    const catRes = await fetch(`${API_BASE}/categorias`);
    if (!catRes.ok) throw new Error("Error al cargar categorías");
    const categorias = await catRes.json();
    
    // Crear mapa de categorías
    const categoriasMap = new Map();
    categorias.forEach(c => {
      categoriasMap.set(c.id, c.nombre || c.descripcion || `Cat ${c.id}`);
    });
    
    // Agrupar productos por categoría
    fullMenu = {};
    productos.forEach(p => {
      const catNombre = categoriasMap.get(p.categoria_id || p.id_categoria) || "Sin categoría";
      if (!fullMenu[catNombre]) {
        fullMenu[catNombre] = [];
      }
      fullMenu[catNombre].push({
        ...p,
        _categoriaNombre: catNombre
      });
    });
    
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

  console.log(filtered);

  totalProductsSpan.textContent = filtered.length;
  grid.innerHTML = "";

  filtered.forEach((p) => {
    const html = `
      <article class="product-card">
        <header class="product-header">
          <div class="product-badge-container">
            <span class="product-badge">${p._categoriaNombre}</span>
          </div>
          <div class="product-name-container">
            <h3 class="product-name">${p.nombre}</h3>
          </div>
        </header>
        <p class="product-description">${p.descripcion}</p>
        <div class="product-meta">
          <span class="product-price">$${p.precio}</span>
          <span class="${p.disponible ? "product-available" : "product-unavailable"}">${p.disponible ? "Disponible" : "No disponible"}</span>
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
