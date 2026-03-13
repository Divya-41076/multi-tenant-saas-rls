from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, projects,tasks,invites



app = FastAPI(title = "Multi-tenant SaaS API",
              description="Saas backend with postgreSQL RLS",
              version ="1.0.0"
              )
              
#CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# apirouter registeration similar to blueprint registration
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(projects.router, prefix ="/projects", tags=["Projects"])
app.include_router(tasks.router, prefix ="/tasks", tags=["Tasks"])
app.include_router(invites.router, prefix="/invites",tags=["Invites"])
@app.get("/")
def root():#or home()
    return {"message":"Saas rls Backend is running"}

@app.get("/health")
def health():
    return {"status":"healthy"}

@app.get("/favicon.ico")
def favicon():
    return {}
