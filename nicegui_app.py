import os
import math
import zipfile
from io import BytesIO
from datetime import datetime
from tempfile import NamedTemporaryFile

from nicegui import ui
from docxtpl import DocxTemplate

from product_validators import validate_xpl201, validate_xqe122, validate_xna121_151


TEMPLATE_PATH = 'template.docx'
LOGO_PATH = 'Picture2.png'

XQE_PDF_CANDIDATES = [
    '1.10_XQE_Layout_planning_Specification.pdf',
    '1.10_XQE_Layout_Planning_Specification.pdf',
]
XPL_PDF_CANDIDATES = [
    '1.9_XPL_Layout_planning_Specification.pdf',
    '1.9_XPL_Layout_Planning_Specification.pdf',
]

FLOW_OPTIONS = ['Inbound', 'Production', 'Buffer Storage', 'Rack Storage', 'Floor Storage', 'Outbound']
NEXT_STEP_OPTIONS = {
    'Inbound': ['Production', 'Buffer Storage', 'Rack Storage', 'Floor Storage', 'Outbound'],
    'Production': ['Buffer Storage', 'Rack Storage', 'Floor Storage', 'Outbound'],
    'Buffer Storage': ['Production', 'Rack Storage', 'Floor Storage', 'Outbound'],
    'Rack Storage': ['Production', 'Buffer Storage', 'Floor Storage', 'Outbound'],
    'Floor Storage': ['Production', 'Buffer Storage', 'Rack Storage', 'Outbound'],
    'Outbound': ['Production', 'Buffer Storage', 'Rack Storage', 'Floor Storage'],
}
TRIGGER_OPTIONS = [
    'PDA / barcode scan', 'Customer WMS order', 'Customer ERP order', 'Customer MES production signal',
    'Integrator system', 'Conveyor sensor', 'Conveyor PLC', 'Photoeye / light sensor',
    'Sky camera / overhead camera', 'Vision system', 'RFID reader', 'Machine / production line signal',
    'Dispatch request', 'Scheduled task', 'Manual release', 'HMI / local panel', 'Other',
]
INFO_SOURCE_OPTIONS = [
    'Customer WMS', 'Customer ERP', 'Customer MES', 'Integrator system', 'EP WMS / DAS',
    'PDA / Scanner', 'Conveyor PLC', 'RFID system', 'Vision system',
    'Fixed rule / predefined location', 'Manual operator', 'Other',
]
COORDINATION_OPTIONS = [
    'Customer WMS', 'Customer ERP', 'Customer MES', 'Integrator system',
    'Middleware / API hub', 'EP WMS / DAS', 'Other',
]
RETURN_TARGET_OPTIONS = [
    'Customer WMS', 'Customer ERP', 'Customer MES', 'Integrator system',
    'EP WMS / DAS', 'PDA / HMI', 'API callback target', 'Other',
]
STATUS_OPTIONS = [
    'Task completed', 'Task assigned', 'Pickup confirmed', 'Destination confirmed',
    'Put-away confirmed', 'Blocked / waiting', 'Failed / exception',
]
KEY_DATA_OPTIONS = [
    'Pallet ID / Barcode', 'Pickup location', 'Destination / Storage location',
    'Storage location confirmation', 'Task ID', 'SKU / Material code', 'Quantity',
]
SYSTEM_INTEGRATION_OPTIONS = [
    'Customer WMS', 'Customer ERP', 'Customer MES', 'Integrator system', 'Other WMS',
    'Fire alarm system', 'Elevators / vertical conveyors', 'Conveyors / PLC',
    'Automatic doors / gates', 'Traffic lights / signals', 'Barcode / RFID system',
    'AS/RS / warehouse automation', 'Production machines / lines', 'Other',
]
API_PROTOCOL_OPTIONS = ['REST API', 'Webhook', 'MQTT', 'OPC UA', 'Profinet', 'Ethernet/IP', 'SQL / DB', 'CSV / File exchange', 'Digital I/O', 'Custom API', 'Other']
APP_TO_EQUIPMENT = {
    'Transport / Cross Docking': 'XPL',
    'Stacking/Conveyor': 'XQE',
    'Narrow Aisle': 'XNA',
}
TRIGGER_DEFAULT_SOURCE = {
    'PDA / barcode scan': 'PDA / Scanner',
    'Customer WMS order': 'Customer WMS',
    'Customer ERP order': 'Customer ERP',
    'Customer MES production signal': 'Customer MES',
    'Integrator system': 'Integrator system',
    'Conveyor sensor': 'Conveyor PLC',
    'Conveyor PLC': 'Conveyor PLC',
    'Photoeye / light sensor': 'Conveyor PLC',
    'Sky camera / overhead camera': 'Vision system',
    'Vision system': 'Vision system',
    'RFID reader': 'RFID system',
    'Machine / production line signal': 'Customer MES',
    'Dispatch request': 'Customer WMS',
    'Scheduled task': 'EP WMS / DAS',
    'Manual release': 'Manual operator',
    'HMI / local panel': 'Manual operator',
    'Other': 'Other',
}


def find_existing_file(candidates):
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def clean_value(value):
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    if isinstance(value, list):
        return ', '.join(str(v) for v in value if str(v).strip())
    return value


def _format_number(value):
    if value in (None, ''):
        return ''
    try:
        n = float(value)
    except Exception:
        return str(value)
    if n.is_integer():
        return str(int(n))
    return f'{n:.2f}'.rstrip('0').rstrip('.')


def _to_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0


def _parse_load_height_m(dimensions_text: str) -> float:
    if not dimensions_text:
        return 0.0
    try:
        parts = str(dimensions_text).replace('x', '×').replace('X', '×').replace('*', '×').split('×')
        if len(parts) >= 3:
            return float(parts[2].strip()) / 1000.0
    except Exception:
        return 0.0
    return 0.0


def _dedupe_keep_order(values):
    result = []
    for v in values:
        if v and v not in result:
            result.append(v)
    return result


