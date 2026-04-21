# app/services/csv_importer.py
import csv
from datetime import datetime
from pathlib import Path

from app import db
from app.models import (
    Dataset, Carrier, Shipment, ShipmentEvent,
    ShipmentDocument, Claim, CarrierBehavior
)


class CSVImporter:

    def __init__(self, verbose=True):
        self.stats = {
            'carriers': 0,
            'shipments': 0,
            'events': 0,
            'documents': 0,
            'claims': 0,
            'behavior': 0
        }
        self.verbose = verbose

    def _parse_int(self, val):
        if not val or val == '':
            return None
        try:
            return int(float(val))
        except:
            return None

    def _parse_datetime(self, val):
        if not val:
            return None
        try:
            return datetime.strptime(str(val).strip(), '%Y-%m-%d %H:%M:%S')
        except:
            try:
                return datetime.strptime(str(val).strip(), '%Y-%m-%d %H:%M')
            except:
                return None

    def _log(self, msg):
        if self.verbose:
            print(f"   {msg}")

    def import_csv(self, file_path: str, name='Dataset', description=''):
        print(f"\n📂 Чтение: {file_path}")

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()

        blocks = content.strip().split('\n\n')
        print(f"📊 Блоков: {len(blocks)}")

        ds = Dataset(name=name, file_name=Path(file_path).name,
                     description=description, records_count=0)
        db.session.add(ds)
        db.session.flush()
        print(f"📁 Dataset ID={ds.id}\n")

        for block in blocks:
            if not block.strip():
                continue

            lines = block.strip().split('\n')
            if len(lines) < 2:
                continue

            header = lines[0].lower()

            if 'event_id' in header:
                print(f"📡 Импорт events...")
                self._import_events(lines)
                print(f"   → Загружено {self.stats['events']} событий\n")

            elif 'doc_id' in header:
                print(f"📄 Импорт documents...")
                self._import_documents(lines)
                print(f"   → Загружено {self.stats['documents']} документов\n")

            elif 'claim_id' in header:
                print(f"⚠️ Импорт claims...")
                self._import_claims(lines)
                print(f"   → Загружено {self.stats['claims']} претензий\n")

            elif 'shipment_id' in header:
                print(f"📦 Импорт shipments...")
                self._import_shipments(lines, ds.id)
                print(f"   → Загружено {self.stats['shipments']} рейсов\n")

            elif 'carrier_id' in header and ('company_name' in header or 'name' in header):
                if 'accepted' not in header:
                    print(f"🚚 Импорт carriers...")
                    self._import_carriers(lines, ds.id)
                    print(f"   → Загружено {self.stats['carriers']} перевозчиков\n")

            elif 'carrier_id' in header and 'accepted' in header:
                print(f"🔄 Импорт behavior...")
                self._import_behavior(lines)
                print(f"   → Загружено {self.stats['behavior']} записей поведения\n")

        db.session.commit()
        self._print_stats()
        return ds

    def _import_carriers(self, lines, dataset_id):
        reader = csv.reader(lines)
        headers = [h.lower() for h in next(reader)]

        for row in reader:
            if not row:
                continue
            try:
                cid = int(row[0])
                name = row[1] if len(row) > 1 else ''
                if not name:
                    continue

                db.session.add(Carrier(
                    carrier_id=cid,
                    dataset_id=dataset_id,
                    name=name,
                    inn=row[2] if len(row) > 2 else None,
                    region=row[3] if len(row) > 3 else None,
                    fleet_type=row[4] if len(row) > 4 else None
                ))
                self.stats['carriers'] += 1
                self._log(f"Carrier {cid}: {name}")
            except Exception as e:
                self._log(f"❌ Ошибка carrier: {e} | row: {row[:3]}")

    def _import_shipments(self, lines, dataset_id):
        reader = csv.reader(lines)
        next(reader)

        for row in reader:
            if not row:
                continue
            try:
                sid = int(row[0])
                cid = int(row[1])

                db.session.add(Shipment(
                    shipment_id=sid,
                    dataset_id=dataset_id,
                    carrier_id=cid,
                    shipper_id=self._parse_int(row[2]) if len(row) > 2 else None,
                    origin=row[3] if len(row) > 3 else None,
                    destination=row[4] if len(row) > 4 else None,
                    pickup_window_start=self._parse_datetime(row[5]) if len(row) > 5 else None,
                    pickup_window_end=self._parse_datetime(row[6]) if len(row) > 6 else None,
                    delivery_window_start=self._parse_datetime(row[7]) if len(row) > 7 else None,
                    delivery_window_end=self._parse_datetime(row[8]) if len(row) > 8 else None,
                    cargo_type=row[9] if len(row) > 9 else None,
                    ordered_quantity=self._parse_int(row[10]) if len(row) > 10 else None,
                    delivered_quantity=self._parse_int(row[11]) if len(row) > 11 else None,
                    client_rating=self._parse_int(row[12]) if len(row) > 12 else None,
                    force_majeure=self._parse_int(row[13]) if len(row) > 13 else 0
                ))
                self.stats['shipments'] += 1
                self._log(f"Shipment {sid}: carrier={cid}, rating={row[12] if len(row) > 12 else 'N/A'}")
            except Exception as e:
                self._log(f"❌ Ошибка shipment: {e} | row: {row[:3]}")

    def _import_events(self, lines):
        reader = csv.reader(lines)
        next(reader)

        for row in reader:
            if not row:
                continue
            try:
                db.session.add(ShipmentEvent(
                    event_id=int(row[0]),
                    shipment_id=int(row[1]),
                    carrier_id=self._parse_int(row[2]) if len(row) > 2 else None,
                    event_type=row[3] if len(row) > 3 else None,
                    event_time=self._parse_datetime(row[4]) if len(row) > 4 else None,
                    latitude=float(row[5]) if len(row) > 5 and row[5] else None,
                    longitude=float(row[6]) if len(row) > 6 and row[6] else None,
                    source=row[7] if len(row) > 7 else None,
                    cancelled_by=row[8] if len(row) > 8 else None,
                    is_carrier_fault=bool(int(row[9])) if len(row) > 9 and row[9] else True
                ))
                self.stats['events'] += 1
                self._log(f"Event {row[0]}: shipment={row[1]}, type={row[3]}, source={row[7]}")
            except Exception as e:
                self._log(f"❌ Ошибка event: {e} | row: {row[:4]}")

    def _import_documents(self, lines):
        reader = csv.reader(lines)
        next(reader)

        for row in reader:
            if not row:
                continue
            try:
                db.session.add(ShipmentDocument(
                    doc_id=int(row[0]),
                    shipment_id=int(row[1]),
                    carrier_id=self._parse_int(row[2]) if len(row) > 2 else None,
                    doc_type=row[3] if len(row) > 3 else None,
                    uploaded_at=self._parse_datetime(row[4]) if len(row) > 4 else None,
                    is_valid=bool(int(row[5])) if len(row) > 5 and row[5] else True,
                    payment_due_date=datetime.strptime(row[6], '%Y-%m-%d').date() if len(row) > 6 and row[6] else None,
                    payment_actual_date=datetime.strptime(row[7], '%Y-%m-%d').date() if len(row) > 7 and row[7] else None
                ))
                self.stats['documents'] += 1
                self._log(f"Doc {row[0]}: shipment={row[1]}, type={row[3]}, valid={row[5] if len(row) > 5 else 'N/A'}")
            except Exception as e:
                self._log(f"❌ Ошибка document: {e} | row: {row[:4]}")

    def _import_claims(self, lines):
        reader = csv.reader(lines)
        next(reader)

        for row in reader:
            if not row:
                continue
            try:
                db.session.add(Claim(
                    claim_id=int(row[0]),
                    shipment_id=int(row[1]),
                    carrier_id=self._parse_int(row[2]) if len(row) > 2 else None,
                    claim_type=row[3] if len(row) > 3 else None,
                    resolved=bool(int(row[4])) if len(row) > 4 and row[4] else False,
                    carrier_fault=bool(int(row[5])) if len(row) > 5 and row[5] else False
                ))
                self.stats['claims'] += 1
                self._log(f"Claim {row[0]}: shipment={row[1]}, type={row[3]}, fault={row[5] if len(row) > 5 else 'N/A'}")
            except Exception as e:
                self._log(f"❌ Ошибка claim: {e} | row: {row[:4]}")

    def _import_behavior(self, lines):
        reader = csv.reader(lines)
        next(reader)

        for row in reader:
            if not row:
                continue
            try:
                db.session.add(CarrierBehavior(
                    carrier_id=int(row[0]),
                    accepted=bool(int(row[1])) if len(row) > 1 and row[1] else False,
                    rejected=bool(int(row[2])) if len(row) > 2 and row[2] else False
                ))
                self.stats['behavior'] += 1
                self._log(f"Behavior: carrier={row[0]}, accepted={row[1]}, rejected={row[2]}")
            except Exception as e:
                self._log(f"❌ Ошибка behavior: {e} | row: {row[:3]}")

    def _print_stats(self):
        print(f"""
{'='*50}
✅ ИМПОРТ ЗАВЕРШЕН
{'='*50}
📦 ПЕРЕВОЗЧИКИ: {self.stats['carriers']}
🚛 РЕЙСЫ: {self.stats['shipments']}
📡 СОБЫТИЯ: {self.stats['events']}
📄 ДОКУМЕНТЫ: {self.stats['documents']}
⚠️ ПРЕТЕНЗИИ: {self.stats['claims']}
🔄 ПОВЕДЕНИЕ: {self.stats['behavior']}
{'='*50}
""")