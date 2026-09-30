from proyecto2 import project_name_matcher

# Catalogo simulado de proyectos oficiales, separado del archivo de tests.
PROYECTOS_OFICIALES = [
    "2460 N Australian Ave",
    "24-011 Australian Ave Renovation",
    "1500 S Broadway",
    "7800 W Sample Rd",
    "310 E Main St",
    "23-104 Westlake Clinic",
    "900 S Miami Ave Parking Garage",
    "220 W Lake Dr Phase 1",
]

if __name__ == "__main__":
    print("Probador manual de nombres de proyectos")
    print("Catalogo oficial simulado:")
    for nombre_oficial in PROYECTOS_OFICIALES:
        print(f"- {nombre_oficial}")
    print("Escribi 'salir' para terminar.\n")

    while True:
        nombre_sucio = input("Nombre sucio para buscar: ").strip()
        if nombre_sucio.lower() in {"salir", "exit", "q"}:
            print("Fin de la prueba manual.")
            break
        if not nombre_sucio:
            print("Ingresa un nombre o escribe 'salir'.\n")
            continue

        match, confianza = project_name_matcher(
            nombre_sucio,
            PROYECTOS_OFICIALES,
        )
        print(f"Mejor match: {match}")
        print(f"Confianza:   {confianza:.2f}%\n")
