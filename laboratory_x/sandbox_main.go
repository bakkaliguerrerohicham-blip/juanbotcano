package main

func main() {
    conf := ObtenerConfig("Agricultura")
    GuardarEnNube(conf.NombreNicho, "Sistema Operativo Activo")
    AnalizarGEO("Este es un texto de prueba breve para verificar que el motor de análisis funciona correctamente en nuestro sistema de pruebas local.")
}
