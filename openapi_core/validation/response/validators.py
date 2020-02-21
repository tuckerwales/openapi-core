"""OpenAPI core validation response validators module"""
from openapi_core.casting.schemas.exceptions import CastError
from openapi_core.deserializing.exceptions import DeserializeError
from openapi_core.schema.media_types.exceptions import InvalidContentType
from openapi_core.schema.responses.exceptions import (
    InvalidResponse, MissingResponseContent,
)
from openapi_core.templating.paths.exceptions import PathError
from openapi_core.unmarshalling.schemas.enums import UnmarshalContext
from openapi_core.unmarshalling.schemas.exceptions import (
    UnmarshalError, ValidateError,
)
from openapi_core.validation.response.datatypes import ResponseValidationResult
from openapi_core.validation.validators import BaseValidator


class ResponseValidator(BaseValidator):

    def validate(self, request, response):
        try:
            _, operation, _, _, _ = self._find_path(request)
        # don't process if operation errors
        except PathError as exc:
            return ResponseValidationResult([exc, ], None, None)

        try:
            operation_response = self._get_operation_response(
                operation, response)
        # don't process if operation errors
        except InvalidResponse as exc:
            return ResponseValidationResult([exc, ], None, None)

        data, data_errors = self._get_data(response, operation_response)

        headers, headers_errors = self._get_headers(
            response, operation_response)

        errors = data_errors + headers_errors
        return ResponseValidationResult(errors, data, headers)

    def _get_operation_response(self, operation, response):
        return operation.get_response(str(response.status_code))

    def _validate_data(self, request, response):
        try:
            _, operation, _, _, _ = self._find_path(request)
        # don't process if operation errors
        except PathError as exc:
            return ResponseValidationResult([exc, ], None, None)

        try:
            operation_response = self._get_operation_response(
                operation, response)
        # don't process if operation errors
        except InvalidResponse as exc:
            return ResponseValidationResult([exc, ], None, None)

        data, data_errors = self._get_data(response, operation_response)
        return ResponseValidationResult(data_errors, data, None)

    def _get_data(self, response, operation_response):
        if not operation_response.content:
            return None, []

        try:
            media_type = operation_response[response.mimetype]
        except InvalidContentType as exc:
            return None, [exc, ]

        try:
            raw_data = self._get_data_value(response)
        except MissingResponseContent as exc:
            return None, [exc, ]

        try:
            deserialised = self._deserialise_media_type(media_type, raw_data)
        except DeserializeError as exc:
            return None, [exc, ]

        try:
            casted = self._cast(media_type, deserialised)
        except CastError as exc:
            return None, [exc, ]

        try:
            data = self._unmarshal(media_type, casted)
        except (ValidateError, UnmarshalError) as exc:
            return None, [exc, ]

        return data, []

    def _get_headers(self, response, operation_response):
        errors = []

        # @todo: implement
        headers = {}

        return headers, errors

    def _get_data_value(self, response):
        if not response.data:
            raise MissingResponseContent(response)

        return response.data

    def _unmarshal(self, param_or_media_type, value):
        return super(ResponseValidator, self)._unmarshal(
            param_or_media_type, value, context=UnmarshalContext.RESPONSE,
        )
