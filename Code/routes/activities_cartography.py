from .activities_bp import activities_bp
from flask import jsonify
import os, io, contextlib, traceback
from Code.scripts.extract_visio import process_visio_file, print_summary

@activities_bp.route('/update-cartography', methods=['GET'])
def update_cartography():
    try:
        vsdx_path = os.path.join("Code", "example.vsdx")
        process_visio_file(vsdx_path)
        summary_output = io.StringIO()
        with contextlib.redirect_stdout(summary_output):
            print_summary()
        summary_text = summary_output.getvalue()
        return jsonify({
            "message": "Cartographie mise à jour (partielle)",
            "summary": summary_text
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
