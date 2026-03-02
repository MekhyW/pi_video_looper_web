#!/usr/bin/env python3

import configparser
import os
import sys
from flask import Flask, jsonify, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

VIDEO_EXTENSIONS = {'.avi', '.mov', '.mkv', '.mp4', '.m4v'}


def _load_upload_dir(config_path: str) -> str:
    """Read the ini file and return the upload directory path."""
    config = configparser.ConfigParser()
    if not config.read(config_path):
        raise RuntimeError(f'Cannot read config file: {config_path}. Is the application properly installed?')
    # web_reader section is the primary source; fall back to [directory] path.
    if config.has_section('web_reader') and config.has_option('web_reader', 'path'):
        return config.get('web_reader', 'path')
    if config.has_section('directory') and config.has_option('directory', 'path'):
        return config.get('directory', 'path')
    raise RuntimeError('Cannot determine upload directory. Add a [web_reader] section with a "path" key in the ini file.')


# ---------------------------------------------------------------------------
# Flask application factory
# ---------------------------------------------------------------------------

def create_app(upload_dir: str) -> Flask:
    """Create and configure the Flask application."""
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    app = Flask(__name__, template_folder=template_dir)
    os.makedirs(upload_dir, exist_ok=True)

    # -----------------------------------------------------------------------
    # Helper functions
    # -----------------------------------------------------------------------

    def is_video(filename: str) -> bool:
        _, ext = os.path.splitext(filename.lower())
        return ext in VIDEO_EXTENSIONS

    def list_videos():
        """Return sorted list of video filenames in the upload directory."""
        try:
            return sorted(f for f in os.listdir(upload_dir) if is_video(f) and not f.startswith('.'))
        except FileNotFoundError:
            return []

    # -----------------------------------------------------------------------
    # Routes
    # -----------------------------------------------------------------------

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/status')
    def api_status():
        videos = list_videos()
        return jsonify({'video_count': len(videos), 'upload_dir': upload_dir})

    @app.route('/api/videos', methods=['GET'])
    def api_videos():
        return jsonify(list_videos())

    @app.route('/api/upload', methods=['POST'])
    def api_upload():
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in request'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        filename = secure_filename(file.filename)
        if not is_video(filename):
            return jsonify({'error': f'Unsupported file type. Allowed: {", ".join(sorted(VIDEO_EXTENSIONS))}'}), 400
        dest = os.path.join(upload_dir, filename)
        file.save(dest)
        return jsonify({'message': f'{filename} uploaded successfully', 'filename': filename}), 201

    @app.route('/api/videos/<filename>', methods=['DELETE'])
    def api_delete(filename):
        safe_name = secure_filename(filename)
        filepath = os.path.join(upload_dir, safe_name)
        if not os.path.isfile(filepath):
            return jsonify({'error': 'File not found'}), 404
        os.remove(filepath)
        return jsonify({'message': f'{safe_name} deleted successfully'})

    @app.route('/api/restart', methods=['POST'])
    def api_restart():
        """Touch a sentinel file to trigger a playlist reload.
        The web_reader.is_changed() method detects directory changes so
        simply touching a file is enough.  We then remove it immediately
        so it does not appear in the video list.
        """
        sentinel = os.path.join(upload_dir, '.reload_sentinel')
        try:
            # Create then delete to trigger a modification event.
            open(sentinel, 'w').close()
            os.remove(sentinel)
        except OSError:
            pass
        return jsonify({'message': 'Restart signal sent to player'})

    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    config_path = '/boot/video_looper.ini'
    if len(sys.argv) == 2:
        config_path = sys.argv[1]
    try:
        upload_dir = _load_upload_dir(config_path)
    except RuntimeError as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
    print(f'[web_server] Upload directory: {upload_dir}')
    print(f'[web_server] Starting web server on port 5000...')
    app = create_app(upload_dir)
    app.run(host='0.0.0.0', port=5000, threaded=True)


if __name__ == '__main__':
    main()
