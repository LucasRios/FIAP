from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import equipamentos, plantas,sensores

app = FastAPI(title="Forzy API", version="1.0.0.0" )


app.add_middleware( 
    CORSMiddleware,
    allow_origins=["https://localhost:7860"],
    allow_methods=["GET,POST"],
    allow_headers=["*"]
)


app.include_router(equipamentos.router, prefix="/v1")
app.include_router(plantas.router, prefix="/v1")
app.include_router(sensores.router, prefix="/v1")

@app.get("/")
def raiz():
    return {"status": "ok", "servico": "está online"}