"""
Schema module initialization.
"""
from .auth import (
    UserRegistrationSchema,
    UserLoginSchema,
    UserProfileSchema,
    ForgotPasswordSchema,
    ResetPasswordSchema,
    ChangePasswordSchema,
    UserResponseSchema,
    TokenResponseSchema,
    RefreshTokenSchema,
    MessageSchema,
    ErrorSchema
)

__all__ = [
    'UserRegistrationSchema',
    'UserLoginSchema', 
    'UserProfileSchema',
    'ForgotPasswordSchema',
    'ResetPasswordSchema',
    'ChangePasswordSchema',
    'UserResponseSchema',
    'TokenResponseSchema',
    'RefreshTokenSchema',
    'MessageSchema',
    'ErrorSchema'
]