def _dedupe_consecutive(values):
    result = []
    for v in values:
        if not v:
            continue
        if not result or result[-1] != v:
            result.append(v)
    return result


def _equipment_options(selected_apps):
    return _dedupe_keep_order([APP_TO_EQUIPMENT[a] for a in selected_apps if a in APP_TO_EQUIPMENT]) or ['AGV']


def build_operational_metrics(route_details):
    lines = []
    total = 0.0
    notes = []
    for route in route_details:
        src = route.get('from', '')
        dst = route.get('to', '')
        cap = _to_float(route.get('pallets_per_hour'))
        flow_type = route.get('flow_type', 'Simultaneous / continuous')
        if not src or not dst:
            continue
        if flow_type == 'No - not handled by EP automation':
            lines.append(f'{src} → {dst}: outside EP automation scope')
            continue
        line = f'{src} → {dst}: {_format_number(cap)} pallets/hour'
        if flow_type == 'On request / intermittent':
            line += ' (on request)'
        else:
            total += cap
        lines.append(line)
    if any(r.get('flow_type') == 'On request / intermittent' for r in route_details):
        notes.append('Some routes are triggered only on request.')
    if any(r.get('flow_type') == 'No - not handled by EP automation' for r in route_details):
        notes.append('Routes outside EP automation scope are excluded from EP throughput and fleet calculations.')
    return {
        'pallets_per_hour': '\n'.join(lines),
        'pallets_per_hour_total': total,
        'pallets_per_day': '',
        'operational_efficiency_note': '\n'.join(notes),
    }


def _build_execution_nodes(execution_mode, primary_vehicle, primary_action, secondary_vehicle, secondary_action):
    if execution_mode == 'Vehicle handover':
        return _dedupe_consecutive([
            f'{primary_vehicle} {primary_action}'.strip(),
            f'{secondary_vehicle} {secondary_action}'.strip(),
        ])
    return [primary_vehicle]


def _build_forward_nodes(trigger, info_source, leading_system, ep_wms_used, execution_nodes):
    nodes = [
        TRIGGER_DEFAULT_SOURCE.get(trigger, trigger),
        info_source,
        leading_system,
    ]
    if ep_wms_used == 'Yes' and 'EP WMS / DAS' not in nodes:
        nodes.append('EP WMS / DAS')
    nodes.append('EP USP Fleet Manager')
    nodes.extend(execution_nodes)
    return _dedupe_consecutive(nodes)


def _build_return_nodes(final_execution_node, return_targets, ep_wms_used):
    targets = [t for t in return_targets if t]
    if not targets:
        return []
    nodes = [final_execution_node, 'EP USP Fleet Manager']
    if ep_wms_used == 'Yes' and 'EP WMS / DAS' not in targets:
        nodes.append('EP WMS / DAS')
    nodes.extend(targets)
    return _dedupe_consecutive(nodes)


class AppState:
    def __init__(self) -> None:
        self.data = {
            'customer_name': '',
            'customer_email': '',
            'customer_mobile': '',
            'project_name': '',
            'project_location': '',
            'warehouse_area': '',
            'survey_date': datetime.today().strftime('%Y-%m-%d'),
            'application': [],
            'task_description': '',
            'pallets': [{
                'pallet_type': 'Euro',
                'other_pallet_type': '',
                'other_pallet_pickable': '',
                'load_dimensions': '',
                'pallet_width_mm': 0,
            }],
            'load_weight_kg': 0,
            'xpl_sub_type': 'Transport',
            'cross_docking_aisle': 0.0,
            'pickup_type': 'Ground',
            'pickup_type_other': '',
            'stacking_type': 'Floor Stacking',
            'stacking_type_other': '',
            'storage_layout': '',
            'storage_locations': '',
            'aisle_width_mm': 0,
            'aisle_width_m': 0.0,
            'xna_model': 'XNA121 (up to 8.5m)',
            'max_stacking_height_m': 0.0,
            'stacking_level': '',
            'shifts_per_day': 0,
            'peak_hours': 0.0,
            'temperature_range': 'Select temperature range',
            'special_layout': '',
            'site_wifi_available': 'Yes',
            'network_status': '',
            'network_coverage': '',
            'route_count': 3,
            'flow_sequence': ['Inbound', 'Rack Storage', 'Outbound'],
            'route_details': [],
            'job_to_do_flow': '',
            'material_flow_text': '',
            'special_comments': '',
            'integration_required': 'Yes',
            'ep_wms_used': 'Yes',
            'current_system_needed': 'Yes',
            'current_system_type': 'Customer WMS',
            'current_system_name': '',
            'other_wms_integration_needed': 'No',
            'other_wms_name': '',
            'integration_connections': [],
            'api_protocols': ['REST API'],
            'data_flow_additional_notes': '',
            'route_flows': {},
            'parking_area': '',
            'charging_status': '',
            'special_demand': '',
            'other_agvs': '',
            'other_traffic': '',
        }
        self.uploads = {}
        self.messages = {'product': ''}

    def set(self, key, value):
        self.data[key] = value

    def get(self, key, default=None):
        return self.data.get(key, default)

    def primary_pallet(self):
        return self.data['pallets'][0]

    def selected_apps(self):
        return self.data.get('application', [])

    def route_details_filtered(self):
        return [r for r in self.data.get('route_details', []) if r.get('flow_type') != 'No - not handled by EP automation']


state = AppState()


def compute_sequence_routes():
    sequence = state.get('flow_sequence', [])
    routes = []
    for i in range(max(0, len(sequence) - 1)):
        routes.append({
            'from': sequence[i],
            'to': sequence[i + 1],
            'pallets_per_hour': state.get(f'route_pallets_per_hour_{i}', 0),
            'avg_distance_m': state.get(f'route_avg_distance_{i}', 0),
            'flow_type': state.get(f'route_flow_type_{i}', 'Simultaneous / continuous'),
            'source_image': state.uploads.get(f'route_source_image_{i}'),
        })
    state.set('route_details', routes)


