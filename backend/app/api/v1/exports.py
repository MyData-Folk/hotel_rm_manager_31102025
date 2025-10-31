from __future__ import annotations

from fastapi import APIRouter, Body

from ...services.exports import export_reservation_simulation, export_simulation

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.post("/simulation")
async def create_simulation_export(payload: dict = Body(...)):
    return export_simulation(payload)


@router.post("/reservation")
async def create_reservation_export(payload: dict = Body(...)):
    return export_reservation_simulation(payload)
