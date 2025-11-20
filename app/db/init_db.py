"""
Script para inicializar la base de datos con datos de ejemplo
"""
from decimal import Decimal
from db.session import init_db, SessionLocal
from db.models import CategoriaModel, ProductoModel
from domain.models import TipoCategoria, TamanoProducto

def crear_datos_iniciales():
    """Crea las categorías y productos iniciales"""
    db = SessionLocal()
    
    try:
        # Verificar si ya hay datos
        if db.query(CategoriaModel).count() > 0:
            print("La base de datos ya tiene datos. Omitiendo inicialización.")
            return
        
        # Crear categorías
        categorias_data = [
            {"id": 1, "nombre": "Bebidas", "descripcion": "Bebidas frías y calientes", "tipo": TipoCategoria.BEBIDAS_FRIAS.value, "activa": True},
            {"id": 2, "nombre": "Botanas", "descripcion": "Snacks y aperitivos", "tipo": TipoCategoria.SNACKS.value, "activa": True},
            {"id": 3, "nombre": "Platos de Comida", "descripcion": "Platos principales y comidas", "tipo": TipoCategoria.ALMUERZO.value, "activa": True},
            {"id": 4, "nombre": "Combos", "descripcion": "Combos de comida y bebida", "tipo": TipoCategoria.ALMUERZO.value, "activa": True},
        ]
        
        categorias = []
        for cat_data in categorias_data:
            categoria = CategoriaModel(**cat_data)
            db.add(categoria)
            categorias.append(categoria)
        
        db.flush()  # Para obtener los IDs
        
        # 5 Bebidas
        bebidas = [
            {
                "nombre": "Coca Cola",
                "descripcion": "Refresco de cola clásico",
                "precio": 25.0,
                "categoria_id": 1,
                "disponible": True,
                "tamano": TamanoProducto.MEDIANO.value,
                "ingredientes": ["Agua carbonatada", "Azúcar", "Saborizantes"],
                "calorias": 140
            },
            {
                "nombre": "Jugo de Naranja Natural",
                "descripcion": "Jugo de naranja recién exprimido",
                "precio": 30.0,
                "categoria_id": 1,
                "disponible": True,
                "tamano": TamanoProducto.GRANDE.value,
                "ingredientes": ["Naranja", "Azúcar"],
                "calorias": 110
            },
            {
                "nombre": "Agua de Horchata",
                "descripcion": "Agua fresca de horchata tradicional",
                "precio": 20.0,
                "categoria_id": 1,
                "disponible": True,
                "tamano": TamanoProducto.GRANDE.value,
                "ingredientes": ["Arroz", "Canela", "Azúcar", "Leche"],
                "calorias": 120
            },
            {
                "nombre": "Limonada",
                "descripcion": "Limonada natural con limón fresco",
                "precio": 22.0,
                "categoria_id": 1,
                "disponible": True,
                "tamano": TamanoProducto.MEDIANO.value,
                "ingredientes": ["Limón", "Azúcar", "Agua"],
                "calorias": 50
            },
            {
                "nombre": "Café Americano",
                "descripcion": "Café negro americano caliente",
                "precio": 28.0,
                "categoria_id": 1,
                "disponible": True,
                "tamano": TamanoProducto.MEDIANO.value,
                "ingredientes": ["Café", "Agua"],
                "calorias": 5
            },
        ]
        
        # 5 Botanas
        botanas = [
            {
                "nombre": "Papas Fritas",
                "descripcion": "Papas fritas crujientes con sal",
                "precio": 35.0,
                "categoria_id": 2,
                "disponible": True,
                "tamano": None,
                "ingredientes": ["Papa", "Aceite", "Sal"],
                "calorias": 365
            },
            {
                "nombre": "Nachos con Queso",
                "descripcion": "Nachos crujientes bañados en queso derretido",
                "precio": 45.0,
                "categoria_id": 2,
                "disponible": True,
                "tamano": None,
                "ingredientes": ["Totopos", "Queso", "Jalapeños"],
                "calorias": 320
            },
            {
                "nombre": "Palomitas",
                "descripcion": "Palomitas de maíz recién hechas",
                "precio": 25.0,
                "categoria_id": 2,
                "disponible": True,
                "tamano": None,
                "ingredientes": ["Maíz", "Aceite", "Sal"],
                "calorias": 130
            },
            {
                "nombre": "Chicharrones",
                "descripcion": "Chicharrones de cerdo crujientes",
                "precio": 40.0,
                "categoria_id": 2,
                "disponible": True,
                "tamano": None,
                "ingredientes": ["Piel de cerdo", "Sal"],
                "calorias": 545
            },
            {
                "nombre": "Mix de Frutos Secos",
                "descripcion": "Mezcla de cacahuates, almendras y nueces",
                "precio": 50.0,
                "categoria_id": 2,
                "disponible": True,
                "tamano": None,
                "ingredientes": ["Cacahuates", "Almendras", "Nueces"],
                "calorias": 280
            },
        ]
        
        # 5 Platos de Comida
        platos = [
            {
                "nombre": "Burrito de Pollo",
                "descripcion": "Burrito grande con pollo, frijoles, arroz y queso",
                "precio": 85.0,
                "categoria_id": 3,
                "disponible": True,
                "tamano": None,
                "ingredientes": ["Tortilla", "Pollo", "Frijoles", "Arroz", "Queso", "Lechuga"],
                "calorias": 520
            },
            {
                "nombre": "Tacos de Carne Asada",
                "descripcion": "3 tacos de carne asada con cebolla y cilantro",
                "precio": 90.0,
                "categoria_id": 3,
                "disponible": True,
                "tamano": None,
                "ingredientes": ["Tortilla", "Carne asada", "Cebolla", "Cilantro", "Salsa"],
                "calorias": 450
            },
            {
                "nombre": "Quesadillas",
                "descripcion": "Quesadillas de queso con champiñones",
                "precio": 70.0,
                "categoria_id": 3,
                "disponible": True,
                "tamano": None,
                "ingredientes": ["Tortilla", "Queso", "Champiñones"],
                "calorias": 380
            },
            {
                "nombre": "Enchiladas Verdes",
                "descripcion": "Enchiladas bañadas en salsa verde con pollo",
                "precio": 95.0,
                "categoria_id": 3,
                "disponible": True,
                "tamano": None,
                "ingredientes": ["Tortilla", "Pollo", "Salsa verde", "Queso", "Crema"],
                "calorias": 480
            },
            {
                "nombre": "Pozole",
                "descripcion": "Pozole tradicional con carne de cerdo",
                "precio": 100.0,
                "categoria_id": 3,
                "disponible": True,
                "tamano": None,
                "ingredientes": ["Maíz", "Carne de cerdo", "Lechuga", "Rábano", "Cebolla"],
                "calorias": 350
            },
        ]
        
        # 5 Combos
        combos = [
            {
                "nombre": "Combo Burrito y Soda",
                "descripcion": "Burrito de pollo + refresco de 500ml",
                "precio": 100.0,
                "categoria_id": 4,
                "disponible": True,
                "tamano": None,
                "ingredientes": ["Burrito de pollo", "Refresco"],
                "calorias": 660
            },
            {
                "nombre": "Combo Tacos y Agua",
                "descripcion": "3 tacos de carne asada + agua de horchata",
                "precio": 105.0,
                "categoria_id": 4,
                "disponible": True,
                "tamano": None,
                "ingredientes": ["Tacos de carne", "Agua de horchata"],
                "calorias": 570
            },
            {
                "nombre": "Combo Quesadillas y Limonada",
                "descripcion": "Quesadillas + limonada natural",
                "precio": 85.0,
                "categoria_id": 4,
                "disponible": True,
                "tamano": None,
                "ingredientes": ["Quesadillas", "Limonada"],
                "calorias": 430
            },
            {
                "nombre": "Combo Enchiladas y Jugo",
                "descripcion": "Enchiladas verdes + jugo de naranja",
                "precio": 115.0,
                "categoria_id": 4,
                "disponible": True,
                "tamano": None,
                "ingredientes": ["Enchiladas verdes", "Jugo de naranja"],
                "calorias": 590
            },
            {
                "nombre": "Combo Pozole y Café",
                "descripcion": "Pozole + café americano",
                "precio": 120.0,
                "categoria_id": 4,
                "disponible": True,
                "tamano": None,
                "ingredientes": ["Pozole", "Café americano"],
                "calorias": 355
            },
        ]
        
        # Agregar todos los productos
        todos_productos = bebidas + botanas + platos + combos
        
        for prod_data in todos_productos:
            producto = ProductoModel(**prod_data)
            db.add(producto)
        
        db.commit()
        print(f"[OK] Base de datos inicializada:")
        print(f"  - {len(categorias)} categorias creadas")
        print(f"  - {len(bebidas)} bebidas")
        print(f"  - {len(botanas)} botanas")
        print(f"  - {len(platos)} platos de comida")
        print(f"  - {len(combos)} combos")
        print(f"  - Total: {len(todos_productos)} productos")
        
    except Exception as e:
        db.rollback()
        print(f"Error al inicializar base de datos: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Inicializando base de datos...")
    init_db()
    crear_datos_iniciales()
    print("[OK] Base de datos lista!")