def validate_product_logic():
    apps = state.selected_apps()
    load_weight = _to_float(state.get('load_weight_kg'))
    max_h = _to_float(state.get('max_stacking_height_m'))
    pallet = state.primary_pallet()
    load_height_m = _parse_load_height_m(pallet.get('load_dimensions', ''))
    messages = []

    if 'Stacking/Conveyor' in apps and max_h > 5.5:
        messages.append('XQE122 maximum stacking height is 5.5 m. Please reduce the value or choose Narrow Aisle for higher stacking.')
    if 'Stacking/Conveyor' in apps and load_weight > 1200 and max_h > 3.5:
        messages.append('For XQE122 above 1200 kg, maximum stacking height is 3.5 m.')
    if 'Stacking/Conveyor' in apps and load_weight > 1500:
        messages.append('XQE122 maximum load capacity is 1500 kg.')
    if 'Narrow Aisle' in apps:
        model = state.get('xna_model')
        if model == 'XNA121 (up to 8.5m)' and max_h > 8.5:
            messages.append('XNA121 maximum lift height is 8.5 m.')
        if model == 'XNA151 (up to 13m)' and max_h > 13.0:
            messages.append('XNA151 maximum lift height is 13 m.')
    if load_height_m > 0 and max_h > 0:
        state.set('stacking_level', str(math.floor(max_h / load_height_m)))
    state.messages['product'] = '\n'.join(messages)
    return not messages


