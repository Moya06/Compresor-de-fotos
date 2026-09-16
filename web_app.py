import os, sys, uuid, shutil, tempfile, threading, webbrowser, time
from flask import Flask, render_template, request, jsonify, send_file
from compressor import SmartCompressor, find_images

if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except: pass

app = Flask(__name__, template_folder="templates")
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024 * 1024

SESSIONS = {}

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'Archivos demasiado grandes.'}), 413
@app.errorhandler(Exception)
def handle_err(e):
    return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/create_session', methods=['POST'])
def create_session():
    sid = str(uuid.uuid4())
    tmp = tempfile.mkdtemp(prefix=f"cmp_{sid[:8]}_")
    inp = os.path.join(tmp, "in")
    os.makedirs(inp)
    SESSIONS[sid] = {
        'tmp': tmp, 'inp': inp,
        'zip': os.path.join(tmp, f"fotos_{sid[:8]}.zip"),
        'state': 'uploading', 'current': 0, 'total': 0,
        'filename': '', 'stats': None, 'error': None
    }
    return jsonify({'session_id': sid})

@app.route('/api/upload_chunk/<sid>', methods=['POST'])
def upload_chunk(sid):
    s = SESSIONS.get(sid)
    if not s: return jsonify({'error': 'Sesión no encontrada.'}), 404
    saved = 0
    for f in request.files.getlist('images'):
        if f.filename:
            name = os.path.basename(f.filename.replace('/', os.sep).replace('\\', os.sep))
            dest = os.path.join(s['inp'], name)
            if os.path.exists(dest):
                base, ext = os.path.splitext(name)
                name = f"{base}_{saved}{ext}"
                dest = os.path.join(s['inp'], name)
            f.save(dest)
            saved += 1
    return jsonify({'saved': saved})

@app.route('/api/start/<sid>', methods=['POST'])
def start(sid):
    s = SESSIONS.get(sid)
    if not s: return jsonify({'error': 'Sesión no encontrada.'}), 404
    images = find_images([s['inp']])
    if not images: return jsonify({'error': 'Sin imágenes.'}), 400

    target_mb = float(request.form.get('target_mb', 10.0))
    s['state'] = 'processing'
    s['total'] = len(images)
    s['current'] = 0

    def run():
        def cb(cur, tot, fname, orig, comp):
            s['current'] = cur
            s['total'] = tot
            s['filename'] = fname
        try:
            c = SmartCompressor(target_mb_per_image=target_mb, workers=8)
            st = c.compress_to_zip(images, s['zip'], s['inp'], cb)
            s['state'] = 'completed'
            s['stats'] = {
                'total_files': st.total_files,
                'success_count': st.success_count,
                'total_original_size': st.total_original_size,
                'total_compressed_size': st.total_compressed_size,
                'saved_bytes': st.saved_bytes,
                'reduction_percentage': st.reduction_percentage,
                'elapsed_time': round(st.elapsed_time, 2),
                'resolution_used': st.resolution_used,
                'target_mb_per_image': st.target_mb_per_image
            }
        except Exception as e:
            s['state'] = 'error'
            s['error'] = str(e)

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'started': True, 'total': len(images)})

@app.route('/api/progress/<sid>')
def progress(sid):
    s = SESSIONS.get(sid)
    if not s: return jsonify({'error': 'No encontrada'}), 404
    return jsonify({
        'state': s['state'], 'current': s['current'], 'total': s['total'],
        'filename': s['filename'], 'stats': s['stats'], 'error': s['error']
    })

@app.route('/api/download/<sid>')
def download(sid):
    s = SESSIONS.get(sid)
    if not s or s['state'] != 'completed': return jsonify({'error': 'No listo'}), 404
    if not os.path.exists(s['zip']): return jsonify({'error': 'ZIP no existe'}), 404
    return send_file(s['zip'], mimetype='application/zip', as_attachment=True, download_name='fotos_comprimidas.zip')

def run_server(port=5000):
    url = f"http://localhost:{port}"
    print("=" * 60)
    print("  COMPRESOR DE FOTOS PROFESIONAL (PER IMAGE)")
    print(f"  Abrir en navegador: {url}")
    print("  Ctrl+C para detener")
    print("=" * 60)
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 5000
    run_server(port)
