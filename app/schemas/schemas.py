"""
Модуль схем валидации данных Marshmallow.

Автор: Лосева Е.А.
Дата создания: ДД.ММ.ГГГГ
Последнее изменение: ДД.ММ.ГГГГ
Контакт: ekaterinaloseva91@gmail.com
"""

import re
from marshmallow import (
    Schema,
    fields,
    validate,
    validates_schema,
    ValidationError
)


def validate_username(value):
    """Только буквы, цифры и подчеркивание"""
    if not re.match(r'^[a-zA-Z0-9_]+$', value):
        raise ValidationError('Только латиница, цифры и подчеркивание')


def validate_positive(value):
    if value <= 0:
        raise ValidationError('Должно быть больше 0')


def validate_rating(value):
    if value < 1 or value > 5:
        raise ValidationError('Должно быть от 1 до 5')


class LoginSchema(Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)


class RegisterSchema(Schema):
    username = fields.String(
        required=True,
        validate=[
            validate.Length(min=3, max=100, error='От 3 до 100 символов'),
            validate_username
        ],
        metadata={'description': 'Имя пользователя (латиница, цифры, _)'}
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=6, error='Минимум 6 символов'),
        metadata={'description': 'Пароль'}
    )
    full_name = fields.String(
        required=True,
        validate=validate.Length(min=2, max=255, error='От 2 до 255 символов'),
        metadata={'description': 'Полное имя'}
    )


class DatasetUploadSchema(Schema):
    name = fields.String(
        load_default='',
        validate=validate.Length(max=255),
        metadata={'description': 'Название датасета'}
    )
    description = fields.String(
        load_default='',
        validate=validate.Length(max=1000),
        metadata={'description': 'Описание'}
    )
    skip_preprocess = fields.Boolean(
        load_default=False,
        metadata={'description': 'Пропустить предобработку'}
    )


class ShipmentFilterSchema(Schema):
    carrier_id = fields.Integer(
        metadata={'description': 'ID перевозчика'}
    )
    dataset_id = fields.Integer(
        metadata={'description': 'ID датасета'}
    )
    status = fields.String(
        validate=validate.OneOf(['Доставлено', 'Отменено', 'Не приехал']),
        metadata={'description': 'Статус рейса'}
    )


class CarrierFilterSchema(Schema):
    region = fields.String(
        validate=validate.OneOf([
            'Центральный', 'Северо-Западный', 'Южный',
            'Приволжский', 'Уральский', 'Сибирский', 'Дальневосточный'
        ]),
        metadata={'description': 'Регион'}
    )
    fleet_type = fields.String(
        validate=validate.OneOf([
            'самосвалы', 'бортовые', 'все типы', 'рефрижераторы'
        ]),
        metadata={'description': 'Тип автопарка'}
    )


class ScenarioCreateSchema(Schema):
    name = fields.String(
        required=True,
        validate=validate.Length(min=3, max=255, error='От 3 до 255 символов'),
        metadata={'description': 'Название сценария'}
    )
    description = fields.String(
        load_default='',
        validate=validate.Length(max=1000),
        metadata={'description': 'Описание'}
    )
    method = fields.String(
        required=True,
        validate=validate.OneOf(['topsis', 'vikor']),
        metadata={'description': 'Метод расчета'}
    )
    criterion_ids = fields.List(
        fields.Integer(strict=True),
        required=True,
        validate=validate.Length(min=1, error='Минимум 1 критерий'),
    )
    swara_config = fields.Dict(
        load_default={},
        metadata={'description': 'Конфигурация SWARA весов'}
    )


class ScenarioUpdateSchema(Schema):
    name = fields.String(
        validate=validate.Length(min=3, max=255, error='От 3 до 255 символов'),
        metadata={'description': 'Название сценария'}
    )
    description = fields.String(
        validate=validate.Length(max=1000),
        metadata={'description': 'Описание'}
    )
    method = fields.String(
        validate=validate.OneOf(['topsis', 'vikor']),
        metadata={'description': 'Метод расчета'}
    )
    criterion_ids = fields.List(
        fields.Integer(strict=True),
        validate=validate.Length(min=1, error='Минимум 1 критерия'),
        metadata={'description': 'Список ID критериев'}
    )
    swara_config = fields.Dict(
        required=False,
        allow_none=True,
        metadata={'description': 'Конфигурация SWARA весов'}
    )


class SwaraWeightsSchema(Schema):
    ranking = fields.List(
        fields.String(),
        required=True,
        validate=validate.Length(min=1, error='Минимум 1 критерия'),
        metadata={'description': 'Критерии от важного к неважному'}
    )
    s_values = fields.List(
        fields.Float(
            validate=validate.Range(min=0, error='Должно быть >= 0')
        ),
        required=True,
        metadata={'description': 'Сравнительная важность (>=0)'}
    )


class ShipmentCreateSchema(Schema):
    shipment_id = fields.Integer(required=True)
    carrier_id = fields.Integer(required=True)
    dataset_id = fields.Integer(required=True)
    price = fields.Float(required=True, validate=validate.Range(min=0, min_inclusive=False))
    distance_km = fields.Float(required=True, validate=validate.Range(min=0, min_inclusive=False))
    client_rating = fields.Integer(validate=validate.Range(min=1, max=5))
    status = fields.String(
        required=True,
        validate=validate.OneOf(['Доставлено', 'Отменено', 'Не приехал'])
    )
    pickup_window_start = fields.DateTime()
    delivery_window_end = fields.DateTime()
    actual_delivery_time = fields.DateTime()


class PaginationSchema(Schema):
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1, error='Страница должна быть >= 1'),
        metadata={'description': 'Номер страницы'}
    )
    per_page = fields.Integer(
        load_default=20,
        validate=validate.Range(min=1, max=100, error='От 1 до 100'),
        metadata={'description': 'Записей на странице'}
    )
    sort_by = fields.String(
        load_default='id',
        metadata={'description': 'Поле для сортировки'}
    )
    sort_order = fields.String(
        load_default='asc',
        validate=validate.OneOf(['asc', 'desc']),
        metadata={'description': 'Порядок сортировки'}
    )


class FileUploadSchema(Schema):
    file = fields.Raw(
        required=True,
        metadata={'description': 'Excel файл'}
    )

    @validates_schema
    def validate_file(self, data, **kwargs):
        file = data.get('file')

        if not file:
            raise ValidationError({'file': ['Файл не передан']})

        # Проверка имени файла
        filename = getattr(file, 'filename', '')
        if not filename:
            raise ValidationError({'file': ['Имя файла отсутствует']})

        # Проверка расширения
        if not (filename.endswith('.xlsx') or filename.endswith('.xls')):
            raise ValidationError({
                'file': ['Поддерживаются только .xlsx и .xls']
            })

        # Проверка path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            raise ValidationError({'file': ['Некорректное имя файла']})

        # Проверка размера (10MB = 10_485_760 байт)
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)

        if size > 10_485_760:
            raise ValidationError({'file': ['Файл не должен превышать 10MB']})

        if size == 0:
            raise ValidationError({'file': ['Файл не может быть пустым']})