def build_context():
    compute_sequence_routes()
    route_details = state.get('route_details', [])
    op = build_operational_metrics(route_details)
    apps = state.selected_apps()
    primary_pallet = state.primary_pallet()

    distances = [_to_float(r.get('avg_distance_m')) for r in route_details if _to_float(r.get('avg_distance_m')) > 0]
    avg_transport_m = round(sum(distances) / len(distances), 2) if distances else ''

    aisle_lines = []
    if 'Transport / Cross Docking' in apps and state.get('cross_docking_aisle'):
        aisle_lines.append(f"XPL available aisle width: {state.get('cross_docking_aisle')} m")
    if 'Stacking/Conveyor' in apps and state.get('aisle_width_mm'):
        aisle_lines.append(f"XQE available aisle width: {state.get('aisle_width_mm')} mm")
    if 'Narrow Aisle' in apps and state.get('aisle_width_m'):
        aisle_lines.append(f"XNA available aisle width: {state.get('aisle_width_m')} m")

    load_weight_lines = []
    if state.get('load_weight_kg'):
        if 'Transport / Cross Docking' in apps:
            load_weight_lines.append(f"XPL load weight: {state.get('load_weight_kg')} kg")
        if 'Stacking/Conveyor' in apps:
            load_weight_lines.append(f"XQE load weight: {state.get('load_weight_kg')} kg")
        if 'Narrow Aisle' in apps:
            load_weight_lines.append(f"XNA load weight: {state.get('load_weight_kg')} kg")

    stacking_height_lines = []
    stacking_level_lines = []
    if state.get('max_stacking_height_m'):
        if 'Stacking/Conveyor' in apps:
            stacking_height_lines.append(f"XQE maximum stacking height: {state.get('max_stacking_height_m')} m")
            if state.get('stacking_level'):
                stacking_level_lines.append(f"XQE stacking level: {state.get('stacking_level')}")
        if 'Narrow Aisle' in apps:
            stacking_height_lines.append(f"XNA maximum stacking height: {state.get('max_stacking_height_m')} m")
            if state.get('stacking_level'):
                stacking_level_lines.append(f"XNA stacking level: {state.get('stacking_level')}")

    application_lines = []
    if 'Transport / Cross Docking' in apps:
        application_lines.append('XPL - Transport / Cross Docking:')
        if state.get('xpl_sub_type'):
            application_lines.append(f"Application type: {state.get('xpl_sub_type')}")
    if 'Stacking/Conveyor' in apps:
        if application_lines:
            application_lines.append('')
        application_lines.append('XQE - Stacking / Conveyor:')
        for label, key in [
            ('Pickup type', 'pickup_type'),
            ('Pickup type (other)', 'pickup_type_other'),
            ('Stacking type', 'stacking_type'),
            ('Stacking type (other)', 'stacking_type_other'),
            ('Storage layout description', 'storage_layout'),
            ('Storage locations', 'storage_locations'),
        ]:
            if state.get(key):
                application_lines.append(f'{label}: {state.get(key)}')
    if 'Narrow Aisle' in apps:
        if application_lines:
            application_lines.append('')
        application_lines.append('XNA - Narrow Aisle:')
        if state.get('xna_model'):
            application_lines.append(f"Preferred model: {state.get('xna_model')}")

    summary_lines = []
    if 'Transport / Cross Docking' in apps:
        xpl_parts = []
        if state.get('xpl_sub_type'):
            xpl_parts.append(f"Type: {state.get('xpl_sub_type')}")
        if state.get('cross_docking_aisle'):
            xpl_parts.append(f"Aisle: {state.get('cross_docking_aisle')} m")
        if state.get('load_weight_kg'):
            xpl_parts.append(f"Load: {state.get('load_weight_kg')} kg")
        if xpl_parts:
            summary_lines.append('XPL summary: ' + ' | '.join(xpl_parts))
    if 'Stacking/Conveyor' in apps:
        xqe_parts = []
        if state.get('pickup_type'):
            xqe_parts.append(f"Pickup: {state.get('pickup_type')}")
        if state.get('stacking_type'):
            xqe_parts.append(f"Stacking: {state.get('stacking_type')}")
        if state.get('max_stacking_height_m'):
            xqe_parts.append(f"Height: {state.get('max_stacking_height_m')} m")
        if state.get('load_weight_kg'):
            xqe_parts.append(f"Load: {state.get('load_weight_kg')} kg")
        if xqe_parts:
            summary_lines.append('XQE summary: ' + ' | '.join(xqe_parts))
    if 'Narrow Aisle' in apps:
        xna_parts = []
        if state.get('xna_model'):
            xna_parts.append(f"Model: {state.get('xna_model')}")
        if state.get('aisle_width_m'):
            xna_parts.append(f"Aisle: {state.get('aisle_width_m')} m")
        if state.get('max_stacking_height_m'):
            xna_parts.append(f"Height: {state.get('max_stacking_height_m')} m")
        if state.get('load_weight_kg'):
            xna_parts.append(f"Load: {state.get('load_weight_kg')} kg")
        if xna_parts:
            summary_lines.append('XNA summary: ' + ' | '.join(xna_parts))

    route_summary = '\n'.join(f"{r['from']} → {r['to']}" for r in route_details)
    step_details = []
    for r in route_details:
        detail_parts = []
        if r['flow_type'] == 'No - not handled by EP automation':
            detail_parts.append('outside EP automation scope')
        else:
            if _to_float(r.get('avg_distance_m')) > 0:
                detail_parts.append(f"{_format_number(r.get('avg_distance_m'))} m")
            if _to_float(r.get('pallets_per_hour')) > 0:
                detail_parts.append(f"with a capacity of {_format_number(r.get('pallets_per_hour'))} pallets per hour")
            if r.get('flow_type') == 'On request / intermittent':
                detail_parts.append('on request')
        if detail_parts:
            step_details.append(f"From {r['from']} to {r['to']}: " + ', '.join(detail_parts) + '.')
        else:
            step_details.append(f"From {r['from']} to {r['to']}.")

    concise_flow_lines = []
    diagram_blocks = []
    all_connected = set()
    all_status = set()
    all_key_data = set()
    for i, route in enumerate(state.route_details_filtered()):
        route_name = f"{route['from']} → {route['to']}"
        rf = state.get('route_flows', {}).get(i, {})
        trigger = rf.get('trigger', 'Customer WMS order')
        info_source = rf.get('info_source', 'Customer WMS')
        leading = rf.get('leading_system', 'Customer WMS')
        provided = rf.get('provided_info', '')
        execution_mode = rf.get('execution_mode', 'Single EP vehicle')
        primary_vehicle = rf.get('primary_vehicle', _equipment_options(apps)[0])
        primary_action = rf.get('primary_action', 'transport')
        secondary_vehicle = rf.get('secondary_vehicle', _equipment_options(apps)[-1])
        secondary_action = rf.get('secondary_action', 'stacking')
        return_targets = rf.get('return_targets', ['Customer WMS'])
        statuses = rf.get('statuses', ['Task completed'])
        key_data = rf.get('key_data', ['Pallet ID / Barcode', 'Pickup location', 'Destination / Storage location'])
        process_notes = rf.get('process_notes', '')

        execution_nodes = _build_execution_nodes(execution_mode, primary_vehicle, primary_action, secondary_vehicle, secondary_action)
        forward = _build_forward_nodes(trigger, info_source, leading, state.get('ep_wms_used', 'Yes'), execution_nodes)
        ret = _build_return_nodes(execution_nodes[-1], return_targets, state.get('ep_wms_used', 'Yes'))

        line_parts = [f'{route_name}:', ' → '.join(forward)]
        if provided.strip():
            line_parts.append(f'{info_source} provides: {provided.strip()}')
        if process_notes.strip():
            line_parts.append(process_notes.strip())
        concise_flow_lines.append('\n'.join(line_parts))
        d = ' → '.join(forward)
        if ret:
            d += '\nReturn: ' + ' → '.join(ret)
        diagram_blocks.append(f'{route_name}:\n{d}')
        all_connected.update(forward)
        all_connected.update(ret)
        all_status.update(statuses)
        all_key_data.update(key_data)

    integration_req_lines = [
        f"Integration required: {state.get('integration_required')}",
        f"DAS / EP WMS required: {state.get('ep_wms_used')}",
        f"Integration to current customer system needed: {state.get('current_system_needed')}",
    ]
    if state.get('current_system_name'):
        integration_req_lines.append(f"Current customer system: {state.get('current_system_name')} ({state.get('current_system_type')})")
    if state.get('other_wms_integration_needed') == 'Yes':
        integration_req_lines.append(f"Other WMS / system integration: {state.get('other_wms_name') or 'Yes'}")
    if state.get('integration_connections'):
        integration_req_lines.append('Other integrations: ' + ', '.join(state.get('integration_connections')))

    connections_details_lines = []
    if state.get('api_protocols'):
        connections_details_lines.append('All integrations are API / interface based via: ' + ', '.join(state.get('api_protocols')))
    if state.get('current_system_name'):
        connections_details_lines.append(f"Current customer system name: {state.get('current_system_name')}")
    if state.get('other_wms_name'):
        connections_details_lines.append(f"Other WMS / system name: {state.get('other_wms_name')}")
    if state.get('data_flow_additional_notes'):
        connections_details_lines.append(f"Overall integration notes: {state.get('data_flow_additional_notes')}")

    system_architecture_lines = []
    if state.get('current_system_needed') == 'Yes' and state.get('ep_wms_used') == 'Yes':
        system_architecture_lines.append('Customer-side system integration is required. EP WMS / DAS is included as the mandatory coordination layer before EP USP Fleet Manager and EP vehicle execution.')
    elif state.get('ep_wms_used') == 'Yes':
        system_architecture_lines.append('EP WMS / DAS is used as the main coordination layer before EP USP Fleet Manager and EP vehicle execution.')
    else:
        system_architecture_lines.append('Customer / third-party systems coordinate the process and hand tasks to EP USP Fleet Manager for EP vehicle execution.')

    integration_route_parts = []
    if state.get('current_system_name'):
        integration_route_parts.append(state.get('current_system_name'))
    elif state.get('current_system_needed') == 'Yes' and state.get('current_system_type'):
        integration_route_parts.append(state.get('current_system_type'))
    if state.get('ep_wms_used') == 'Yes':
        integration_route_parts.append('EP WMS / DAS')
    integration_route_parts.extend(['EP USP Fleet Manager', 'EP equipment'])

    context = {
        **{k: clean_value(v) for k, v in state.data.items()},
        'job_to_do': state.get('job_to_do_flow') or state.get('task_description', ''),
        'pallet_type': primary_pallet.get('pallet_type', ''),
        'other_pallet_type': primary_pallet.get('other_pallet_type', ''),
        'other_pallet_pickable': primary_pallet.get('other_pallet_pickable', ''),
        'load_dimensions': primary_pallet.get('load_dimensions', ''),
        'pallet_width_mm': primary_pallet.get('pallet_width_mm', ''),
        'pallets_summary': '\n'.join(
            ', '.join(
                [f"Pallet {i+1}: {(p.get('other_pallet_type') if p.get('pallet_type') == 'Other' and p.get('other_pallet_type') else p.get('pallet_type'))}"] +
                ([f"Dimensions: {p.get('load_dimensions')}"] if p.get('load_dimensions') else []) +
                ([f"Insertion Depth: {p.get('pallet_width_mm')} mm"] if p.get('pallet_width_mm') else []) +
                ([f"Can be picked by normal pallet truck: {p.get('other_pallet_pickable')}"] if p.get('other_pallet_pickable') else [])
            ) for i, p in enumerate(state.get('pallets', []))
        ),
        'pallets_per_hour': op['pallets_per_hour'],
        'pallets_per_day': '',
        'operational_efficiency_note': op['operational_efficiency_note'],
        'avg_transport_m': avg_transport_m,
        'aisle_width_text': '\n'.join(aisle_lines),
        'load_weight_text': '\n'.join(load_weight_lines),
        'stacking_height_text': '\n'.join(stacking_height_lines),
        'stacking_level_text': '\n'.join(stacking_level_lines),
        'clearance_height_text': '',
        'storage_locations_text': state.get('storage_locations', ''),
        'application_specific_text': '\n'.join(application_lines).strip(),
        'xqe_xpl_xna_summary_text': '\n'.join(summary_lines),
        'route_summary': route_summary,
        'material_step_details_text': '\n'.join(step_details),
        'step_details_text': '\n'.join(step_details),
        'system_architecture_text': '\n'.join(system_architecture_lines),
        'integration_route_text': ' → '.join(_dedupe_consecutive(integration_route_parts)),
        'data_flow_diagram_text': '\n\n'.join(diagram_blocks),
        'task_flow_text': '\n\n'.join(concise_flow_lines),
        'connected_systems_text': '\n'.join(sorted(x for x in all_connected if x)),
        'status_feedback_text': '\n'.join(sorted(x for x in all_status if x)),
        'key_data_exchange_text': '\n'.join(sorted(x for x in all_key_data if x)),
        'integration_req': '\n'.join(integration_req_lines),
        'connections_details': '\n'.join(connections_details_lines),
        'cad_filename': state.uploads.get('cad_file_name', ''),
        'conveyor_picture_name': state.uploads.get('conveyor_picture_name', ''),
    }
    return context


