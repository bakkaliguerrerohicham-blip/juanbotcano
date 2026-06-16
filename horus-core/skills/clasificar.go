package skills

import (
	"regexp"
	"strings"
)

type Clasificacion string

const (
	Caliente Clasificacion = "caliente"
	Templado Clasificacion = "templado"
	Frio     Clasificacion = "frio"
)

var keywordsCaliente = []string{
	// urgencia temporal
	"urgente", "cuanto antes", "inmediato", "inmediata", "hoy", "mañana",
	"ya", "necesito", "prisa", "rápido", "ahora", "esta semana",
	"lo antes posible", "a la mayor brevedad",
	// decisión tomada
	"quiero comprar", "quiero vender", "quiero alquilar", "quiero contratar",
	"voy a comprar", "voy a vender", "decidido", "decidida", "confirmado",
	"estoy listo", "estoy lista", "tenemos decidido",
	// situación crítica legal/deuda
	"embargo", "demanda", "juicio", "deuda", "ejecutado", "desahucio",
	"despido", "despedir", "accidente", "siniestro", "urgencia médica",
	// budget alto (detectado por regex separado)
}

var keywordsTemplado = []string{
	"próximo mes", "pronto", "tres meses", "seis meses", "este año",
	"pensando", "mirando", "valorando", "interesado", "interesada",
	"me gustaría", "estoy buscando", "a ver opciones", "tengo curiosidad",
	"cuánto cuesta", "cuanto cuesta", "qué precio", "que precio",
	"para informarme", "para saber más",
}

// presupuestoAlto detecta cantidades >= 100.000 € (caliente por volumen)
var rePresupuesto = regexp.MustCompile(`(\d{3}[\.,]\d{3}|\d{6,})\s*(€|euros?|eur)`)

func ClasificarLead(mensaje string) Clasificacion {
	m := strings.ToLower(mensaje)

	for _, k := range keywordsCaliente {
		if strings.Contains(m, k) {
			return Caliente
		}
	}

	// Presupuesto alto = lead caliente aunque no haya urgencia explícita
	if rePresupuesto.MatchString(m) {
		return Caliente
	}

	for _, k := range keywordsTemplado {
		if strings.Contains(m, k) {
			return Templado
		}
	}

	return Frio
}

func EmojiClasificacion(c Clasificacion) string {
	switch c {
	case Caliente:
		return "🔥"
	case Templado:
		return "🌡️"
	default:
		return "❄️"
	}
}
