const API_BASE = "http://127.0.0.1:8000/api/v1";

const tbody = document.getElementById("products-table-body");
const reloadBtn = document.getElementById("reload-admin-btn");
const form = document.getElementById("product-form");
const cancelEditBtn = document.getElementById("cancel-edit-btn");
const editStatus = document.getElementById("edit-status");

const inputId = document.getElementById("product-id");
const inputNombre = document.getElementById("nombre");
const inputDescripcion = document.getElementById("descripcion");
const inputPrecio = document.getElementById("precio");
const selectCategoria = document.getElementById("categoria");
const selectDisponible = document.getElementById("disponible");

let categoriasMap = new Map(); // id -> nombre

async function loadCategorias() {
  try {
    const res = await fetch(`${API_BASE}/categorias`);
    if (!res.ok) throw new Error("Error al cargar categorías");
    const data = await res.json();

    categoriasMap.clear();
    selectCategoria.innerHTML = '<option value="">Selecciona categoría</option>';

    data.forEach((c) => {
      categoriasMap.set(c.id, c.nombre || c.descripcion || `Cat ${c.id}`);
      const opt = document.createElement("option");
      opt.value = c.id;
      opt.textContent = c.nombre || c.descripcion || `Categoría #${c.id}`;
      selectCategoria.appendChild(opt);
    });
  } catch (err) {
    console.error(err);
    alert("No se pudieron cargar las categorías. Revisa la API.");
  }
}

async function loadProductos() {
  try {
    const res = await fetch(`${API_BASE}/productos`);
    if (!res.ok) throw new Error("Error al cargar productos");
    const data = await res.json();
    renderProductos(data);
  } catch (err) {
    console.error(err);
    alert("No se pudieron cargar los productos. Revisa la API.");
  }
}

function renderProductos(productos) {
  tbody.innerHTML = "";
  productos.forEach((p) => {
    const tr = document.createElement("tr");

    const catNombre =
      categoriasMap.get(p.categoria_id || p.id_categoria) || "N/A";

    tr.innerHTML = `
      <td style="padding:6px 8px; border-bottom:1px solid #111827;">${p.id}</td>
      <td style="padding:6px 8px; border-bottom:1px solid #111827;">${p.nombre}</td>
      <td style="padding:6px 8px; border-bottom:1px solid #111827;">${catNombre}</td>
      <td style="padding:6px 8px; border-bottom:1px solid #111827;">$${Number(p.precio).toFixed(2)}</td>
      <td style="padding:6px 8px; border-bottom:1px solid #111827;">${
        p.disponible ? "Sí" : "No"
      }</td>
      <td style="padding:6px 8px; border-bottom:1px solid #111827;">
        <button data-id="${p.id}" class="btn-edit" style="margin-right:6px;">Editar</button>
        <button data-id="${p.id}" class="btn-delete" style="background:#b91c1c; color:#fee2e2;">Eliminar</button>
      </td>
    `;

    tbody.appendChild(tr);
  });

  // Eventos de acciones
  tbody.querySelectorAll(".btn-edit").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      // Buscar fila en memoria: más simple es buscar en la tabla
      // pero para ejemplo rápido, recargamos todo y buscamos en DOM.
      // Lo ideal: mantener un array global de productos.
      editProductoDesdeTabla(id);
    });
  });

  tbody.querySelectorAll(".btn-delete").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      deleteProducto(id);
    });
  });
}

function editProductoDesdeTabla(id) {
  const filas = Array.from(tbody.querySelectorAll("tr"));
  const fila = filas.find((row) =>
    row.firstElementChild.textContent.trim() == id.toString()
  );
  if (!fila) return;

  const celdas = fila.querySelectorAll("td");
  inputId.value = id;
  inputNombre.value = celdas[1].textContent.trim();
  // descripción no está en tabla, la recargamos rápido llamando a la API específica,
  // pero para ejemplo lo dejamos en blanco:
  inputDescripcion.value = "";

  const precioTexto = celdas[3].textContent.replace("$", "").trim();
  inputPrecio.value = precioTexto;

  const disponibleTexto = celdas[4].textContent.trim();
  selectDisponible.value = disponibleTexto === "Sí" ? "true" : "false";

  // categoría no la podemos inferir por id desde la tabla,
  // pero es suficiente dejarla como está el usuario puede cambiarla.
  editStatus.textContent = `Editando ID ${id}`;
}

async function deleteProducto(id) {
  if (!confirm(`¿Seguro que deseas eliminar el producto #${id}?`)) return;
  try {
    const res = await fetch(`${API_BASE}/productos/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Error al eliminar producto");
    await loadProductos();
  } catch (err) {
    console.error(err);
    alert("No se pudo eliminar el producto.");
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    nombre: inputNombre.value,
    descripcion: inputDescripcion.value,
    precio: parseFloat(inputPrecio.value),
    disponible: selectDisponible.value === "true",
    categoria_id: parseInt(selectCategoria.value, 10),
  };

  const id = inputId.value;

  try {
    if (id) {
      // UPDATE
      const res = await fetch(`${API_BASE}/productos/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Error al actualizar producto");
    } else {
      // CREATE
      const res = await fetch(`${API_BASE}/productos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Error al crear producto");
    }

    await loadProductos();
    resetForm();
  } catch (err) {
    console.error(err);
    alert("Ocurrió un error al guardar el producto.");
  }
});

function resetForm() {
  inputId.value = "";
  inputNombre.value = "";
  inputDescripcion.value = "";
  inputPrecio.value = "";
  selectCategoria.value = "";
  selectDisponible.value = "true";
  editStatus.textContent = "Nuevo producto";
}

cancelEditBtn.addEventListener("click", () => resetForm());
reloadBtn.addEventListener("click", () => {
  loadCategorias();
  loadProductos();
});

// Inicial
(async () => {
  await loadCategorias();
  await loadProductos();
})();
