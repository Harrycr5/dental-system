
import importlib
import pkgutil

from fastapi import APIRouter

from app import modules

api_router = APIRouter()


@api_router.get("/health", tags=["system"], summary="Estado de la API")
def health_v1(request):
    s = request.app.state.settings

    return {
        "status": "ok",
        "version": s.app_version,
        "environment": s.environment,
        "timezone": s.timezone,
    }


def include_module_routers() -> None:
    for module_info in pkgutil.iter_modules(
        modules.__path__,
        prefix=f"{modules.__name__}.",
    ):
        router_module_name = f"{module_info.name}.router"

        try:
            router_module = importlib.import_module(router_module_name)
        except ModuleNotFoundError as exc:
            # Ignora módulos que no tengan router.py.
            if exc.name == router_module_name:
                continue
            raise

        module_router = getattr(router_module, "router", None)

        if isinstance(module_router, APIRouter):
            api_router.include_router(module_router)


include_module_routers()

