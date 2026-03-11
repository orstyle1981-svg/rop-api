from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# Загружаем базу кодов при старте
with open(os.path.join(os.path.dirname(__file__), 'rop_codes.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

def normalize_code(code, code_type):
    """Приводит код к стандартному виду: удаляет точки и лишние символы."""
    return re.sub(r'[^0-9]', '', code) if code_type in ('tnved', 'okpd2') else code

@app.route('/check', methods=['GET'])
def check_code():
    code = request.args.get('code', '').strip()
    code_type = request.args.get('type', '').strip().lower()  # 'tnved' или 'okpd2'

    if not code or not code_type:
        return jsonify({'error': 'Missing code or type parameter'}), 400

    if code_type not in ('tnved', 'okpd2'):
        return jsonify({'error': 'Type must be "tnved" or "okpd2"'}), 400

    # Поиск по точному совпадению
    found = []
    for item in data:
        db_code = item.get(f'{code_type}_code')
        if db_code:
            # Убираем префикс 'из' для ТН ВЭД
            if code_type == 'tnved' and db_code.startswith('из '):
                db_code = db_code[3:].strip()
            if db_code == code:
                found.append(item)

    if not found:
        # Если не нашли, пробуем частичное совпадение (первые N знаков)
        # Для ТН ВЭД: сначала 10 знаков, потом 6, потом 4
        # Для ОКПД2: сначала 9 знаков, потом 6, потом 4 (но у нас 9-значные)
        # Упрощённо: отсекаем последние символы и ищем любой код, начинающийся с этого префикса
        # Реализуем базовый алгоритм
        normalized = normalize_code(code, code_type)
        for item in data:
            db_code = item.get(f'{code_type}_code')
            if db_code:
                if code_type == 'tnved' and db_code.startswith('из '):
                    db_code_clean = db_code[3:].strip()
                else:
                    db_code_clean = db_code
                db_norm = normalize_code(db_code_clean, code_type)
                if db_norm and normalized.startswith(db_norm):
                    found.append(item)

    # Если нашли, формируем ответ
    if found:
        # Берём первую запись (можно уточнить)
        first = found[0]
        group = first.get('group')
        group_name = first.get('group_name')
        note = first.get('tnved_note') if code_type == 'tnved' else None
        message = f"Код найден в группе {group} ({group_name})."
        if note:
            message += f" Обратите внимание: сноска {note} может содержать ограничения."
        return jsonify({
            'found': True,
            'group': group,
            'group_name': group_name,
            'message': message,
            'note': note
        })
    else:
        return jsonify({'found': False, 'message': 'Код не найден в перечне.'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)