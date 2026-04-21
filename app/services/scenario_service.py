# app/services/scenario_service.py
from app import db
from app.models import Scenario, ScenarioCriterion, Criterion


class ScenarioService:
    def list_all(self):
        return Scenario.query.order_by(Scenario.id.asc()).all()

    def get(self, scenario_id):
        return Scenario.query.get_or_404(scenario_id)

    def create(self, payload, user_id):
        scenario = Scenario(
            name=payload['name'].strip(),
            description=(payload.get('description') or '').strip(),
            method=payload.get('method', 'topsis_entropy'),
            status='черновик',
            created_by=user_id,
        )
        db.session.add(scenario)
        db.session.flush()

        self._sync_criteria(scenario.id, payload.get('criterion_ids', []))

        db.session.commit()
        return scenario

    def update(self, scenario_id, payload):
        scenario = Scenario.query.get_or_404(scenario_id)
        scenario.name = payload['name'].strip()
        scenario.description = (payload.get('description') or '').strip()
        scenario.method = payload.get('method', 'topsis_entropy')

        ScenarioCriterion.query.filter_by(scenario_id=scenario.id).delete()
        self._sync_criteria(scenario.id, payload.get('criterion_ids', []))

        db.session.commit()
        return scenario

    def delete(self, scenario_id):
        scenario = Scenario.query.get_or_404(scenario_id)
        db.session.delete(scenario)
        db.session.commit()

    def _sync_criteria(self, scenario_id, criterion_ids):
        criteria = Criterion.query.filter(Criterion.id.in_(criterion_ids)).order_by(Criterion.order_no.asc()).all()
        for idx, c in enumerate(criteria, start=1):
            db.session.add(ScenarioCriterion(
                scenario_id=scenario_id,
                criterion_id=c.id,
                is_enabled=True,
                order_no=idx
            ))