import uuid
from datetime import datetime

def generate_booking_id():
    return "CMH-" + uuid.uuid4().hex[:6].upper()

def current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