def generate_report():
    compute_sequence_routes()
    if state.get('temperature_range') == 'Below 0°C':
        ui.notify('Project not possible for temperature below 0°C.', type='negative')
        return
    if not validate_product_logic():
        ui.notify('Please fix product validation issues first.', type='negative')
        return
    required = ['customer_name', 'customer_email', 'customer_mobile']
    missing = [k for k in required if not state.get(k)]
    if not state.selected_apps():
        missing.append('application')
    if missing:
        ui.notify('Missing required fields: ' + ', '.join(missing), type='negative')
        return
    if not os.path.exists(TEMPLATE_PATH):
        ui.notify('Template file not found: template.docx', type='negative')
        return

    context = build_context()
    doc = DocxTemplate(TEMPLATE_PATH)
    doc.render(context)

    report_buffer = BytesIO()
    doc.save(report_buffer)
    report_buffer.seek(0)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = (state.get('customer_name') or 'customer').strip().replace(' ', '_').lower()

    with NamedTemporaryFile(delete=False, suffix='.docx') as tmp_docx:
        tmp_docx.write(report_buffer.getvalue())
        tmp_docx_path = tmp_docx.name

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(tmp_docx_path, arcname=f'site_survey_{safe_name}_{timestamp}.docx')
        cad = state.uploads.get('cad_file')
        if cad:
            zf.writestr(state.uploads.get('cad_file_name', 'cad_file'), cad)
        conveyor = state.uploads.get('conveyor_picture')
        if conveyor:
            zf.writestr(state.uploads.get('conveyor_picture_name', 'conveyor_picture'), conveyor)
        for i, route in enumerate(state.get('route_details', [])):
            data = route.get('source_image')
            name = state.uploads.get(f'route_source_image_{i}_name')
            if data and name:
                zf.writestr(name, data)
    zip_buffer.seek(0)

    with NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
        tmp_zip.write(zip_buffer.getvalue())
        tmp_zip_path = tmp_zip.name

    ui.notify('ZIP generated. Download will start. Please email the ZIP to ritick.sethi@ep-equipment.eu', type='positive')
    ui.download(tmp_zip_path)


