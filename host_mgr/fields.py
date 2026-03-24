import json

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class NullableJSONStringField(models.JSONField):

    default_error_messages = {
        "invalid_json_string": _("请输入合法的 JSON 字符串。"),
    }

    def validate(self, value, model_instance):
        if value is None or value == "":
            return
        if isinstance(value, str):
            try:
                json.loads(value)
            except (TypeError, ValueError):
                raise ValidationError(
                    self.error_messages["invalid_json_string"],
                    code="invalid_json_string",
                )
        super().validate(value, model_instance)

    def get_prep_value(self, value):
        if value is None or value == "":
            return value
        if isinstance(value, str):
            value = json.loads(value)
        return super().get_prep_value(value)
