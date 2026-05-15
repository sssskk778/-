"""
Модуль API маршрутов Carrier Rating Platform.

Автор: Лосева Е.А.
Дата создания: ДД.ММ.ГГГГ
Последнее изменение: ДД.ММ.ГГГГ
Контакт: ekaterinaloseva91@gmail.com
"""
from functools import wraps

from flask import Blueprint, jsonify, request, make_response
from marshmallow import ValidationError
from app.utils.validators import validate_body, validate_query

from app.auth import login_required, admin_required, current_user
from app.schemas.schemas import (
    ShipmentFilterSchema,
    ScenarioCreateSchema,
    ScenarioUpdateSchema,
    SwaraWeightsSchema,
    DatasetUploadSchema,
)
from app.schemas.serializers import (
    serialize_dataset,
    serialize_carrier,
    serialize_shipment,
    serialize_scenario,
    serialize_run,
    serialize_run_result,
    serialize_criterion,
)
from app.services.core.carrier_service import CarrierService
from app.services.data.dataset_service import DatasetService
from app.services.core.export_service import ExportService
from app.services.core.scenario_service import ScenarioService
from app.services.core.run_service import RunService
from app.services.algorithms.swara import SwaraService

api_bp = Blueprint('api', __name__, url_prefix='/api')
carriers_svc = CarrierService()
datasets = DatasetService()
export_svc = ExportService()
scenarios = ScenarioService()
runs = RunService()

def success(data=None, status=200, meta=None):
    """Успешный ответ в едином формате."""
    body = {'ok': True, 'data': data}
    if meta is not None:
        body['meta'] = meta
    return jsonify(body), status


def error(message, status=400, details=None):
    """Ответ с ошибкой в едином формате."""
    body = {'ok': False, 'error': message}
    if details is not None:
        body['details'] = details
    return jsonify(body), status


@api_bp.get('/auth/me')
@login_required
def me():
    u = current_user()
    return success({
        'id': u.id,
        'username': u.username,
        'full_name': u.full_name,
        'role': u.role,
    })

@api_bp.get('/datasets')
@login_required
def dataset_list():
    return success([serialize_dataset(d) for d in datasets.list_datasets()])


@api_bp.get('/datasets/<int:did>')
@login_required
def dataset_detail(did):
    ds = datasets.get_dataset(did)
    counts = carriers_svc.get_dataset_counts(did)
    return success({**serialize_dataset(ds), **counts})


@api_bp.post('/datasets/upload')
@login_required
def upload_dataset():
    if 'file' not in request.files:
        return error('Файл не передан', 400)
    file = request.files['file']
    if not file.filename.endswith(('.xlsx', '.xls')):
        return error('Поддерживаются только Excel-файлы (.xlsx, .xls)', 400)

    try:
        params = DatasetUploadSchema().load(request.form.to_dict())
    except ValidationError as e:
        return error('Ошибка параметров', 422, e.messages)

    try:
        result = datasets.import_excel(
            file_storage=file,
            name=params.get('name') or file.filename,
            description=params.get('description', ''),
            skip_preprocess=params.get('skip_preprocess', False),
        )
        ds = result['dataset']
        counts = carriers_svc.get_dataset_counts(ds.id)
        data = {
            **serialize_dataset(ds),
            **counts,
            'message': 'Датасет успешно загружен',
        }
        if result.get('preprocess_report'):
            data['preprocess'] = datasets.format_preprocess_report(result['preprocess_report'])
        return success(data, 201)
    except Exception as e:
        return error(str(e), 400)


@api_bp.delete('/datasets/<int:did>')
@login_required
def delete_dataset(did):
    try:
        datasets.delete_dataset(did)
        return success({'message': 'Датасет удален'})
    except Exception as e:
        return error(str(e), 400)


@api_bp.get('/carriers')
@login_required
def carriers():
    return success([serialize_carrier(c) for c in carriers_svc.list_carriers()])


@api_bp.get('/carriers/<int:cid>')
@login_required
def carrier_detail(cid):
    carrier = carriers_svc.get_carrier(cid)
    return success({
        **serialize_carrier(carrier),
        'stats': carriers_svc.get_carrier_stats(cid),
    })