@ui.page('/')
def main():
    xqe_pdf = find_existing_file(XQE_PDF_CANDIDATES)
    xpl_pdf = find_existing_file(XPL_PDF_CANDIDATES)

    with ui.column().classes('w-full max-w-7xl mx-auto p-6 gap-6'):
        with ui.row().classes('items-center justify-between w-full'):
            with ui.row().classes('items-center gap-4'):
                if os.path.exists(LOGO_PATH):
                    ui.image(LOGO_PATH).classes('w-40')
                with ui.column().classes('gap-0'):
                    ui.label('EP Equipment – Warehouse-Automation-Presales-tool').classes('text-3xl font-bold')
                    ui.label('Customer-facing multi-step workflow').classes('text-gray-600')
            with ui.row().classes('gap-2'):
                if xqe_pdf:
                    ui.link('Download XQE PDF', xqe_pdf).props('target=_blank').classes('text-primary')
                if xpl_pdf:
                    ui.link('Download XPL PDF', xpl_pdf).props('target=_blank').classes('text-primary')

        with ui.stepper().props('flat animated').classes('w-full') as stepper:
            with ui.step('Basic Information'):
                ui.label('Basic information and product requirements').classes('text-xl font-semibold')
                with ui.card().classes('w-full'):
                    with ui.grid(columns=2).classes('w-full gap-4'):
                        ui.input('Customer Name *', value=state.get('customer_name')).bind_value(state.data, 'customer_name')
                        ui.input('Customer Email *', value=state.get('customer_email')).bind_value(state.data, 'customer_email')
                        ui.input('Customer Mobile *', value=state.get('customer_mobile')).bind_value(state.data, 'customer_mobile')
                        ui.input('Project Name', value=state.get('project_name')).bind_value(state.data, 'project_name')
                        ui.input('Project Location', value=state.get('project_location')).bind_value(state.data, 'project_location')
                        ui.input('Warehouse / Workshop Area [sq m]', value=state.get('warehouse_area')).bind_value(state.data, 'warehouse_area')
                        ui.input('Survey Date', value=state.get('survey_date')).bind_value(state.data, 'survey_date')
                    ui.textarea('Job-To-Do', value=state.get('task_description')).bind_value(state.data, 'task_description').props('autogrow')
                    ui.select(['Transport / Cross Docking', 'Stacking/Conveyor', 'Narrow Aisle', 'Other'], label='Application(s)', multiple=True,
                              value=state.get('application'), on_change=lambda e: (state.set('application', e.value), validate_product_logic())).classes('w-full')

                    pallet = state.primary_pallet()
                    with ui.grid(columns=2).classes('w-full gap-4'):
                        ui.select(['Euro', 'Industrial', 'Other'], label='Pallet Type', value=pallet['pallet_type'],
                                  on_change=lambda e: pallet.__setitem__('pallet_type', e.value))
                        ui.input('Load Dimensions (L×W×H) [mm]', value=pallet['load_dimensions'],
                                 on_change=lambda e: (pallet.__setitem__('load_dimensions', e.value), validate_product_logic()))
                        ui.number('Insertion Depth (Fork Entry) [mm]', value=pallet['pallet_width_mm'], min=0, step=1,
                                  on_change=lambda e: pallet.__setitem__('pallet_width_mm', e.value))
                        ui.number('Load Weight [kg]', value=state.get('load_weight_kg'), min=0, step=1,
                                  on_change=lambda e: (state.set('load_weight_kg', e.value), validate_product_logic()))
                        ui.number('Maximum Stacking Height [m]', value=state.get('max_stacking_height_m'), min=0, step=0.1,
                                  on_change=lambda e: (state.set('max_stacking_height_m', e.value), validate_product_logic()))
                        ui.number('XPL Aisle Width [m]', value=state.get('cross_docking_aisle'), min=0, step=0.1).bind_value(state.data, 'cross_docking_aisle')
                        ui.number('XNA Actual Aisle Width [m]', value=state.get('aisle_width_m'), min=0, step=0.1,
                                  on_change=lambda e: (state.set('aisle_width_m', e.value), validate_product_logic()))
                        ui.select(['Transport', 'Cross Docking'], label='XPL Application Type', value=state.get('xpl_sub_type')).bind_value(state.data, 'xpl_sub_type')
                        ui.select(['XNA121 (up to 8.5m)', 'XNA151 (up to 13m)'], label='Preferred XNA Model',
                                  value=state.get('xna_model'),
                                  on_change=lambda e: (state.set('xna_model', e.value), validate_product_logic()))
                        ui.select(['Ground', 'Conveyor', 'Other'], label='Pickup Type', value=state.get('pickup_type')).bind_value(state.data, 'pickup_type')
                        ui.select(['Floor Stacking', 'Rack Stacking', 'Other'], label='Stacking Type', value=state.get('stacking_type')).bind_value(state.data, 'stacking_type')
                        ui.textarea('Storage Layout Description', value=state.get('storage_layout')).bind_value(state.data, 'storage_layout')
                        ui.textarea('Storage Locations', value=state.get('storage_locations')).bind_value(state.data, 'storage_locations')
                    ui.upload(label='Upload Conveyor Picture', auto_upload=True,
                              on_upload=lambda e: (state.uploads.__setitem__('conveyor_picture', e.content.read()),
                                                   state.uploads.__setitem__('conveyor_picture_name', e.name)))
                    product_msg = ui.markdown('')
                    validate_product_logic()
                    product_msg.set_content(state.messages['product'] or 'Product limits look acceptable with the current selections.')

                with ui.stepper_navigation():
                    ui.button('Next', on_click=stepper.next).props('color=primary')

            with ui.step('Material Flow'):
                ui.label('Material flow').classes('text-xl font-semibold')
                route_count = ui.number('Number of Steps', value=state.get('route_count'), min=2, step=1)
                flow_container = ui.column().classes('w-full gap-3')
                route_container = ui.column().classes('w-full gap-4')

                def rebuild_flow_ui():
                    state.set('route_count', int(route_count.value))
                    flow_container.clear()
                    route_container.clear()
                    seq = state.get('flow_sequence', [])[:int(route_count.value)]
                    while len(seq) < int(route_count.value):
                        seq.append(FLOW_OPTIONS[min(len(seq), len(FLOW_OPTIONS) - 1)])
                    state.set('flow_sequence', seq)

                    with flow_container:
                        for i in range(int(route_count.value)):
                            options = FLOW_OPTIONS if i == 0 else (NEXT_STEP_OPTIONS.get(seq[i - 1], FLOW_OPTIONS) or FLOW_OPTIONS)
                            sel = ui.select(options, label=f'Step {i + 1}', value=seq[i]).classes('w-72')
                            def update_step(e, idx=i):
                                seq[idx] = e.value
                                state.set('flow_sequence', seq)
                                rebuild_flow_ui()
                            sel.on_value_change(update_step)

                    with route_container:
                        compute_sequence_routes()
                        for i in range(len(seq) - 1):
                            src, dst = seq[i], seq[i + 1]
                            with ui.card().classes('w-full'):
                                ui.label(f'{src} → {dst}').classes('text-lg font-semibold')
                                with ui.grid(columns=3).classes('w-full gap-4'):
                                    ui.number('Pallets/hour', value=state.get(f'route_pallets_per_hour_{i}', 0), min=0, step=1,
                                              on_change=lambda e, k=f'route_pallets_per_hour_{i}': (state.set(k, e.value), compute_sequence_routes()))
                                    ui.number('Average Distance [m]', value=state.get(f'route_avg_distance_{i}', 0), min=0, step=1,
                                              on_change=lambda e, k=f'route_avg_distance_{i}': (state.set(k, e.value), compute_sequence_routes()))
                                    ui.select(['Simultaneous / continuous', 'On request / intermittent', 'No - not handled by EP automation'],
                                              label='Flow Type',
                                              value=state.get(f'route_flow_type_{i}', 'On request / intermittent' if dst == 'Outbound' else 'Simultaneous / continuous'),
                                              on_change=lambda e, k=f'route_flow_type_{i}': (state.set(k, e.value), compute_sequence_routes()))
                                ui.upload(label=f'Upload Image / Layout for {src} → {dst}', auto_upload=True,
                                          on_upload=lambda e, idx=i: (
                                              state.uploads.__setitem__(f'route_source_image_{idx}', e.content.read()),
                                              state.uploads.__setitem__(f'route_source_image_{idx}_name', e.name)
                                          ))
                        ui.input('Job-To-Do / Process Name', value=state.get('job_to_do_flow')).bind_value(state.data, 'job_to_do_flow')
                        ui.textarea('Material Flow Details', value=state.get('material_flow_text')).bind_value(state.data, 'material_flow_text').props('autogrow')
                        ui.textarea('Special comments / direct flows / notes', value=state.get('special_comments')).bind_value(state.data, 'special_comments').props('autogrow')
                        ui.upload(label='Upload CAD / Layout File', auto_upload=True,
                                  on_upload=lambda e: (state.uploads.__setitem__('cad_file', e.content.read()),
                                                       state.uploads.__setitem__('cad_file_name', e.name)))
                route_count.on_value_change(lambda e: rebuild_flow_ui())
                rebuild_flow_ui()

                with ui.stepper_navigation():
                    ui.button('Back', on_click=stepper.previous)
                    ui.button('Next', on_click=lambda: (compute_sequence_routes(), stepper.next())).props('color=primary')

            with ui.step('Data Flow'):
                ui.label('Data flow').classes('text-xl font-semibold')
                df_container = ui.column().classes('w-full gap-4')

                def rebuild_data_flow():
                    compute_sequence_routes()
                    df_container.clear()
                    routes = state.route_details_filtered()
                    equipment_choices = _equipment_options(state.selected_apps())
                    with df_container:
                        with ui.card().classes('w-full'):
                            with ui.grid(columns=2).classes('w-full gap-4'):
                                ui.select(['Yes', 'No'], label='Integration required?', value=state.get('integration_required')).bind_value(state.data, 'integration_required')
                                ui.select(['Yes', 'No'], label='Do you want DAS / EP WMS?', value=state.get('ep_wms_used')).bind_value(state.data, 'ep_wms_used')
                                ui.select(['Yes', 'No'], label='Current customer system needed?', value=state.get('current_system_needed')).bind_value(state.data, 'current_system_needed')
                                ui.select(['Customer WMS', 'Customer ERP', 'Customer MES', 'Integrator system', 'Other'], label='Current system type', value=state.get('current_system_type')).bind_value(state.data, 'current_system_type')
                                ui.input('Current system name', value=state.get('current_system_name')).bind_value(state.data, 'current_system_name')
                                ui.select(['Yes', 'No'], label='Other WMS / business system?', value=state.get('other_wms_integration_needed')).bind_value(state.data, 'other_wms_integration_needed')
                                ui.input('Other WMS / system name', value=state.get('other_wms_name')).bind_value(state.data, 'other_wms_name')
                                ui.select(SYSTEM_INTEGRATION_OPTIONS, label='Integration to other systems / equipment', multiple=True, value=state.get('integration_connections')).bind_value(state.data, 'integration_connections')
                                ui.select(API_PROTOCOL_OPTIONS, label='API / interface types', multiple=True, value=state.get('api_protocols')).bind_value(state.data, 'api_protocols')
                            ui.textarea('Overall integration / API notes', value=state.get('data_flow_additional_notes')).bind_value(state.data, 'data_flow_additional_notes').props('autogrow')

                        if not routes:
                            ui.label('No EP-automation routes available for Data Flow.')

                        route_flows = state.get('route_flows')
                        for i, route in enumerate(routes):
                            route_name = f"{route['from']} → {route['to']}"
                            route_flow = route_flows.setdefault(i, {
                                'trigger': 'Customer WMS order',
                                'info_source': 'Customer WMS',
                                'leading_system': 'Customer WMS',
                                'provided_info': '',
                                'execution_mode': 'Single EP vehicle',
                                'primary_vehicle': equipment_choices[0],
                                'primary_action': 'transport',
                                'secondary_vehicle': equipment_choices[-1],
                                'secondary_action': 'stacking' if route['to'] != 'Outbound' else 'transport',
                                'return_targets': ['Customer WMS'],
                                'statuses': ['Task completed'],
                                'key_data': ['Pallet ID / Barcode', 'Pickup location', 'Destination / Storage location'],
                                'process_notes': '',
                            })
                            with ui.card().classes('w-full'):
                                ui.label(route_name).classes('text-lg font-semibold')
                                with ui.grid(columns=2).classes('w-full gap-4'):
                                    ui.select(TRIGGER_OPTIONS, label='Task trigger', value=route_flow['trigger'],
                                              on_change=lambda e, idx=i: state.get('route_flows')[idx].__setitem__('trigger', e.value))
                                    ui.select(INFO_SOURCE_OPTIONS, label='Info source', value=route_flow['info_source'],
                                              on_change=lambda e, idx=i: state.get('route_flows')[idx].__setitem__('info_source', e.value))
                                    ui.select(COORDINATION_OPTIONS, label='Leading system', value=route_flow['leading_system'],
                                              on_change=lambda e, idx=i: state.get('route_flows')[idx].__setitem__('leading_system', e.value))
                                    ui.input('What does the source system provide?', value=route_flow['provided_info'],
                                             on_change=lambda e, idx=i: state.get('route_flows')[idx].__setitem__('provided_info', e.value))
                                    ui.select(['Single EP vehicle', 'Vehicle handover'], label='Execution mode', value=route_flow['execution_mode'],
                                              on_change=lambda e, idx=i: (state.get('route_flows')[idx].__setitem__('execution_mode', e.value), rebuild_data_flow()))
                                    ui.select(equipment_choices, label='Primary EP vehicle', value=route_flow['primary_vehicle'],
                                              on_change=lambda e, idx=i: state.get('route_flows')[idx].__setitem__('primary_vehicle', e.value))
                                    ui.input('Primary vehicle action', value=route_flow['primary_action'],
                                             on_change=lambda e, idx=i: state.get('route_flows')[idx].__setitem__('primary_action', e.value))
                                    if route_flow['execution_mode'] == 'Vehicle handover':
                                        ui.select(equipment_choices, label='Final EP vehicle', value=route_flow['secondary_vehicle'],
                                                  on_change=lambda e, idx=i: state.get('route_flows')[idx].__setitem__('secondary_vehicle', e.value))
                                        ui.input('Final vehicle action', value=route_flow['secondary_action'],
                                                 on_change=lambda e, idx=i: state.get('route_flows')[idx].__setitem__('secondary_action', e.value))
                                with ui.expansion('Advanced options'):
                                    with ui.grid(columns=2).classes('w-full gap-4'):
                                        ui.select(STATUS_OPTIONS, label='Status returned', multiple=True, value=route_flow['statuses'],
                                                  on_change=lambda e, idx=i: state.get('route_flows')[idx].__setitem__('statuses', e.value))
                                        ui.select(RETURN_TARGET_OPTIONS, label='Return targets', multiple=True, value=route_flow['return_targets'],
                                                  on_change=lambda e, idx=i: state.get('route_flows')[idx].__setitem__('return_targets', e.value))
                                        ui.select(KEY_DATA_OPTIONS, label='Key data exchanged', multiple=True, value=route_flow['key_data'],
                                                  on_change=lambda e, idx=i: state.get('route_flows')[idx].__setitem__('key_data', e.value))
                                    ui.textarea('Additional process note', value=route_flow['process_notes'],
                                                on_change=lambda e, idx=i: state.get('route_flows')[idx].__setitem__('process_notes', e.value)).props('autogrow')

                                execution_nodes = _build_execution_nodes(
                                    route_flow['execution_mode'],
                                    route_flow['primary_vehicle'],
                                    route_flow['primary_action'],
                                    route_flow['secondary_vehicle'],
                                    route_flow['secondary_action'],
                                )
                                forward = _build_forward_nodes(route_flow['trigger'], route_flow['info_source'], route_flow['leading_system'], state.get('ep_wms_used'), execution_nodes)
                                ui.label('Preview').classes('text-sm font-medium text-gray-600')
                                ui.label(' → '.join(forward)).classes('font-mono')
                rebuild_data_flow()

                with ui.stepper_navigation():
                    ui.button('Back', on_click=stepper.previous)
                    ui.button('Next', on_click=stepper.next).props('color=primary')

            with ui.step('Site Conditions & Generate'):
                with ui.card().classes('w-full'):
                    with ui.grid(columns=2).classes('w-full gap-4'):
                        ui.input('Presence of Other AGVs / AMRs / Automated Equipment', value=state.get('other_agvs')).bind_value(state.data, 'other_agvs')
                        ui.input('Presence of Trucks / Forklifts / Pedestrians', value=state.get('other_traffic')).bind_value(state.data, 'other_traffic')
                        ui.textarea('Vehicle Parking & Rest Area Description', value=state.get('parking_area')).bind_value(state.data, 'parking_area')
                        ui.textarea('Charging Area Status / Requirements', value=state.get('charging_status')).bind_value(state.data, 'charging_status')
                        ui.number('Shifts per Day', value=state.get('shifts_per_day'), min=0, max=10, step=1).bind_value(state.data, 'shifts_per_day')
                        ui.number('Operational peak hours / shift', value=state.get('peak_hours'), min=0, step=0.5).bind_value(state.data, 'peak_hours')
                        ui.select(['Select temperature range', 'Below 0°C', '1-10°C', '10-20°C', '20-30°C', '30-40°C'], label='Temperature Range (°C)', value=state.get('temperature_range')).bind_value(state.data, 'temperature_range')
                        ui.select(['Yes', 'No'], label='Is WiFi available on site?', value=state.get('site_wifi_available')).bind_value(state.data, 'site_wifi_available')
                    ui.textarea('Special Layout Requirements', value=state.get('special_layout')).bind_value(state.data, 'special_layout').props('autogrow')
                    ui.textarea('Special Demand / Customization Details', value=state.get('special_demand')).bind_value(state.data, 'special_demand').props('autogrow')

                with ui.stepper_navigation():
                    ui.button('Back', on_click=stepper.previous)
                    ui.button('Generate Report ZIP', on_click=generate_report).props('color=primary')

ui.run(title='EP Equipment – NiceGUI Site Survey')
