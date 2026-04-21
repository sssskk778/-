# app/seed.py
from app import db
from app.models import User, Criterion


def seed_everything():
    # =========================================================================
    # 1. СОЗДАЕМ ПОЛЬЗОВАТЕЛЕЙ
    # =========================================================================
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', full_name='Администратор системы', role='admin', is_active=True)
        admin.set_password('admin123')
        db.session.add(admin)

    user = User.query.filter_by(username='logist').first()
    if not user:
        user = User(username='logist', full_name='Логист Иванов', role='user', is_active=True)
        user.set_password('logist123')
        db.session.add(user)

    db.session.commit()
    print('✅ Пользователи созданы: admin / admin123, logist / logist123')

    # =========================================================================
    # 2. СОЗДАЕМ ГЛОБАЛЬНЫЕ КРИТЕРИИ (13 критериев)
    # =========================================================================
    criteria_list = [
        ('on_time_pickup', 'Своевременная подача', 'benefit'),
        ('otif', 'Своевременная и в полном объеме доставка', 'benefit'),
        ('cancellation_rate', 'Отмены рейсов', 'cost'),
        ('no_show_rate', 'Неявка', 'cost'),
        ('damage_rate', 'Повреждения груза', 'cost'),
        ('claim_rate', 'Частота претензий', 'cost'),
        ('tracking_compliance', 'Трекинг статусов', 'benefit'),
        ('pod_rate', 'Подтверждение доставки', 'benefit'),
        ('payment_compliance', 'Доля просроченных платежей', 'cost'),
        ('acceptance_rate', 'Доля принятых заказов', 'benefit'),
        ('rejection_rate', 'Отказы от заявок', 'cost'),
        ('repeat_order_rate', 'Доля повторных рейсов', 'benefit'),
        ('feedback_score', 'Отзывы клиентов', 'benefit'),
    ]

    for order, (code, name, kind) in enumerate(criteria_list, 1):
        existing = Criterion.query.filter_by(code=code).first()
        if not existing:
            db.session.add(Criterion(
                code=code,
                name=name,
                kind=kind,
                order_no=order
            ))
        else:
            existing.name = name
            existing.kind = kind
            existing.order_no = order

    db.session.commit()
    print(f'✅ Создано/обновлено {Criterion.query.count()} глобальных критериев')


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_everything()