@api_bp.get('/shipments')
@login_required
@validate_query(ShipmentFilterSchema)
def shipments(filters):
    rows = carriers_svc.get_shipments(
        carrier_id=filters.get('carrier_id'),
        dataset_id=filters.get('dataset_id'),
        status=filters.get('status'),
    )
    return success([serialize_shipment(s) for s in rows])

@api_bp.get('/criteria')
@login_required
def criteria():
    return success([serialize_criterion(c) for c in scenarios.list_criteria()])


@api_bp.get('/scenarios')
@login_required
def scenario_list():
    return success([serialize_scenario(s) for s in scenarios.list_all()])


@api_bp.get('/scenarios/<int:sid>')
@login_required
def scenario_get(sid):
    s = scenarios.get(sid)
    return success({**serialize_scenario(s), 'swara_config': s.get_swara_config()})


@api_bp.post('/scenarios')
@admin_required
@validate_body(ScenarioCreateSchema)
def scenario_create(data):
    try:
        s = scenarios.create(data, current_user().id)
        return success({'id': s.id, 'name': s.name}, 201)
    except ValueError as e:
        return error(str(e), 400)


@api_bp.put('/scenarios/<int:sid>')
@admin_required
@validate_body(ScenarioUpdateSchema)
def scenario_update(sid, data):
    try:
        s = scenarios.update(sid, data)
        return success({'id': s.id, 'name': s.name})
    except ValueError as e:
        return error(str(e), 400)


@api_bp.delete('/scenarios/<int:sid>')
@admin_required
def scenario_delete(sid):
    scenarios.delete(sid)
    return success({'message': 'deleted'})


@api_bp.put('/scenarios/<int:sid>/weights/swara')
@admin_required
@validate_body(SwaraWeightsSchema)
def scenario_set_swara_weights(sid, data):
    try:
        result = scenarios.set_swara_weights(sid, data['ranking'], data['s_values'])
        return success(result)
    except ValueError as e:
        return error(str(e), 400)


@api_bp.get('/scenarios/<int:sid>/weights/swara')
@login_required
def scenario_get_swara_weights(sid):
    return success(scenarios.get_swara_weights(sid))


@api_bp.post('/scenarios/<int:sid>/weights/swara/preview')
@login_required
@validate_body(SwaraWeightsSchema)
def scenario_preview_swara_weights(sid, data):
    try:
        weights = SwaraService.preview_weights(data['ranking'], data['s_values'])
        return success({'weights': weights})
    except ValueError as e:
        return error(str(e), 400)


@api_bp.post('/scenarios/<int:sid>/run')
@admin_required
def scenario_run(sid):
    try:
        run = runs.execute(sid, current_user().id)
        return success({'run_id': run.id, 'status': run.status}, 201)
    except ValueError as e:
        return error(str(e), 400)
    except Exception as e:
        return error(str(e), 500)


@api_bp.get('/scenarios/<int:sid>/runs')
@login_required
def scenario_runs(sid):
    return success([serialize_run(r) for r in runs.list_runs(sid)])


@api_bp.get('/runs/<int:rid>')
@login_required
def run_detail(rid):
    run, results = runs.get_run_detail(rid)
    return success({
        'run': serialize_run(run),
        'results': [serialize_run_result(r) for r in results],
    })


@api_bp.get('/scenarios/<int:sid>/latest-results')
@login_required
def latest_results(sid):
    run, results = runs.latest_results(sid)
    if not run:
        return success({'run': None, 'results': [], 'meta': None})
    return success({
        'run': serialize_run(run),
        'results': [serialize_run_result(r) for r in results],
    })

@api_bp.get('/scenarios/<int:sid>/export')
@login_required
def export_excel(sid):
    run, results = runs.latest_results(sid)
    if not run:
        return error('Нет результатов', 404)

    file_bytes = export_svc.build_excel_results(results)

    response = make_response(file_bytes)
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename=scenario_{sid}_results.xlsx'
    return response