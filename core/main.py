from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(title="El Ojo de Dios - OpenClaw API")

class WebhookPayload(BaseModel):
    sender_id: str
    text: str

# Lógica asíncrona modular OpenClaw
async def procesar_enjambre(nicho: str, payload: WebhookPayload):
    print(f"[OpenClaw] Activando enjambre para el nicho: {nicho}")
    print(f"[OpenClaw] Mensaje del usuario {payload.sender_id}: {payload.text}")

# --- ENLACES COMERCIALES ÚNICOS POR NICHO ---

@app.post("/v1/webhook/inmobiliaria")
async def webhook_inmobiliaria(payload: WebhookPayload, background_tasks: BackgroundTasks):
    background_tasks.add_task(procesar_enjambre, "inmobiliaria", payload)
    return {"status": "recibido", "nicho": "inmobiliaria"}

@app.post("/v1/webhook/legal")
async def webhook_legal(payload: WebhookPayload, background_tasks: BackgroundTasks):
    background_tasks.add_task(procesar_enjambre, "legal", payload)
    return {"status": "recibido", "nicho": "legal"}

@app.post("/v1/webhook/clinicas")
async def webhook_clinicas(payload: WebhookPayload, background_tasks: BackgroundTasks):
    background_tasks.add_task(procesar_enjambre, "clinicas", payload)
    return {"status": "recibido", "nicho": "clinicas"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
