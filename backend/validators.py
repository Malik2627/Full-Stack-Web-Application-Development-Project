"""
Validation utilities for TaskFlow API payloads.
Ensures titles, dates, priorities, statuses, and foreign key references are valid.
"""

import re
from datetime import datetime
from models import get_user_by_id, get_category_by_id

# Allowed domain values
VALID_PRIORITIES = {"Low", "Medium", "High", "Urgent"}
VALID_STATUSES = {"Pending", "In Progress", "Completed", "Cancelled"}
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_case_value(val, allowed_set):
    """Matches a case-insensitive value against allowed_set and returns exact casing."""
    if not val:
        return None
    val_clean = str(val).strip()
    for allowed in allowed_set:
        if allowed.lower() == val_clean.lower():
            return allowed
    return None


def validate_date(date_str):
    """
    Validates date string with YYYY-MM-DD format and real calendar date.
    Returns (True, parsed_str) or (False, error_message).
    """
    if date_str is None or str(date_str).strip() == "":
        return True, None

    date_clean = str(date_str).strip()
    try:
        dt = datetime.strptime(date_clean, "%Y-%m-%d")
        return True, dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return False, "Due date cannot be invalid. Please enter a valid date in YYYY-MM-DD format."


def validate_task_payload(data, is_update=False):
    """
    Validates task creation or update payload.
    Returns (is_valid, errors_dict, cleaned_data)
    """
    if not isinstance(data, dict):
        return False, {"payload": "Request body must be a valid JSON object."}, {}

    errors = {}
    cleaned = {}

    # 1. Title validation
    if 'title' in data:
        title = data.get('title')
        if title is None or not str(title).strip():
            errors['title'] = "Task title is required."
        elif len(str(title).strip()) > 200:
            errors['title'] = "Task title must not exceed 200 characters."
        else:
            cleaned['title'] = str(title).strip()
    elif not is_update:
        errors['title'] = "Task title is required."

    # 2. Description
    if 'description' in data:
        desc = data.get('description')
        cleaned['description'] = str(desc).strip() if desc else None

    # 3. Priority validation
    if 'priority' in data:
        p_val = data.get('priority')
        normalized_p = normalize_case_value(p_val, VALID_PRIORITIES)
        if not normalized_p:
            errors['priority'] = f"Invalid priority '{p_val}'. Allowed values: {', '.join(sorted(VALID_PRIORITIES))}."
        else:
            cleaned['priority'] = normalized_p
    elif not is_update:
        cleaned['priority'] = 'Medium'

    # 4. Status validation
    if 'status' in data:
        s_val = data.get('status')
        normalized_s = normalize_case_value(s_val, VALID_STATUSES)
        if not normalized_s:
            errors['status'] = f"Invalid status '{s_val}'. Allowed values: {', '.join(sorted(VALID_STATUSES))}."
        else:
            cleaned['status'] = normalized_s
    elif not is_update:
        cleaned['status'] = 'Pending'

    # 5. Due date validation
    if 'due_date' in data:
        is_date_valid, date_res = validate_date(data.get('due_date'))
        if not is_date_valid:
            errors['due_date'] = date_res
        else:
            cleaned['due_date'] = date_res

    # 6. Category ID validation (support both category_id and category)
    cat_id = data.get('category_id') if 'category_id' in data else data.get('category')
    if cat_id is not None:
        if str(cat_id).strip() == "":
            cleaned['category_id'] = None
        else:
            try:
                c_id = int(cat_id)
                if not get_category_by_id(c_id):
                    errors['category_id'] = f"Category with ID {c_id} does not exist."
                else:
                    cleaned['category_id'] = c_id
            except (ValueError, TypeError):
                errors['category_id'] = f"Invalid category_id '{cat_id}'. Must be an integer."

    # 7. User ID validation
    if 'user_id' in data:
        u_id_val = data.get('user_id')
        if u_id_val is None or str(u_id_val).strip() == "":
            cleaned['user_id'] = None
        else:
            try:
                u_id = int(u_id_val)
                if not get_user_by_id(u_id):
                    errors['user_id'] = f"User with ID {u_id} does not exist."
                else:
                    cleaned['user_id'] = u_id
            except (ValueError, TypeError):
                errors['user_id'] = f"Invalid user_id '{u_id_val}'. Must be an integer."

    return (len(errors) == 0, errors, cleaned)


def validate_category_payload(data, is_update=False):
    """
    Validates category creation or update payload.
    """
    if not isinstance(data, dict):
        return False, {"payload": "Request body must be a valid JSON object."}, {}

    errors = {}
    cleaned = {}

    if 'name' in data:
        name = data.get('name')
        if not name or not str(name).strip():
            errors['name'] = "Category name is required."
        elif len(str(name).strip()) > 100:
            errors['name'] = "Category name must not exceed 100 characters."
        else:
            cleaned['name'] = str(name).strip()
    elif not is_update:
        errors['name'] = "Category name is required."

    if 'color' in data:
        color = data.get('color')
        if color and len(str(color).strip()) > 20:
            errors['color'] = "Color string must not exceed 20 characters."
        else:
            cleaned['color'] = str(color).strip() if color else None

    return (len(errors) == 0, errors, cleaned)


def validate_user_payload(data, is_update=False):
    """
    Validates user creation or update payload.
    """
    if not isinstance(data, dict):
        return False, {"payload": "Request body must be a valid JSON object."}, {}

    errors = {}
    cleaned = {}

    if 'name' in data:
        name = data.get('name')
        if not name or not str(name).strip():
            errors['name'] = "Name is required."
        elif len(str(name).strip()) > 100:
            errors['name'] = "Name must not exceed 100 characters."
        else:
            cleaned['name'] = str(name).strip()
    elif not is_update:
        errors['name'] = "Name is required."

    if 'email' in data:
        email = data.get('email')
        if not email or not str(email).strip():
            errors['email'] = "Please enter a valid email."
        else:
            email_clean = str(email).strip().lower()
            if not EMAIL_REGEX.match(email_clean) or len(email_clean) > 150:
                errors['email'] = "Please enter a valid email."
            else:
                cleaned['email'] = email_clean
    elif not is_update:
        errors['email'] = "Please enter a valid email."

    if 'password' in data:
        pw = data.get('password')
        if not pw or not str(pw):
            errors['password'] = "Password is required."
        elif len(str(pw)) < 6:
            errors['password'] = "Password must be at least 6 characters long."
        elif len(str(pw)) > 255:
            errors['password'] = "Password must not exceed 255 characters."
        else:
            cleaned['password'] = str(pw)
    elif not is_update:
        errors['password'] = "Password is required."

    return (len(errors) == 0, errors, cleaned)

