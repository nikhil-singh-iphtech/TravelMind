from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.db.models.user import User
from app.schemas.booking import BookingResponse, CreateBookingRequest
from app.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["bookings"])
_booking_service = BookingService()


@router.post("", response_model=BookingResponse)
async def create_booking(
    payload: CreateBookingRequest,
    current_user: User = Depends(get_current_user),
):
    """Revalidates price and creates a trip booking."""
    try:
        return _booking_service.create_booking(user_id=current_user.id, req=payload)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("", response_model=list[BookingResponse])
async def list_my_bookings(current_user: User = Depends(get_current_user)):
    """List authenticated user's trip bookings."""
    return _booking_service.list_user_bookings(user_id=current_user.id)


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: int, current_user: User = Depends(get_current_user)):
    """Retrieve details for a specific booking."""
    booking = _booking_service.get_booking(booking_id=booking_id, user_id=current_user.id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or access denied",
        )
    return booking


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(booking_id: int, current_user: User = Depends(get_current_user)):
    """Cancel a confirmed or pending booking."""
    try:
        return _booking_service.cancel_booking(booking_id=booking_id, user_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
