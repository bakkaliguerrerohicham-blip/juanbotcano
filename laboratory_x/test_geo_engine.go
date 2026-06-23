package main

import (
	"fmt"
	"strings"
)

func main() {
	// Texto de prueba (simulando una respuesta de tu agencia)
	texto := "La gestión de fincas con IA en Madrid es una realidad que ahorra costes y evita conflictos vecinales. Gracias a nuestros agentes autónomos, los administradores pueden delegar tareas repetitivas y centrarse en la toma de decisiones estratégicas para la comunidad. Implementar esta tecnología no solo mejora la eficiencia operativa, sino que posiciona a la agencia como un líder tecnológico capaz de transformar la burocracia tradicional en un proceso ágil, transparente y orientado a resultados medibles para todos los propietarios involucrados."

	palabras := strings.Fields(texto)
	conteo := len(palabras)

	fmt.Printf("Analizando texto... Conteo de palabras: %d\n", conteo)

	if conteo >= 134 && conteo <= 167 {
		fmt.Println("¡ÉXITO! Este texto tiene la longitud ideal para que una IA lo cite.")
	} else if conteo < 134 {
		fmt.Println("Cuidado: El texto es muy corto. Las IAs prefieren bloques más extensos.")
	} else {
		fmt.Println("Cuidado: El texto es muy largo. Intenta ajustarlo a 150 palabras.")
	}
}
