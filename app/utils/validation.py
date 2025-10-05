from marshmallow import Schema, fields, validate

class UserRegistrationSchema(Schema):
    full_name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    role = fields.Str(required=True, validate=validate.OneOf(['student', 'professor', 'admin']))

class UserLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class CourseSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    description = fields.Str(required=False)

class TestSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    description = fields.Str(required=False)
    course_id = fields.Int(required=True)

class QuestionSchema(Schema):
    question_text = fields.Str(required=True)
    question_type = fields.Str(required=True, validate=validate.OneOf(['mcq', 'short_answer', 'true_false']))
    options = fields.List(fields.Dict(), required=False)

class AnswerSchema(Schema):
    question_id = fields.Int(required=True)
    selected_option_id = fields.Int(required=False, allow_none=True)
    answer_text = fields.Str(required=False, allow_none=True)

class ExerciseSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    description = fields.Str(required=False)
    content = fields.Dict(required=False)
    course_id = fields.Int(required=True)

class BadgeSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    description = fields.Str(required=False)
    icon_url = fields.Url(required=False, allow_none=True)

class BadgeAssignmentSchema(Schema):
    student_id = fields.Str(required=True)
    badge_id = fields.Int(required=True)

class InterventionSchema(Schema):
    student_id = fields.Str(required=True)
    note = fields.Str(required=True, validate=validate.Length(min=1))

class ChatbotMessageSchema(Schema):
    message = fields.Str(required=True, validate=validate.Length(min=1))
    sender_role = fields.Str(required=True, validate=validate.OneOf(['student', 'ai']))
