"""Serve the built app under the API origin without exposing private storage."""
from pathlib import PurePosixPath
from starlette.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse


class AppFiles(StaticFiles):
    async def get_response(self, path, scope):
        if path == 'api' or path.startswith('api/'):
            return JSONResponse({'error': {'code': 'not_found', 'message': 'Unknown API route'}}, status_code=404)
        try:
            response = await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404 or PurePosixPath(path).suffix or '..' in PurePosixPath(path).parts:
                raise
            response = await super().get_response('index.html', scope)
        response.headers['Cache-Control'] = ('public, max-age=31536000, immutable'
                                             if path.startswith('assets/') else 'no-cache')
        response.headers['X-Content-Type-Options'] = 'nosniff'
        if path == 'sw.js':
            response.headers['Service-Worker-Allowed'] = '/'
        return response
