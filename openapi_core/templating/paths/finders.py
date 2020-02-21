"""OpenAPI core templating paths finders module"""
from more_itertools import peekable
from six import iteritems

from openapi_core.templating.datatypes import TemplateResult
from openapi_core.templating.util import parse, search
from openapi_core.templating.paths.exceptions import (
    PathNotFound, OperationNotFound, ServerNotFound,
)


class PathFinder(object):

    def __init__(self, spec, base_url=None):
        self.spec = spec
        self.base_url = base_url

    def find(self, request):
        paths_iter = self._get_paths_iter(request.full_url_pattern)
        paths_iter_peek = peekable(paths_iter)

        if not paths_iter_peek:
            raise PathNotFound(request.full_url_pattern)

        operations_iter = self._get_operations_iter(
            request.method, paths_iter_peek)
        operations_iter_peek = peekable(operations_iter)

        if not operations_iter_peek:
            raise OperationNotFound(request.full_url_pattern, request.method)

        servers_iter = self._get_servers_iter(
            request.full_url_pattern, operations_iter_peek)

        try:
            return next(servers_iter)
        except StopIteration:
            raise ServerNotFound(request.full_url_pattern)

    def _get_paths_iter(self, full_url_pattern):
        for path_pattern, path in iteritems(self.spec.paths):
            # simple path
            if full_url_pattern.endswith(path_pattern):
                path_result = TemplateResult(path_pattern, {})
                yield (path, path_result)
            # template path
            else:
                result = search(path_pattern, full_url_pattern)
                if result:
                    path_result = TemplateResult(path_pattern, result.named)
                    yield (path, path_result)

    def _get_operations_iter(self, request_method, paths_iter):
        for path, path_result in paths_iter:
            if request_method not in path.operations:
                continue
            operation = path.operations[request_method]
            yield (path, operation, path_result)

    def _get_servers_iter(self, full_url_pattern, ooperations_iter):
        for path, operation, path_result in ooperations_iter:
            servers = path.servers or operation.servers or self.spec.servers
            for server in servers:
                server_url_pattern = full_url_pattern.rsplit(
                    path_result.resolved, 1)[0]
                server_url = server.get_absolute_url(self.base_url)
                if server_url.endswith('/'):
                    server_url = server_url[:-1]
                # simple path
                if server_url_pattern.startswith(server_url):
                    server_result = TemplateResult(server.url, {})
                    yield (
                        path, operation, server,
                        path_result, server_result,
                    )
                # template path
                else:
                    result = parse(server.url, server_url_pattern)
                    if result:
                        server_result = TemplateResult(
                            server.url, result.named)
                        yield (
                            path, operation, server,
                            path_result, server_result,
                        )
